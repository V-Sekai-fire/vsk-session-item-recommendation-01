import duckdb
import pandas as pd
from libreco.algorithms import PinSageDGL

# Initialize DuckDB
con = duckdb.connect(':memory:')

# Load schema
con.execute(open('schema.sql').read())

# Load data
con.execute("CALL load_asset_data('assets.parquet')")
con.execute("CALL load_interaction_data('interactions.csv')")
con.execute("CALL normalize_edges()")

# Prepare training data
df = con.execute("""
    SELECT 
      user_id,
      item_id,
      features,
      target
    FROM pinsage_features
""").df()

# Initialize PinSageDGL
model = PinSageDGL(
    task="ranking",
    data_info=data_info,
    paradigm="u2i",
    embed_size=len(features[0]),  # Auto-detect from concatenated embeddings
    num_layers=3,
    num_neighbors=15,
    loss_type="max_margin",
    sampler="random"
)

# Train model
model.fit(
    df[['user_id', 'item_id', 'features']],
    df['target'],
    eval_data=(eval_features, eval_targets)
)
