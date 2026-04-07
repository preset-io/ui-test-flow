-- Migration: Add enhanced profile fields
-- Created: 2025-11-29
-- Description: Add support for profile types, execution modes, init steps, LLM config, and tags

-- Add new columns to profiles table
ALTER TABLE profiles
ADD COLUMN IF NOT EXISTS description TEXT,
ADD COLUMN IF NOT EXISTS profile_type VARCHAR(50) DEFAULT 'environment',
ADD COLUMN IF NOT EXISTS execution_mode VARCHAR(50) DEFAULT 'automated',
ADD COLUMN IF NOT EXISTS init_steps JSON DEFAULT '[]'::JSON,
ADD COLUMN IF NOT EXISTS llm_config JSON DEFAULT '{}'::JSON,
ADD COLUMN IF NOT EXISTS tags JSON DEFAULT '[]'::JSON,
ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP DEFAULT NOW();

-- Create index on profile_type for faster filtering
CREATE INDEX IF NOT EXISTS idx_profiles_profile_type ON profiles(profile_type);

-- Create index on tags for searching (convert to jsonb for GIN index)
CREATE INDEX IF NOT EXISTS idx_profiles_tags ON profiles USING GIN (CAST(tags AS jsonb));

-- Add comment describing profile_type values
COMMENT ON COLUMN profiles.profile_type IS 'Profile type: environment, workflow, or custom';

-- Add comment describing execution_mode values
COMMENT ON COLUMN profiles.execution_mode IS 'Execution mode: automated, manual, or hybrid';

-- Add comment describing init_steps
COMMENT ON COLUMN profiles.init_steps IS 'Initialization steps to run before tests (login, navigation, etc.)';

-- Add comment describing llm_config
COMMENT ON COLUMN profiles.llm_config IS 'LLM configuration for test generation and healing';

-- Update existing rows to have the new updated_at value
UPDATE profiles SET updated_at = created_at WHERE updated_at IS NULL;
