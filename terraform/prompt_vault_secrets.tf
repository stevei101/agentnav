# Prompt Vault Secrets in Secret Manager
# These secrets store Supabase and Google OAuth credentials

# Note: Terraform cannot create OAuth 2.0 Client IDs directly.
# You must create the OAuth credentials manually in Google Cloud Console
# and then store them in these secrets.
# See: docs/PROMPT_VAULT_GOOGLE_OAUTH_SETUP.md for instructions

# Supabase URL
# Note: This is NOT actually a secret - it's your public project URL
# But we store it in Secret Manager for consistency and easy rotation
# Format: https://{project-ref}.supabase.co
resource "google_secret_manager_secret" "supabase_url" {
  secret_id = "SUPABASE_URL"
  project   = var.project_id

  replication {
    auto {}
  }

  labels = {
    app         = "prompt-vault"
    environment = var.environment
    type        = "public-url"
  }
}

# Supabase Publishable Key (for frontend/client-side use)
# Found in: Supabase Dashboard → Settings → API → API Keys → "Publishable key"
# Format: sb_publishable_...
# This is safe to expose in frontend code if Row Level Security (RLS) is enabled
# Has Row Level Security (RLS) restrictions - respects database policies
# Note: Supabase renamed "anon/public" key to "Publishable key" - this is the same key
resource "google_secret_manager_secret" "supabase_anon_key" {
  secret_id = "SUPABASE_ANON_KEY"
  project   = var.project_id

  replication {
    auto {}
  }

  labels = {
    app         = "prompt-vault"
    environment = var.environment
    type        = "publishable-key"
    supabase_key_type = "publishable"
  }
}

# Supabase Secret Key (for backend/admin operations)
# Found in: Supabase Dashboard → Settings → API → API Keys → "Secret keys" → "New secret key"
# Format: sb_...
# ⚠️ HIGHLY SENSITIVE - Never expose in frontend code!
# Bypasses Row Level Security (RLS) - has full database access
# Only use for backend/admin operations that require elevated privileges
# If you're using Supabase Edge Functions exclusively, this may not be needed
# Note: Supabase renamed "service_role" key to "Secret keys" - this is the same concept
resource "google_secret_manager_secret" "supabase_service_key" {
  secret_id = "SUPABASE_SERVICE_KEY"
  project   = var.project_id

  replication {
    auto {}
  }

  labels = {
    app         = "prompt-vault"
    environment = var.environment
    type        = "secret-key"
    supabase_key_type = "secret"
  }
}

# Google OAuth Client ID (for Supabase Google Sign-in)
resource "google_secret_manager_secret" "google_oauth_client_id" {
  secret_id = "GOOGLE_OAUTH_CLIENT_ID"
  project   = var.project_id

  replication {
    auto {}
  }

  labels = {
    app         = "prompt-vault"
    environment = var.environment
    purpose     = "supabase-google-signin"
  }
}

# Google OAuth Client Secret (for Supabase Google Sign-in)
resource "google_secret_manager_secret" "google_oauth_client_secret" {
  secret_id = "GOOGLE_OAUTH_CLIENT_SECRET"
  project   = var.project_id

  replication {
    auto {}
  }

  labels = {
    app         = "prompt-vault"
    environment = var.environment
    purpose     = "supabase-google-signin"
  }
}

# IAM: Grant service accounts access to secrets
# Frontend needs: SUPABASE_URL, SUPABASE_ANON_KEY, GOOGLE_OAUTH_CLIENT_ID
resource "google_secret_manager_secret_iam_member" "prompt_vault_frontend_supabase_url" {
  secret_id = google_secret_manager_secret.supabase_url.secret_id
  role      = "roles/secretmanager.secretAccessor"
  member    = "serviceAccount:${google_service_account.prompt_vault_frontend.email}"
}

resource "google_secret_manager_secret_iam_member" "prompt_vault_frontend_supabase_anon_key" {
  secret_id = google_secret_manager_secret.supabase_anon_key.secret_id
  role      = "roles/secretmanager.secretAccessor"
  member    = "serviceAccount:${google_service_account.prompt_vault_frontend.email}"
}

resource "google_secret_manager_secret_iam_member" "prompt_vault_frontend_google_oauth_client_id" {
  secret_id = google_secret_manager_secret.google_oauth_client_id.secret_id
  role      = "roles/secretmanager.secretAccessor"
  member    = "serviceAccount:${google_service_account.prompt_vault_frontend.email}"
}

# Backend needs: SUPABASE_URL, SUPABASE_SERVICE_KEY
resource "google_secret_manager_secret_iam_member" "prompt_vault_backend_supabase_url" {
  secret_id = google_secret_manager_secret.supabase_url.secret_id
  role      = "roles/secretmanager.secretAccessor"
  member    = "serviceAccount:${google_service_account.prompt_vault_backend.email}"
}

resource "google_secret_manager_secret_iam_member" "prompt_vault_backend_supabase_service_key" {
  secret_id = google_secret_manager_secret.supabase_service_key.secret_id
  role      = "roles/secretmanager.secretAccessor"
  member    = "serviceAccount:${google_service_account.prompt_vault_backend.email}"
}

# Outputs for reference (not exposing secret values)
output "prompt_vault_secrets_created" {
  description = "List of Secret Manager secrets created for Prompt Vault"
  value = [
    google_secret_manager_secret.supabase_url.secret_id,
    google_secret_manager_secret.supabase_anon_key.secret_id,
    google_secret_manager_secret.supabase_service_key.secret_id,
    google_secret_manager_secret.google_oauth_client_id.secret_id,
    google_secret_manager_secret.google_oauth_client_secret.secret_id,
  ]
}

