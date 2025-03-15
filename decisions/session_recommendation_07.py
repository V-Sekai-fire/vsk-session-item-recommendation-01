from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, conint, confloat
from typing import Optional, List
import duckdb
import uuid
import starvote
from libreco.algorithms import PinSAGE
from libreco.data import DatasetPure
import pandas as pd
import time
import random
from datetime import datetime, timedelta

app = FastAPI()

# ======================
# DATABASE INITIALIZATION
# ======================

def initialize_database():
    conn = duckdb.connect('recommendations.db')
    
    # Create tables
    conn.execute("""
    CREATE TABLE IF NOT EXISTS pipelines (
        pipelineid UUID PRIMARY KEY,
        retriever_strategy VARCHAR DEFAULT 'default',
        ranker_strategy VARCHAR DEFAULT 'default'
    )""")
    
    conn.execute("""
    CREATE TABLE IF NOT EXISTS users (
        userid UUID PRIMARY KEY,
        username VARCHAR
    )""")

    conn.execute("""
    CREATE TABLE IF NOT EXISTS items (
        itemid UUID PRIMARY KEY,
        title VARCHAR,
        genre VARCHAR,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )""")

    conn.execute("""
    CREATE TABLE IF NOT EXISTS interactions (
        interactionid UUID PRIMARY KEY,
        userid UUID,
        itemid UUID,
        rating INTEGER,
        timestamp BIGINT
    )""")

    # Insert default pipeline
    conn.execute("""
    INSERT OR IGNORE INTO pipelines VALUES (
        '00000000-0000-0000-0000-000000000000', 
        'default', 
        'default'
    )""")
    
    conn.close()

initialize_database()

# ======================
# DATA MODELS
# ======================

class RecommendationRequest(BaseModel):
    pipelineid: uuid.UUID
    userid: uuid.UUID
    itemid: Optional[uuid.UUID] = None
    k: Optional[conint(ge=1, le=100)] = 20
    retriever_strategy: Optional[str] = 'default'
    ranker_strategy: Optional[str] = 'default'
    exploration_factor: Optional[confloat(ge=0, le=1)] = 0.1
    promoted_items: Optional[List[uuid.UUID]] = None
    excluded_items: Optional[List[uuid.UUID]] = None
    detailed_output: Optional[bool] = False

class TrendsRequest(RecommendationRequest):
    time_period: Optional[conint(ge=3600, le=1209600)] = 604800

class RandomRecommendationRequest(BaseModel):
    pipelineid: uuid.UUID
    userid: uuid.UUID
    k: Optional[conint(ge=1, le=100)] = 20
    promoted_items: Optional[List[uuid.UUID]] = None
    excluded_items: Optional[List[uuid.UUID]] = None
    detailed_output: Optional[bool] = False

# ======================
# CORE RECOMMENDATION ENGINE
# ======================

class RecommendationSystem:
    def __init__(self, conn):
        self.conn = conn
        self.models = {}
        
    def get_pipeline_config(self, pipelineid):
        config = self.conn.execute(f"""
            SELECT retriever_strategy, ranker_strategy 
            FROM pipelines 
            WHERE pipelineid = '{pipelineid}'
        """).fetchone()
        
        if not config:
            raise HTTPException(status_code=404, detail="Pipeline not found")
        return config

    def prepare_model(self, userid):
        if userid not in self.models:
            interactions = self.conn.execute("""
                SELECT userid, itemid, rating
                FROM interactions
            """).fetchdf()

            dataset = DatasetPure.build_negative_samples(
                data=interactions,
                num_neg=1
            )

            model = PinSAGE(
                task="ranking",
                data_info=dataset.data_info,
                embed_size=64,
                n_epochs=10,
                num_walks=10,
                walk_length=5
            )
            model.fit(dataset)
            self.models[userid] = model
        return self.models[userid]

# ======================
# API ENDPOINTS
# ======================

@app.post("/recommendations")
async def get_recommendations(request: RecommendationRequest):
    conn = duckdb.connect('recommendations.db')
    try:
        system = RecommendationSystem(conn)
        config = system.get_pipeline_config(request.pipelineid)
        
        # Validate strategies match pipeline configuration
        if request.retriever_strategy != config[0]:
            raise HTTPException(status_code=400, detail="Invalid retriever strategy for pipeline")
        if request.ranker_strategy != config[1]:
            raise HTTPException(status_code=400, detail="Invalid ranker strategy for pipeline")

        # Generate base recommendations
        base_recs = generate_hybrid_recommendations(
            conn=conn,
            system=system,
            request=request
        )

        # Apply exploration strategy
        final_recs = apply_exploration_strategy(
            recommendations=base_recs,
            exploration_factor=request.exploration_factor
        )

        # Apply promotions and exclusions
        final_recs = apply_promotions_exclusions(
            recommendations=final_recs,
            promoted=request.promoted_items,
            excluded=request.excluded_items,
            k=request.k
        )

        return format_recommendation_output(
            conn=conn,
            items=final_recs,
            detailed=request.detailed_output
        )
    finally:
        conn.close()

@app.post("/trends")
async def get_trends(request: TrendsRequest):
    conn = duckdb.connect('recommendations.db')
    try:
        # Calculate time window
        end_time = datetime.now()
        start_time = end_time - timedelta(seconds=request.time_period)
        
        # Get trending items
        trends = conn.execute(f"""
            SELECT itemid, COUNT(*) as interaction_count
            FROM interactions
            WHERE timestamp BETWEEN {int(start_time.timestamp())} AND {int(end_time.timestamp())}
            GROUP BY itemid
            ORDER BY interaction_count DESC
            LIMIT {request.k}
        """).fetchdf()

        item_ids = [uuid.UUID(item) for item in trends['itemid'].tolist()]
        
        # Apply promotions and exclusions
        final_trends = apply_promotions_exclusions(
            recommendations=item_ids,
            promoted=request.promoted_items,
            excluded=request.excluded_items,
            k=request.k
        )

        return format_recommendation_output(
            conn=conn,
            items=final_trends,
            detailed=request.detailed_output
        )
    finally:
        conn.close()

@app.post("/random-recommendations")
async def get_random_recommendations(request: RandomRecommendationRequest):
    conn = duckdb.connect('recommendations.db')
    try:
        # Get all valid items
        all_items = conn.execute("""
            SELECT itemid FROM items
            WHERE itemid NOT IN (SELECT unnest($excluded))
        """, params={'excluded': request.excluded_items or []}).fetchdf()
        
        # Convert to UUID list
        item_pool = [uuid.UUID(item) for item in all_items['itemid'].tolist()]
        
        # Add promoted items
        final_items = (request.promoted_items or []) + [
            item for item in item_pool 
            if item not in (request.promoted_items or [])
        ]
        
        # Select random subset
        random_recs = random.sample(final_items, min(request.k, len(final_items)))
        
        return format_recommendation_output(
            conn=conn,
            items=random_recs,
            detailed=request.detailed_output
        )
    finally:
        conn.close()

# ======================
# HELPER FUNCTIONS
# ======================

def generate_hybrid_recommendations(conn, system, request):
    # Collaborative Filtering Scores
    cf_scores = conn.execute(f"""
        SELECT itemid, AVG(rating) * 20 AS score
        FROM interactions
        WHERE userid != '{request.userid}'
        GROUP BY itemid
    """).fetchdf().set_index('itemid')['score'].to_dict()

    # Content-Based Scores
    if request.itemid:
        genre = conn.execute(f"""
            SELECT genre FROM items 
            WHERE itemid = '{request.itemid}'
        """).fetchone()[0]
    else:
        genre = conn.execute(f"""
            SELECT genre FROM interactions i
            JOIN items USING (itemid)
            WHERE userid = '{request.userid}'
            GROUP BY genre ORDER BY COUNT(*) DESC
            LIMIT 1
        """).fetchone()[0]

    cb_scores = conn.execute(f"""
        SELECT itemid, CASE WHEN genre = '{genre}' THEN 100 ELSE 0 END AS score
        FROM items
    """).fetchdf().set_index('itemid')['score'].to_dict()

    # PinSAGE Scores
    model = system.prepare_model(request.userid)
    pinsage_scores = {
        uuid.UUID(item): score * 100 
        for item, score in model.predict(userid=request.userid, n=100)
    }

    # Combine scores using STAR voting
    election = starvote.election(
        method=starvote.allocated,
        ballots=[cf_scores, cb_scores, pinsage_scores],
        seats=request.k
    )
    
    return election

def apply_exploration_strategy(recommendations, exploration_factor):
    if exploration_factor == 0:
        return recommendations
    
    explore_count = int(len(recommendations) * exploration_factor)
    explore_items = recommendations[-explore_count:]
    random.shuffle(explore_items)
    
    return recommendations[:-explore_count] + explore_items

def apply_promotions_exclusions(recommendations, promoted, excluded, k):
    promoted = promoted or []
    excluded = excluded or []
    
    # Filter excluded items
    filtered = [item for item in recommendations if item not in excluded]
    
    # Add promoted items to top
    promoted_filtered = [item for item in promoted if item not in excluded]
    combined = promoted_filtered + [item for item in filtered if item not in promoted_filtered]
    
    return combined[:k]

def format_recommendation_output(conn, items, detailed=False):
    if not items:
        return {"results": []}

    items_str = [f"'{item}'" for item in items]
    
    query = """
        SELECT 
            i.itemid,
            i.title,
            i.genre,
            COALESCE(AVG(r.rating), 0) as avg_rating,
            COUNT(r.interactionid) as interaction_count
    """ + ("""
            , RANDOM() as score
    """ if detailed else "") + """
        FROM items i
        LEFT JOIN interactions r USING (itemid)
        WHERE i.itemid IN ({items})
        GROUP BY i.itemid, i.title, i.genre
        ORDER BY MAX(array_position(ARRAY[{ordered_ids}]::UUID[], i.itemid))
    """.format(
        items=','.join(items_str),
        ordered_ids=','.join(items_str)
    )

    result = conn.execute(query).fetchdf()
    result['itemid'] = result['itemid'].astype(str)
    
    return {"results": result.to_dict(orient='records')}

# ======================
# MAIN EXECUTION
# ======================

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
