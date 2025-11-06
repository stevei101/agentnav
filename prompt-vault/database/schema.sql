-- Prompt Vault Database Schema
-- This SQL should be run in your Supabase SQL Editor

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Create prompts table
CREATE TABLE IF NOT EXISTS prompts (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    title TEXT NOT NULL,
    content TEXT NOT NULL,
    description TEXT,
    category TEXT,
    tags TEXT[] DEFAULT '{}',
    is_public BOOLEAN DEFAULT false,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create index on user_id for faster queries
CREATE INDEX IF NOT EXISTS idx_prompts_user_id ON prompts(user_id);

-- Create index on created_at for sorting
CREATE INDEX IF NOT EXISTS idx_prompts_created_at ON prompts(created_at DESC);

-- Create index on updated_at for sorting
CREATE INDEX IF NOT EXISTS idx_prompts_updated_at ON prompts(updated_at DESC);

-- Create index on category for filtering
CREATE INDEX IF NOT EXISTS idx_prompts_category ON prompts(category) WHERE category IS NOT NULL;

-- Create index on tags using GIN for array searches
CREATE INDEX IF NOT EXISTS idx_prompts_tags ON prompts USING GIN(tags);

-- Create function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Create trigger to automatically update updated_at
CREATE TRIGGER update_prompts_updated_at
    BEFORE UPDATE ON prompts
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Enable Row Level Security (RLS)
ALTER TABLE prompts ENABLE ROW LEVEL SECURITY;

-- Create policy: Users can only see their own prompts (unless public)
CREATE POLICY "Users can view their own prompts"
    ON prompts FOR SELECT
    USING (auth.uid() = user_id);

-- Create policy: Users can view public prompts
CREATE POLICY "Anyone can view public prompts"
    ON prompts FOR SELECT
    USING (is_public = true);

-- Create policy: Users can insert their own prompts
CREATE POLICY "Users can insert their own prompts"
    ON prompts FOR INSERT
    WITH CHECK (auth.uid() = user_id);

-- Create policy: Users can update their own prompts
CREATE POLICY "Users can update their own prompts"
    ON prompts FOR UPDATE
    USING (auth.uid() = user_id)
    WITH CHECK (auth.uid() = user_id);

-- Create policy: Users can delete their own prompts
CREATE POLICY "Users can delete their own prompts"
    ON prompts FOR DELETE
    USING (auth.uid() = user_id);

