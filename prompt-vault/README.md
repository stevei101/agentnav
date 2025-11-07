# Prompt Vault

**GenAI Prompt Management App** - A companion application to agentnav for managing and testing AI prompts.

## Overview

Prompt Vault is a separate application that uses:

- **Supabase** for authentication and database
- **React/TypeScript** for the frontend
- **bun** for package management
- **Google Cloud Run** for deployment

## Isolation Strategy

This application is completely isolated from the main `agentnav` application:

- **Container Image:** `prompt-management-app` (vs `agentnav-frontend`, `agentnav-backend`)
- **Cloud Run Service:** `prompt-management-app`
- **CI/CD Workflow:** Separate workflow file (`.github/workflows/build-prompt-vault.yml`) with path filtering
- **GAR Repository:** Dedicated `prompt-vault` repository in `us-central1`
- **Service Account:** `agentnav-prompt-mgmt@${PROJECT_ID}.iam.gserviceaccount.com`

## Local Development

### Prerequisites

- **bun** installed ([install bun](https://bun.sh))
- **Supabase** project set up (see [database/README.md](./database/README.md))
- Environment variables configured

### Setup

1. **Install dependencies:**

```bash
cd prompt-vault/frontend
bun install
```

2. **Create `.env.local` file in `frontend/` directory:**

```bash
VITE_SUPABASE_URL=https://your-project-ref.supabase.co
VITE_SUPABASE_ANON_KEY=your_supabase_anon_key
VITE_GOOGLE_CLIENT_ID=your_google_oauth_client_id
```

3. **Set up Supabase database:**
   - Follow instructions in [database/README.md](./database/README.md)
   - Run the SQL schema in your Supabase SQL Editor

4. **Start development server:**

```bash
cd prompt-vault/frontend
bun run dev
```

The app will be available at `http://localhost:5173`

### Development Commands

```bash
# Install dependencies
bun install

# Start dev server
bun run dev

# Build for production
bun run build

# Preview production build
bun run preview

# Type checking
bun run type-check

# Linting
bun run lint
```

## Project Structure

```
prompt-vault/
├── frontend/          # React frontend application
├── backend/           # Optional backend (if not using Supabase Edge Functions)
├── Dockerfile         # Production Dockerfile for frontend
├── package.json       # Dependencies and scripts
└── README.md          # This file
```

## Deployment

Deployment is handled automatically via GitHub Actions:

- **Trigger:** Changes to `prompt-vault/` directory
- **Workflow:** `.github/workflows/build-prompt-vault.yml`
- **Image Tagging:** Same strategy as agentnav (pr-{number}, {sha}, latest)
- **Registry:** `us-central1-docker.pkg.dev/${PROJECT_ID}/prompt-vault/prompt-management-app:${TAG}`

## Environment Variables (Cloud Run)

The following secrets are injected from Secret Manager:

- `SUPABASE_URL`
- `SUPABASE_ANON_KEY`
- `NEXT_PUBLIC_GOOGLE_CLIENT_ID` (for Google Sign-in via Supabase)

## Related Documentation

- [PROMPT_VAULT_ISOLATION_PLAN.md](../docs/PROMPT_VAULT_ISOLATION_PLAN.md) - Complete isolation strategy
- [Issue #196](https://github.com/stevei101/agentnav/issues/196) - Feature request for parallel deployment
