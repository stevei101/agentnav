# Prompt Vault Database Setup

This directory contains the database schema for Prompt Vault, which uses Supabase (PostgreSQL) for persistence.

## Setup Instructions

1. **Create a Supabase Project**
   - Go to [supabase.com](https://supabase.com) and create a new project
   - Wait for the project to be provisioned

2. **Run the Schema SQL**
   - Open your Supabase project dashboard
   - Navigate to **SQL Editor**
   - Copy and paste the contents of `schema.sql`
   - Click **Run** to execute the schema

3. **Configure Authentication**
   - Go to **Authentication** → **Providers** in your Supabase dashboard
   - Enable **Google** provider
   - Add your Google OAuth Client ID and Client Secret
   - Add authorized redirect URLs:
     - `https://{your-project-ref}.supabase.co/auth/v1/callback`
     - For local development: `http://localhost:5173`

4. **Get Your API Keys**
   - Go to **Settings** → **API**
   - Copy the **Project URL** (this is your `SUPABASE_URL`)
   - Copy the **Publishable key** (this is your `SUPABASE_ANON_KEY`)
   - Optionally copy the **Secret key** (for backend operations, if needed)

5. **Add Secrets to GCP Secret Manager**
   - Follow the instructions in `../docs/PROMPT_VAULT_SECRETS_SETUP.md`

## Schema Overview

The schema creates a `prompts` table with the following features:

- **Row Level Security (RLS)**: Enabled to ensure users can only access their own prompts
- **Automatic Timestamps**: `created_at` and `updated_at` are automatically managed
- **Indexes**: Optimized for common query patterns (user_id, dates, categories, tags)
- **Array Support**: Tags are stored as PostgreSQL arrays for efficient searching

## Security Policies

The schema includes RLS policies that:

- Allow users to view their own prompts
- Allow anyone to view public prompts (`is_public = true`)
- Allow users to create, update, and delete only their own prompts

## Local Development

For local development, you can use Supabase's local development setup:

```bash
# Install Supabase CLI
npm install -g supabase

# Initialize Supabase locally
supabase init

# Start local Supabase
supabase start

# Run migrations
supabase db reset
```

Then update your `.env.local` with:

```
VITE_SUPABASE_URL=http://localhost:54321
VITE_SUPABASE_ANON_KEY=<local-anon-key>
```
