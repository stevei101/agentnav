# Prompt Vault Secrets Setup Guide

**Status:** In Progress  
**Last Updated:** November 5, 2025

---

## Overview

Prompt Vault requires secrets in two places:
1. **GitHub Secrets** - For CI/CD workflows (building and deploying)
2. **GCP Secret Manager** - For Cloud Run services (runtime access)

---

## ✅ Current Status

### GitHub Secrets (Added)
- ✅ `SUPABASE_URL`
- ✅ `SUPABASE_ANON_KEY`

### GitHub Secrets (Still Needed)
- [ ] `SUPABASE_SERVICE_KEY` (only if using backend service, not Supabase Edge Functions)
- [ ] `GOOGLE_OAUTH_CLIENT_ID` (for Google Sign-in via Supabase)
- [ ] `GOOGLE_OAUTH_CLIENT_SECRET` (for Google Sign-in via Supabase)

### GCP Secret Manager (Needed)
- [ ] `SUPABASE_URL` - Create secret and add value
- [ ] `SUPABASE_ANON_KEY` - Create secret and add value
- [ ] `SUPABASE_SERVICE_KEY` - Create secret (only if using backend)
- [ ] `GOOGLE_OAUTH_CLIENT_ID` - Create secret
- [ ] `GOOGLE_OAUTH_CLIENT_SECRET` - Create secret

---

## Why Two Places?

### GitHub Secrets
- Used by GitHub Actions workflows during CI/CD
- Accessed via `${{ secrets.SECRET_NAME }}`
- Used for building and deploying containers
- **Not accessible to running Cloud Run services**

### GCP Secret Manager
- Used by Cloud Run services at runtime
- Accessed via environment variables injected from secrets
- Required for the application to actually use these values
- **Not accessible to GitHub Actions workflows**

---

## Setup Steps

### Step 1: Create Secrets in GCP Secret Manager

Run `terraform apply` to create the secret containers (or create manually):

```bash
cd terraform
terraform apply
```

This creates the secret containers but doesn't add values yet.

### Step 2: Add Values to GCP Secret Manager

After Terraform creates the secrets, add the actual values:

```bash
# Set your project ID
export PROJECT_ID="your-gcp-project-id"

# Add Supabase URL (from your Supabase dashboard)
echo -n "https://wgdqmufqwcezvwjdoumu.supabase.co" | \
  gcloud secrets versions add SUPABASE_URL \
  --data-file=- \
  --project=${PROJECT_ID}

# Add Supabase Publishable Key (from Supabase Dashboard → Settings → API → API Keys → Publishable key)
# Format: sb_publishable_...
echo -n "sb_publishable_bel3_K8s8fsNbUq_SS4C-A_rBYhymNK" | \
  gcloud secrets versions add SUPABASE_ANON_KEY \
  --data-file=- \
  --project=${PROJECT_ID}

# Add Supabase Secret Key (only if using backend, get from Supabase Dashboard → Settings → API → API Keys → Secret keys)
# Format: sb_...
# echo -n "sb_your-secret-key-here" | \
#   gcloud secrets versions add SUPABASE_SERVICE_KEY \
#   --data-file=- \
#   --project=${PROJECT_ID}

# Add Google OAuth Client ID (after creating OAuth credentials in GCP Console)
# See PROMPT_VAULT_GOOGLE_OAUTH_SETUP.md for detailed instructions
# echo -n "your-google-client-id.apps.googleusercontent.com" | \
#   gcloud secrets versions add GOOGLE_OAUTH_CLIENT_ID \
#   --data-file=- \
#   --project=${PROJECT_ID}

# Add Google OAuth Client Secret
# echo -n "your-google-client-secret" | \
#   gcloud secrets versions add GOOGLE_OAUTH_CLIENT_SECRET \
#   --data-file=- \
#   --project=${PROJECT_ID}
```

### Step 3: Add Remaining GitHub Secrets

Add to GitHub repository settings → Secrets and variables → Actions:

- `SUPABASE_SERVICE_KEY` (if using backend)
- `GOOGLE_OAUTH_CLIENT_ID`
- `GOOGLE_OAUTH_CLIENT_SECRET`

---

## Where to Find Supabase Keys

### Supabase Dashboard
1. Go to: https://supabase.com/dashboard/project/wgdqmufqwcezvwjdoumu
2. Navigate to: **Settings** → **API** → **API Keys**
3. Find:
   - **Project URL**: `https://wgdqmufqwcezvwjdoumu.supabase.co` ✅ (You have this)
   - **Publishable key**: Copy this for `SUPABASE_ANON_KEY` ✅ (You have this)
     - Format: `sb_publishable_...`
     - Safe to use in frontend if RLS is enabled
   - **Secret keys** → **New secret key**: Copy this for `SUPABASE_SERVICE_KEY` (if needed)
     - Format: `sb_...`
     - ⚠️ Backend/admin use only - never expose in frontend

---

## Do You Need SUPABASE_SERVICE_KEY?

**Answer:** **No, not for the current frontend-only implementation.**

### ❌ **Don't Need It (Current Setup):**
- ✅ Frontend uses Supabase client directly with `SUPABASE_ANON_KEY`
- ✅ All database operations go through Row Level Security (RLS) policies
- ✅ No backend service deployed yet
- ✅ Authentication handled by Supabase Auth

### ✅ **Need It If You Add Later:**
- Building a separate backend service (`prompt-vault-backend` Cloud Run service)
- Need to bypass RLS for admin operations
- Server-side operations that require elevated privileges
- Batch operations or data migrations

**For Prompt Vault:** The current implementation is **frontend-only** and doesn't require `SUPABASE_SERVICE_KEY`. The infrastructure is set up for it (in Terraform and GitHub Actions), but you can skip adding this secret until you actually build a backend service.

---

## Environment Variables in Cloud Run

The Terraform configuration in `prompt_vault_cloud_run.tf` automatically injects these secrets as environment variables:

**Frontend (`prompt-vault-frontend`):**
- `SUPABASE_URL` (from Secret Manager)
- `SUPABASE_ANON_KEY` (from Secret Manager)
- `NEXT_PUBLIC_GOOGLE_CLIENT_ID` (from Secret Manager)

**Backend (`prompt-vault-backend`):** (if deployed)
- `SUPABASE_URL` (from Secret Manager)
- `SUPABASE_SERVICE_KEY` (from Secret Manager)

---

## Verification

### Check GitHub Secrets
1. Go to: GitHub repo → Settings → Secrets and variables → Actions
2. Verify: `SUPABASE_URL` and `SUPABASE_ANON_KEY` are present ✅

### Check GCP Secret Manager
```bash
gcloud secrets list --project=${PROJECT_ID} --filter="labels.app=prompt-vault"
```

Should show:
- `SUPABASE_URL`
- `SUPABASE_ANON_KEY`
- `SUPABASE_SERVICE_KEY` (if created)
- `GOOGLE_OAUTH_CLIENT_ID` (after OAuth setup)
- `GOOGLE_OAUTH_CLIENT_SECRET` (after OAuth setup)

### Verify Secret Values
```bash
# Check if secret has a value (won't show the value, just confirms it exists)
gcloud secrets versions access latest --secret=SUPABASE_URL --project=${PROJECT_ID}
```

---

## Next Steps

1. ✅ **Done:** Added GitHub Secrets for `SUPABASE_URL` and `SUPABASE_ANON_KEY`
2. [ ] Run `terraform apply` to create Secret Manager secrets
3. [ ] Add values to GCP Secret Manager (see Step 2 above)
4. [ ] Set up Google OAuth credentials - **See [PROMPT_VAULT_GOOGLE_OAUTH_SETUP.md](./PROMPT_VAULT_GOOGLE_OAUTH_SETUP.md) for complete guide**
5. [ ] Add Google OAuth secrets to both GitHub and GCP Secret Manager

---

## Related Documentation

- [PROMPT_VAULT_ISOLATION_PLAN.md](./PROMPT_VAULT_ISOLATION_PLAN.md) - Complete isolation strategy
- [Issue #193](https://github.com/stevei101/agentnav/issues/193) - Supabase Authentication (Google Sign-in)
- [Issue #196](https://github.com/stevei101/agentnav/issues/196) - Parallel Deployment and Isolation

