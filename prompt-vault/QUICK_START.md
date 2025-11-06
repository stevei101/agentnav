# Prompt Vault - Quick Start Guide

Get Prompt Vault up and running in 5 minutes!

## 1. Set Up Supabase (5 minutes)

1. **Create Supabase Project**
   - Go to [supabase.com](https://supabase.com) and create a new project
   - Wait for provisioning (usually 1-2 minutes)

2. **Run Database Schema**
   - In Supabase Dashboard → **SQL Editor**
   - Copy contents of `database/schema.sql`
   - Click **Run**

3. **Configure Google OAuth**
   - Go to **Authentication** → **Providers** → **Google**
   - Enable Google provider
   - Add your Google OAuth credentials
   - Add redirect URL: `https://{project-ref}.supabase.co/auth/v1/callback`

4. **Get API Keys**
   - Go to **Settings** → **API**
   - Copy **Project URL** → `SUPABASE_URL`
   - Copy **Publishable key** → `SUPABASE_ANON_KEY`

## 2. Local Development (2 minutes)

```bash
# Navigate to frontend
cd prompt-vault/frontend

# Install dependencies
bun install

# Create .env.local
cat > .env.local << EOF
VITE_SUPABASE_URL=https://your-project-ref.supabase.co
VITE_SUPABASE_ANON_KEY=your_publishable_key_here
VITE_GOOGLE_CLIENT_ID=your-google-client-id.apps.googleusercontent.com
EOF

# Note: You only need the Google OAuth Client ID, NOT the Client Secret!
# The Client Secret is stored in Supabase Dashboard and used server-side by Supabase.

# Start dev server
bun run dev
```

Visit `http://localhost:5173` and sign in with Google!

## 3. Deploy to Cloud Run (Automatic)

Once you push to the `main` or `main-promptvault` branch:

1. **GitHub Actions** will automatically:
   - Build the container image
   - Push to Google Artifact Registry
   - Deploy to Cloud Run

2. **Set up Secrets in GCP Secret Manager:**
   ```bash
   # Add Supabase secrets
   echo -n "https://your-project-ref.supabase.co" | gcloud secrets create SUPABASE_URL --data-file=-
   echo -n "your_publishable_key" | gcloud secrets create SUPABASE_ANON_KEY --data-file=-
   echo -n "your_google_client_id" | gcloud secrets create GOOGLE_OAUTH_CLIENT_ID --data-file=-
   ```

3. **Access your deployed app:**
   - Frontend URL will be shown in GitHub Actions summary
   - Or find it in Cloud Run console

## What's Next?

- ✨ Create your first prompt
- 🔍 Search and organize prompts
- 📝 Edit and refine prompts
- 🌐 Share public prompts

## Troubleshooting

**"Missing Supabase credentials" error:**
- Check your `.env.local` file exists
- Verify environment variable names start with `VITE_`

**"Authentication failed":**
- Verify Google OAuth is enabled in Supabase
- Check redirect URL matches Supabase callback URL

**"Database error":**
- Make sure you ran the schema SQL in Supabase
- Check Row Level Security policies are active

## Need Help?

- See [database/README.md](./database/README.md) for database setup
- See [docs/PROMPT_VAULT_ISOLATION_PLAN.md](../docs/PROMPT_VAULT_ISOLATION_PLAN.md) for architecture details

