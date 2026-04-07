-- Migration: Add environment_status to profiles
-- Created: 2025-11-30
-- Description: Add environment_status field to track profile environment state

-- Add environment_status column to profiles table
ALTER TABLE profiles
ADD COLUMN IF NOT EXISTS environment_status VARCHAR(50);

-- Add comment describing environment_status values
COMMENT ON COLUMN profiles.environment_status IS 'Environment status: running, stopped, error, etc.';
