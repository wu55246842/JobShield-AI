CREATE TABLE IF NOT EXISTS labels (
  id SERIAL PRIMARY KEY,
  assessment_id INT NOT NULL REFERENCES assessments(id) ON DELETE CASCADE,
  rater TEXT NOT NULL,
  label_type TEXT NOT NULL,
  risk_score_label DOUBLE PRECISION,
  confidence_label DOUBLE PRECISION,
  factor_overrides JSONB NOT NULL DEFAULT '{}'::jsonb,
  notes TEXT,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS experiments (
  id SERIAL PRIMARY KEY,
  name TEXT NOT NULL UNIQUE,
  description TEXT,
  model_version TEXT NOT NULL,
  params JSONB NOT NULL,
  is_active BOOLEAN NOT NULL DEFAULT FALSE,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS experiment_assignments (
  id SERIAL PRIMARY KEY,
  user_key TEXT NOT NULL,
  experiment_id INT NOT NULL REFERENCES experiments(id) ON DELETE CASCADE,
  variant TEXT NOT NULL,
  assigned_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  UNIQUE (user_key, experiment_id)
);

CREATE TABLE IF NOT EXISTS experiment_runs (
  id SERIAL PRIMARY KEY,
  experiment_id INT NOT NULL REFERENCES experiments(id) ON DELETE CASCADE,
  assessment_id INT NOT NULL REFERENCES assessments(id) ON DELETE CASCADE,
  variant TEXT NOT NULL,
  output JSONB NOT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_labels_assessment_id ON labels(assessment_id);
CREATE INDEX IF NOT EXISTS idx_experiment_runs_experiment_assessment ON experiment_runs(experiment_id, assessment_id);
CREATE INDEX IF NOT EXISTS idx_experiment_assignments_user_key ON experiment_assignments(user_key);
