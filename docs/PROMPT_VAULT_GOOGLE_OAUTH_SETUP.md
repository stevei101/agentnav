# Google OAuth Setup for Prompt Vault

This guide walks you through setting up Google OAuth for Supabase authentication in Prompt Vault.

---

## Overview

The setup involves 4 steps:
1. **Create OAuth credentials in Google Cloud Console** (manual)
2. **Configure OAuth in Supabase Dashboard** (manual)
3. **Store credentials in GCP Secret Manager** (gcloud commands)
4. **Add credentials to GitHub Secrets** (manual)

---

## Step 1: Create OAuth Credentials in Google Cloud Console

### 1.1 Enable Google+ API (if not already enabled)

```bash
# Set your project ID
export PROJECT_ID="your-gcp-project-id"

# Enable Google+ API (required for OAuth)
gcloud services enable plus.googleapis.com --project=${PROJECT_ID}

# Or use the console: https://console.cloud.google.com/apis/library/plus.googleapis.com
```

### 1.2 Configure OAuth Consent Screen

**Via Console (Recommended):**
1. Go to: [Google Cloud Console → APIs & Services → OAuth consent screen](https://console.cloud.google.com/apis/credentials/consent)
2. **Select User Type (Audience):**
   
   **External** - ✅ **Recommended for Prompt Vault**
   - **What it means:** Anyone with a Google account (gmail.com, Google Workspace, etc.) can sign in
   - **Use case:** Public applications, SaaS apps, apps for end users
   - **Limitations:** 
     - Up to 100 test users can sign in before app verification
     - Requires Google's verification process if you want to publish to more than 100 users
     - For basic scopes (`email`, `profile`, `openid`): Usually no verification needed if you add test users
   - **Best for:** Most applications, including Prompt Vault
   
   **Internal** - ❌ **Only if you have Google Workspace**
   - **What it means:** Only users in your Google Workspace organization can sign in
   - **Use case:** Internal company tools, enterprise applications
   - **Requirements:** 
     - Must have a Google Workspace account (not just a GCP account)
     - Must be in the same organization as your GCP project
   - **Best for:** Internal tools within a company
   
   **For Prompt Vault:** 
   - ✅ **Select "External"** - This allows any Google user to sign in to your app
   - You can add up to 100 test users during development
   - No verification needed for basic scopes (`email`, `profile`, `openid`) if you add test users
3. Fill in required fields:
   - **App name**: `Prompt Vault`
   - **User support email**: Your email
   - **Developer contact information**: Your email
4. Click **Save and Continue**
5. **Scopes (Data Access)**: This is critical for Supabase!
   - Click **Add or Remove Scopes**
   - **Required scopes for Supabase:**
     - ✅ `openid` - **MUST be added manually** (this is the key one!)
     - ✅ `.../auth/userinfo.email` - Usually added by default
     - ✅ `.../auth/userinfo.profile` - Usually added by default
   - **Important**: The `openid` scope is often not added by default - you need to add it manually!
   - If you don't see `openid` in the list, search for it or it might be under "OpenID Connect"
   - **Warning**: Adding sensitive or restricted scopes may require app verification
   - Click **Update** when done
6. Click **Save and Continue**
7. **Test users**: Add your email for testing (optional, recommended for External apps)
   - **Important for External apps**: You can add up to 100 test users before publishing
   - These users can sign in even if the app isn't verified yet
   - Recommended: Add your email and any team members' emails
8. Click **Save and Continue**

**Via gcloud (Advanced):**
```bash
# Note: This is complex - using console is recommended
# But you can view current consent screen:
gcloud alpha iap oauth-clients list --project=${PROJECT_ID}
```

### 1.3 Create OAuth 2.0 Client ID

**Step-by-Step Instructions:**

1. **Navigate to Credentials Page:**
   - Go to: https://console.cloud.google.com/apis/credentials?project=linear-archway-476722-v0
   - Or: Click the hamburger menu (☰) → **APIs & Services** → **Credentials**
   - Make sure your project is selected: `linear-archway-476722-v0`

2. **Create OAuth Client:**
   - Click the **+ CREATE CREDENTIALS** button at the top
   - Select **OAuth client ID** from the dropdown
   - If this is your first time, you may need to configure the OAuth consent screen first (see Step 1.2 above)

3. **Select Application Type:**
   - Choose **Web application** (not Desktop app, not iOS/Android)

4. **Configure OAuth Client:**
   - **Name**: `Prompt Vault - Supabase`
   
   - **Authorized JavaScript origins** (click **+ ADD URI** for each):
     - `https://wgdqmufqwcezvwjdoumu.supabase.co` (your Supabase project URL)
     - `http://localhost:5173` (for local development)
   
   - **Authorized redirect URIs** (click **+ ADD URI** for each):
     - `https://wgdqmufqwcezvwjdoumu.supabase.co/auth/v1/callback` ✅ (This is your Supabase callback URL)
     - `http://localhost:5173/auth/v1/callback` (for local dev - optional)

5. **Create and Copy Credentials:**
   - Click **Create**
   - A popup will appear showing:
     - **Your Client ID**: `xxxxx-yyyyyyyyyy.apps.googleusercontent.com` ← **COPY THIS!**
     - **Your Client Secret**: `GOCSPX-xxxxxxxxxxxxx` ← **COPY THIS!**
   - ⚠️ **Important**: Copy both values immediately - you won't be able to see the secret again!
   - Click **OK** to close the popup

6. **Save Credentials:**
   - You can see your OAuth client in the credentials list
   - The Client ID is always visible
   - The Client Secret is hidden (you can only see it once when created)

**Direct Links:**
- **Credentials Page**: https://console.cloud.google.com/apis/credentials?project=linear-archway-476722-v0
- **OAuth Consent Screen** (do this first if not done): https://console.cloud.google.com/apis/credentials/consent?project=linear-archway-476722-v0

**Via gcloud (Alternative):**
```bash
# Create OAuth client
gcloud alpha iap oauth-clients create \
  --display_name="Prompt Vault - Supabase" \
  --project=${PROJECT_ID}

# Note: The above command is for IAP, not standard OAuth. 
# For standard OAuth, use the console or REST API:
# https://cloud.google.com/identity-platform/docs/rest/v1/projects.oauthIdpConfigs/create
```

**Recommended:** Use the console method above as it's the most straightforward.

---

## Step 2: Configure OAuth in Supabase Dashboard

1. Go to your Supabase project: https://supabase.com/dashboard/project/wgdqmufqwcezvwjdoumu
2. Navigate to: **Authentication** → **Providers**
3. Find **Google** in the list and click to expand
4. Click **Enable Google provider**
5. Enter:
   - **Client ID (for OAuth)**: Paste your Google OAuth Client ID
   - **Client Secret (for OAuth)**: Paste your Google OAuth Client Secret
6. Click **Save**

**Note:** The Client ID from Step 1.3 goes here. This is the `VITE_GOOGLE_CLIENT_ID` you'll use in the frontend.

---

## Step 3: Store Credentials in GCP Secret Manager

Once you have the Client ID and Client Secret from Step 1.3, store them in Secret Manager:

```bash
# Set your project ID
export PROJECT_ID="your-gcp-project-id"

# Make sure secrets exist (created by Terraform)
# If not, create them first:
# gcloud secrets create GOOGLE_OAUTH_CLIENT_ID --project=${PROJECT_ID}
# gcloud secrets create GOOGLE_OAUTH_CLIENT_SECRET --project=${PROJECT_ID}

# Add Google OAuth Client ID
# Replace 'your-client-id-here' with the actual Client ID from Step 1.3
echo -n "your-client-id-here.apps.googleusercontent.com" | \
  gcloud secrets versions add GOOGLE_OAUTH_CLIENT_ID \
  --data-file=- \
  --project=${PROJECT_ID}

# Add Google OAuth Client Secret
# Replace 'your-client-secret-here' with the actual Client Secret from Step 1.3
echo -n "your-client-secret-here" | \
  gcloud secrets versions add GOOGLE_OAUTH_CLIENT_SECRET \
  --data-file=- \
  --project=${PROJECT_ID}

# Verify secrets were added
gcloud secrets versions list GOOGLE_OAUTH_CLIENT_ID --project=${PROJECT_ID}
gcloud secrets versions list GOOGLE_OAUTH_CLIENT_SECRET --project=${PROJECT_ID}
```

**Note:** The Client ID format is usually: `xxxxx.apps.googleusercontent.com`

---

## Step 4: Add Credentials to GitHub Secrets

1. Go to your GitHub repository: https://github.com/stevei101/agentnav
2. Navigate to: **Settings** → **Secrets and variables** → **Actions**
3. Click **New repository secret**
4. Add each secret:
   - **Name**: `GOOGLE_OAUTH_CLIENT_ID`
     - **Value**: Your Google OAuth Client ID (from Step 1.3)
   - **Name**: `GOOGLE_OAUTH_CLIENT_SECRET`
     - **Value**: Your Google OAuth Client Secret (from Step 1.3)

---

## Step 5: Add to Local Development `.env.local`

For local development, create `prompt-vault/frontend/.env.local`:

```bash
# Supabase credentials
VITE_SUPABASE_URL=https://wgdqmufqwcezvwjdoumu.supabase.co
VITE_SUPABASE_ANON_KEY=your_supabase_anon_key

# Google OAuth Client ID (use the Client ID from Step 1.3)
# Note: You only need the Client ID, NOT the Client Secret!
VITE_GOOGLE_CLIENT_ID=your-client-id-here.apps.googleusercontent.com
```

**Important Notes:**
- ✅ **You only need the Client ID** - Never put the Client Secret in `.env.local`!
- ✅ **Client Secret is stored in Supabase Dashboard** (Step 2) - Supabase uses it server-side
- ✅ **Client Secret should never be exposed to the frontend** - It's only used by Supabase's backend
- ✅ **The Client ID is safe to expose** - It's meant to be public (like a public API key)

---

## Verification

### 1. Check GCP Secret Manager
```bash
# Verify secrets exist and have values
gcloud secrets versions access latest --secret=GOOGLE_OAUTH_CLIENT_ID --project=${PROJECT_ID}
gcloud secrets versions access latest --secret=GOOGLE_OAUTH_CLIENT_SECRET --project=${PROJECT_ID}
```

### 2. Test in Supabase Dashboard
1. Go to Supabase Dashboard → Authentication → Providers
2. Verify Google provider is enabled
3. Test the connection (if Supabase provides a test button)

### 3. Test in Local Development
```bash
cd prompt-vault/frontend
bun run dev
```

Visit `http://localhost:5173` and try clicking "Sign in with Google". You should see:
- ✅ Google OAuth popup/redirect
- ✅ Successful authentication
- ✅ Redirected back to the app

### 4. Test in Production (after deployment)
After deploying to Cloud Run, the secrets are automatically injected. Test the Google Sign-in button.

---

## Troubleshooting

### "Error: redirect_uri_mismatch"
- **Cause**: The redirect URI in your OAuth credentials doesn't match Supabase's callback URL
- **Fix**: 
  1. Go to Google Cloud Console → Credentials → Your OAuth Client
  2. Add: `https://wgdqmufqwcezvwjdoumu.supabase.co/auth/v1/callback`
  3. For local dev: `http://localhost:5173/auth/v1/callback`

### "Error: invalid_client"
- **Cause**: Client ID or Client Secret is incorrect
- **Fix**: 
  1. Verify the Client ID/Secret in Supabase Dashboard → Authentication → Providers
  2. Make sure you copied the full Client ID (including `.apps.googleusercontent.com`)

### "Unsupported provider: provider is not enabled" (Error 400)
- **Cause**: Google OAuth provider is not enabled in Supabase Dashboard
- **Fix**: 
  1. Go to: https://supabase.com/dashboard/project/wgdqmufqwcezvwjdoumu/auth/providers
  2. Find **Google** in the providers list
  3. Click on **Google** to expand it
  4. Toggle **Enable Google provider** to ON
  5. Enter your **Client ID (for OAuth)** from Google Cloud Console
  6. Enter your **Client Secret (for OAuth)** from Google Cloud Console
  7. Click **Save**
  8. Try signing in again

### "OAuth consent screen not configured"
- **Cause**: OAuth consent screen isn't set up
- **Fix**: Complete Step 1.2 above

### "Access blocked: This app's request is invalid"
- **Cause**: App verification required or test users not added
- **Fix**: 
  - For External apps: Add test users in Step 1.2 (Test users section)
  - For production: Submit app for verification (only needed if requesting sensitive scopes or publishing to many users)
  - For basic `email`, `profile`, `openid` scopes: Usually no verification needed if you add test users

### "Missing required scope: openid" or authentication fails silently
- **Cause**: The `openid` scope is not added to your OAuth consent screen
- **Fix**: 
  1. Go to Google Cloud Console → APIs & Services → OAuth consent screen
  2. Click on the **Scopes** tab
  3. Click **Add or Remove Scopes**
  4. Search for `openid` and make sure it's checked
  5. If you don't see it, it might be listed as "OpenID Connect" or under "OpenID Connect scopes"
  6. Click **Update** and **Save and Continue**
  7. Try signing in again

### Google Sign-in button not showing
- **Cause**: `VITE_GOOGLE_CLIENT_ID` not set in `.env.local`
- **Fix**: Add it to your `.env.local` file (see Step 5)

---

## Quick Reference

### OAuth Client ID Format
```
xxxxx-yyyyyyyyyy.apps.googleusercontent.com
```

### Redirect URIs to Add
- **Production**: `https://{your-supabase-project-ref}.supabase.co/auth/v1/callback`
- **Local Dev**: `http://localhost:5173/auth/v1/callback`

### Where Credentials Are Used

| Location | What's Needed | Source |
|----------|--------------|--------|
| **Supabase Dashboard** | Client ID + Client Secret | Google Cloud Console |
| **GCP Secret Manager** | Client ID + Client Secret | Google Cloud Console |
| **GitHub Secrets** | Client ID + Client Secret | Google Cloud Console |
| **Frontend `.env.local`** | Client ID only | Google Cloud Console |
| **Cloud Run (via Secret Manager)** | Client ID only | Injected from Secret Manager |

---

## Related Documentation

- [PROMPT_VAULT_SECRETS_SETUP.md](./PROMPT_VAULT_SECRETS_SETUP.md) - General secrets setup
- [PROMPT_VAULT_ISOLATION_PLAN.md](./PROMPT_VAULT_ISOLATION_PLAN.md) - Architecture overview
- [Supabase Google Auth Docs](https://supabase.com/docs/guides/auth/social-login/auth-google)
- [Google OAuth 2.0 Docs](https://developers.google.com/identity/protocols/oauth2)

---

## Summary Checklist

- [ ] Step 1: Created OAuth credentials in Google Cloud Console
- [ ] Step 1.2: Configured OAuth consent screen
- [ ] Step 1.3: Created OAuth Client ID and Secret
- [ ] Step 2: Added credentials to Supabase Dashboard
- [ ] Step 3: Stored credentials in GCP Secret Manager
- [ ] Step 4: Added credentials to GitHub Secrets
- [ ] Step 5: Added `VITE_GOOGLE_CLIENT_ID` to `.env.local`
- [ ] Verified: Tested Google Sign-in locally
- [ ] Verified: Tested Google Sign-in in production (after deploy)

