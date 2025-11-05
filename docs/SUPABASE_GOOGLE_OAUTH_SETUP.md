# Supabase Google OAuth Setup Guide

This guide provides step-by-step instructions for configuring Google OAuth authentication in Supabase for the Gen AI Prompt Management App.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Google Cloud Project Configuration](#google-cloud-project-configuration)
3. [Supabase Dashboard Configuration](#supabase-dashboard-configuration)
4. [Environment Variables](#environment-variables)
5. [Testing the OAuth Flow](#testing-the-oauth-flow)
6. [Troubleshooting](#troubleshooting)

---

## Prerequisites

Before you begin, ensure you have:

- ✅ A Google Cloud Project (can be the same as the agentnav project)
- ✅ A Supabase account and project
- ✅ Access to the Supabase project dashboard
- ✅ Admin access to Google Cloud Console
- ✅ The Gen AI Prompt Management App repository cloned

---

## Google Cloud Project Configuration

### Step 1: Enable Google+ API (if not already enabled)

1. Navigate to the [Google Cloud Console](https://console.cloud.google.com/)
2. Select your project
3. Go to **APIs & Services** > **Library**
4. Search for "Google+ API"
5. Click **Enable** (if not already enabled)

### Step 2: Create OAuth 2.0 Credentials

1. Go to **APIs & Services** > **Credentials**
2. Click **+ CREATE CREDENTIALS** > **OAuth client ID**
3. If prompted to configure the OAuth consent screen:
   - Select **External** user type (or **Internal** if using Google Workspace)
   - Fill in the required fields:
     - **App name**: Gen AI Prompt Management App
     - **User support email**: Your email
     - **Developer contact information**: Your email
   - Click **Save and Continue**
   - Skip the "Scopes" section (click **Save and Continue**)
   - Skip the "Test users" section (click **Save and Continue**)
   - Click **Back to Dashboard**

4. Return to **Credentials** > **+ CREATE CREDENTIALS** > **OAuth client ID**
5. Select **Application type**: **Web application**
6. Set a name: `Prompt Management App - Supabase`
7. Under **Authorized redirect URIs**, add the Supabase callback URL:

   ```
   https://<your-project-ref>.supabase.co/auth/v1/callback
   ```

   **Important:** Replace `<your-project-ref>` with your actual Supabase project reference ID.

   You can find this in your Supabase dashboard under:
   - **Settings** > **API** > **Project URL**
   - The format is: `https://xxxxxxxxxxxxx.supabase.co`

8. Click **Create**

9. **Save your credentials:**
   - Copy the **Client ID**
   - Copy the **Client Secret**
   - Store these securely (you'll need them in the next step)

---

## Supabase Dashboard Configuration

### Step 1: Access Authentication Settings

1. Log into your [Supabase Dashboard](https://app.supabase.com/)
2. Select your project
3. Navigate to **Authentication** > **Providers** in the left sidebar

### Step 2: Configure Google Provider

1. Find **Google** in the list of providers
2. Toggle the **Enabled** switch to ON
3. Enter the credentials from Google Cloud:
   - **Client ID (for OAuth)**: Paste the Client ID from Google Cloud
   - **Client Secret (for OAuth)**: Paste the Client Secret from Google Cloud
4. Configure additional settings (optional):
   - **Skip nonce checks**: Leave unchecked (recommended for security)
   - **Authorized Client IDs**: Leave empty unless using mobile OAuth
5. Click **Save**

### Step 3: Verify Callback URL

1. In the same **Authentication** > **Providers** page
2. Scroll to the top to find the **Redirect URLs** section
3. Confirm the callback URL matches what you entered in Google Cloud:
   ```
   https://<your-project-ref>.supabase.co/auth/v1/callback
   ```

---

## Environment Variables

### Local Development (.env file)

Add the following to your `.env` file (use the provided `.env.example` as a template):

```bash
# Supabase Configuration
SUPABASE_URL=https://<your-project-ref>.supabase.co
SUPABASE_ANON_KEY=your-anon-key-from-supabase-dashboard
SUPABASE_SERVICE_KEY=your-service-role-key-from-supabase-dashboard

# For Next.js (if applicable)
NEXT_PUBLIC_SUPABASE_URL=https://<your-project-ref>.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=your-anon-key-from-supabase-dashboard
```

**Where to find these values:**

1. **SUPABASE_URL**:
   - Supabase Dashboard > **Settings** > **API** > **Project URL**

2. **SUPABASE_ANON_KEY**:
   - Supabase Dashboard > **Settings** > **API** > **Project API keys** > **anon public**

3. **SUPABASE_SERVICE_KEY**:
   - Supabase Dashboard > **Settings** > **API** > **Project API keys** > **service_role**
   - ⚠️ **CRITICAL**: Never commit this key to version control!

### GitHub Secrets (for CI/CD)

Add these secrets to your GitHub repository:

1. Go to your GitHub repository
2. Navigate to **Settings** > **Secrets and variables** > **Actions**
3. Click **New repository secret**
4. Add each of the following:

| Secret Name            | Value                                    | Description                         |
| ---------------------- | ---------------------------------------- | ----------------------------------- |
| `SUPABASE_URL`         | `https://<your-project-ref>.supabase.co` | Your Supabase project URL           |
| `SUPABASE_ANON_KEY`    | `eyJ...`                                 | Supabase anonymous key (public)     |
| `SUPABASE_SERVICE_KEY` | `eyJ...`                                 | Supabase service role key (private) |

### Google Secret Manager (for Cloud Run)

The Terraform configuration automatically creates Secret Manager resources. You need to populate them:

```bash
# Set your GCP project
PROJECT_ID="your-gcp-project-id"

# Add Supabase URL
echo -n "https://<your-project-ref>.supabase.co" | \
  gcloud secrets versions add SUPABASE_URL --data-file=- --project=$PROJECT_ID

# Add Supabase Anon Key
echo -n "your-anon-key" | \
  gcloud secrets versions add SUPABASE_ANON_KEY --data-file=- --project=$PROJECT_ID

# Add Supabase Service Key
echo -n "your-service-role-key" | \
  gcloud secrets versions add SUPABASE_SERVICE_KEY --data-file=- --project=$PROJECT_ID
```

---

## Testing the OAuth Flow

### Frontend Implementation (Example)

If using the Supabase JavaScript client library:

```typescript
import { createClient } from '@supabase/supabase-js';

const supabaseUrl = import.meta.env.VITE_SUPABASE_URL;
const supabaseAnonKey = import.meta.env.VITE_SUPABASE_ANON_KEY;

const supabase = createClient(supabaseUrl, supabaseAnonKey);

// Sign in with Google
async function signInWithGoogle() {
  const { data, error } = await supabase.auth.signInWithOAuth({
    provider: 'google',
    options: {
      redirectTo: `${window.location.origin}/auth/callback`,
    },
  });

  if (error) {
    console.error('Error signing in:', error);
    return;
  }

  console.log('Sign in initiated:', data);
}
```

### Manual Testing Steps

1. Start your development server (Prompt Management App)
2. Navigate to the login page
3. Click the "Sign in with Google" button
4. You should be redirected to Google's consent screen
5. Select a Google account
6. Grant the requested permissions
7. You should be redirected back to your application
8. Verify you are logged in (check Supabase dashboard **Authentication** > **Users**)

### Verify in Supabase Dashboard

1. Go to **Authentication** > **Users**
2. You should see a new user entry with:
   - Provider: `google`
   - Email: Your Google email
   - User ID: Auto-generated UUID

---

## Troubleshooting

### Issue: "Redirect URI mismatch" error

**Solution:**

- Verify the redirect URI in Google Cloud Console matches exactly:
  ```
  https://<your-project-ref>.supabase.co/auth/v1/callback
  ```
- Ensure there are no trailing slashes or extra characters
- Wait a few minutes after updating Google Cloud Console (changes can take time to propagate)

### Issue: "Invalid client" error

**Solution:**

- Double-check that the Client ID and Client Secret in Supabase match those from Google Cloud
- Ensure the OAuth credentials in Google Cloud are of type "Web application"
- Verify the Google+ API is enabled in your Google Cloud project

### Issue: User not appearing in Supabase after authentication

**Solution:**

- Check the browser console for errors
- Verify your Supabase project is not in "Paused" state
- Check the Supabase logs: **Logs** > **Auth Logs**

### Issue: "Access blocked: This app's request is invalid"

**Solution:**

- Configure the OAuth consent screen in Google Cloud Console
- Add your email as a test user if using "External" user type in testing mode
- Ensure all required fields are filled in the consent screen configuration

### Issue: Environment variables not loading

**Solution:**

- Verify `.env` file exists in the project root
- Restart your development server after modifying `.env`
- For Next.js, ensure public variables are prefixed with `NEXT_PUBLIC_`
- For Vite, ensure variables are prefixed with `VITE_`

---

## Additional Resources

- [Supabase Auth with Google Documentation](https://supabase.com/docs/guides/auth/social-login/auth-google)
- [Google OAuth 2.0 Documentation](https://developers.google.com/identity/protocols/oauth2)
- [Supabase JavaScript Client Library](https://supabase.com/docs/reference/javascript/auth-signinwithoauth)

---

## Security Best Practices

1. ✅ **Never commit secrets to Git:**
   - Use `.env` files (ensure `.env` is in `.gitignore`)
   - Use environment variables for production

2. ✅ **Protect service role keys:**
   - The `SUPABASE_SERVICE_KEY` bypasses Row Level Security (RLS)
   - Only use it in server-side code, never in the browser

3. ✅ **Use HTTPS:**
   - Always use HTTPS in production
   - Supabase provides HTTPS by default

4. ✅ **Review OAuth scopes:**
   - Only request the minimum Google scopes needed
   - Default Supabase integration only requests basic profile info

5. ✅ **Enable Row Level Security:**
   - Configure RLS policies in Supabase for all tables
   - Use `auth.uid()` to filter data by authenticated user

---

## Next Steps

After completing this setup:

1. ✅ Test the authentication flow in development
2. ✅ Deploy to Cloud Run with Terraform
3. ✅ Configure production redirect URIs in Google Cloud
4. ✅ Implement user profile management in your app
5. ✅ Set up Row Level Security policies in Supabase

For deployment instructions, see [Cloud Run Deployment Guide](./GCP_SETUP_GUIDE.md).
