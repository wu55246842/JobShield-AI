CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE IF NOT EXISTS assessments (
  id SERIAL PRIMARY KEY,
  session_id VARCHAR(128) NOT NULL,
  occupation_code VARCHAR(32),
  occupation_title VARCHAR(256),
  input_payload JSONB NOT NULL,
  output_summary TEXT NOT NULL,
  risk_score DOUBLE PRECISION NOT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS agents (
  id SERIAL PRIMARY KEY,
  assessment_id INT REFERENCES assessments(id),
  version VARCHAR(16) NOT NULL DEFAULT 'v1',
  config JSONB NOT NULL,
  explanation TEXT NOT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS tools_catalog (
  id SERIAL PRIMARY KEY,
  name VARCHAR(256) NOT NULL,
  description TEXT NOT NULL,
  url VARCHAR(512) NOT NULL UNIQUE,
  tags JSONB NOT NULL DEFAULT '[]'::jsonb,
  source VARCHAR(64) NOT NULL DEFAULT 'apify',
  raw_payload JSONB NOT NULL DEFAULT '{}'::jsonb,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS tool_embeddings (
  id SERIAL PRIMARY KEY,
  tool_id INT NOT NULL UNIQUE REFERENCES tools_catalog(id) ON DELETE CASCADE,
  embedding vector(1536) NOT NULL,
  model VARCHAR(128) NOT NULL,
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS onet_cache (
  id SERIAL PRIMARY KEY,
  occupation_code VARCHAR(32) NOT NULL UNIQUE,
  payload JSONB NOT NULL,
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_assessments_session_id ON assessments(session_id);
CREATE INDEX IF NOT EXISTS idx_tools_catalog_source ON tools_catalog(source);
CREATE INDEX IF NOT EXISTS idx_tool_embeddings_hnsw ON tool_embeddings USING hnsw (embedding vector_cosine_ops);
