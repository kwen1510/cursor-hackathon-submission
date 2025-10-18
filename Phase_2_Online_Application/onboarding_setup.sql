-- Onboarding Sessions Table
-- Stores teacher onboarding conversations and research results

CREATE TABLE IF NOT EXISTS onboarding_sessions (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  user_email TEXT NOT NULL,
  goal_text TEXT,
  conversation_json JSONB,
  manus_task_id TEXT,
  manus_task_url TEXT,
  research_output TEXT,
  research_sources JSONB,
  status TEXT DEFAULT 'in_progress' CHECK (status IN ('in_progress', 'researching', 'completed')),
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Index for faster lookups by email
CREATE INDEX IF NOT EXISTS idx_onboarding_sessions_email ON onboarding_sessions(user_email);

-- Index for faster lookups by status
CREATE INDEX IF NOT EXISTS idx_onboarding_sessions_status ON onboarding_sessions(status);

-- Index for faster lookups by manus_task_id
CREATE INDEX IF NOT EXISTS idx_onboarding_sessions_manus_task_id ON onboarding_sessions(manus_task_id);

