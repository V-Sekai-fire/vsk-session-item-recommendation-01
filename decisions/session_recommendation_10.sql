-- =============================================
-- Godot Asset Recommendation OLAP Schema
-- DuckDB Implementation with Vector Support
-- =============================================

-- Enable extensions for vector search
INSTALL 'hnsw';
LOAD 'hnsw';

-- ======================
-- Core Tables
-- ======================

CREATE OR REPLACE TABLE assets (
  id UUID PRIMARY KEY,
  display_name TEXT NOT NULL,
  slug TEXT NOT NULL,
  scene_text TEXT NOT NULL,
  node_types MAP(VARCHAR, INT),
  script_languages MAP(VARCHAR, INT),
  shaders VARCHAR[],
  structural_embedding FLOAT[64],
  text_embedding FLOAT[384],
  mesh_embedding FLOAT[256],
  image_embedding FLOAT[512],
  audio_embedding FLOAT[128]
);

CREATE OR REPLACE TABLE users (
  id UUID PRIMARY KEY,
  godot_version VARCHAR,
  gpu_vendor VARCHAR,
  os_family VARCHAR,
  behavior_embedding FLOAT[256],
  session_patterns JSON
);

-- ======================
-- Interaction Tables
-- ======================

CREATE OR REPLACE TABLE sessions (
  id UUID PRIMARY KEY,
  user_id UUID,
  start_time TIMESTAMP,
  duration INTERVAL SECOND,
  modified_assets UUID[]
);

CREATE OR REPLACE TABLE session_assets (
  session_id UUID,
  asset_id UUID,
  usage_count INT,
  node_paths VARCHAR[],
  PRIMARY KEY (session_id, asset_id)
);

-- ======================
-- Graph Structure Tables
-- ======================

CREATE OR REPLACE TABLE item_graph (
  source UUID,
  target UUID,
  weight FLOAT,
  cooccurrence_type VARCHAR,
  PRIMARY KEY (source, target, cooccurrence_type)
);

CREATE OR REPLACE TABLE user_item_edges (
  user_id UUID,
  asset_id UUID,
  interaction_type VARCHAR,
  weight FLOAT,
  last_interacted TIMESTAMP,
  PRIMARY KEY (user_id, asset_id, interaction_type)
);

-- ======================
-- Materialized Views
-- ======================

CREATE OR REPLACE VIEW training_features AS
SELECT
  u.id AS user_id,
  a.id AS asset_id,
  -- User features
  u.godot_version,
  u.gpu_vendor,
  u.os_family,
  -- Asset features
  a.node_types,
  a.script_languages,
  a.shaders,
  -- Combined embeddings
  u.behavior_embedding AS user_embedding,
  array_cat(
    a.structural_embedding,
    a.text_embedding
  ) AS asset_embedding,
  -- Interaction context
  sa.usage_count,
  DATE_DIFF('hour', s.start_time, CURRENT_TIMESTAMP) AS hours_since_use
FROM users u
JOIN sessions s ON u.id = s.user_id
JOIN session_assets sa ON s.id = sa.session_id
JOIN assets a ON sa.asset_id = a.id;

CREATE OR REPLACE VIEW normalized_item_graph AS
SELECT 
  source,
  target,
  weight / SUM(weight) OVER (PARTITION BY source) AS normalized_weight,
  cooccurrence_type
FROM item_graph;

-- ======================
-- Indexes
-- ======================

-- HNSW index for asset similarity search
CREATE INDEX asset_embedding_idx ON assets 
USING HNSW(text_embedding)
WITH (
  metric = 'cosine',
  m = 16,
  ef_construction = 200
);

-- Range index for temporal queries
CREATE INDEX session_time_idx ON sessions 
USING BTREE(start_time);

-- ======================
-- Data Loading Procedures
-- ======================

CREATE OR REPLACE PROCEDURE load_asset_data(path VARCHAR) AS
BEGIN
  COPY assets FROM path 
  WITH (FORMAT PARQUET, AUTO_DETECT TRUE);
END;

CREATE OR REPLACE PROCEDURE load_interaction_data(path VARCHAR) AS
BEGIN
  -- Load session-relationship data
  INSERT INTO session_assets
  SELECT
    session_id::UUID,
    asset_id::UUID,
    usage_count::INT,
    string_split(node_paths, ';') 
  FROM read_csv(
    path,
    delim='|',
    header=true,
    columns={
      'session_id': 'VARCHAR',
      'asset_id': 'VARCHAR',
      'usage_count': 'INT',
      'node_paths': 'VARCHAR'
    }
  );
  
  -- Update co-occurrence graph
  INSERT INTO item_graph
  SELECT
    a.asset_id AS source,
    b.asset_id AS target,
    COUNT(*) AS weight,
    'session' AS cooccurrence_type
  FROM session_assets a
  JOIN session_assets b 
    ON a.session_id = b.session_id
    AND a.asset_id < b.asset_id
  GROUP BY 1, 2;
END;

-- ======================
-- Graph Maintenance
-- ======================

CREATE OR REPLACE PROCEDURE normalize_edges() AS
BEGIN
  -- Normalize item graph weights
  UPDATE item_graph
  SET weight = sub.normalized_weight
  FROM (
    SELECT 
      source,
      target,
      weight / SUM(weight) OVER (PARTITION BY source) AS normalized_weight
    FROM item_graph
  ) sub
  WHERE item_graph.source = sub.source
    AND item_graph.target = sub.target;
  
  -- Normalize user-item edges
  UPDATE user_item_edges
  SET weight = sub.normalized_weight
  FROM (
    SELECT 
      user_id,
      asset_id,
      weight / SUM(weight) OVER (PARTITION BY user_id) AS normalized_weight
    FROM user_item_edges
  ) sub
  WHERE user_item_edges.user_id = sub.user_id
    AND user_item_edges.asset_id = sub.asset_id;
END;

-- ======================
-- PinSageDGL Feature View
-- ======================

CREATE OR REPLACE VIEW pinsage_features AS
SELECT
  u.id AS user_id,
  a.id AS item_id,
  -- User metadata
  map(
    ['godot_version', 'gpu_vendor', 'os_family'],
    [u.godot_version, u.gpu_vendor, u.os_family]
  ) AS user_sparse,
  -- Asset metadata
  map(
    ['node_types', 'script_languages', 'shaders'],
    [a.node_types, a.script_languages, a.shaders]
  ) AS item_sparse,
  -- Combined embeddings
  array_cat(
    u.behavior_embedding,
    array_cat(
      a.structural_embedding,
      a.text_embedding
    )
  ) AS features,
  -- Interaction weight
  COALESCE(ue.weight, 0.0) AS target
FROM users u
CROSS JOIN assets a
LEFT JOIN user_item_edges ue
  ON u.id = ue.user_id
  AND a.id = ue.asset_id;
