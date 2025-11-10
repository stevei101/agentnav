# Secret Manager Secrets
# Placeholders for sensitive keys - actual values should be added manually
# or via gcloud/Terraform after creation

# Gemini API Key
resource "google_secret_manager_secret" "gemini_api_key" {
  secret_id = "GEMINI_API_KEY"
  project   = var.project_id

  replication {
    auto {
    }
  }

  labels = {
    service    = "backend"
    api_type   = "gemini"
    managed_by = "terraform"
  }

  depends_on = [google_project_service.apis]
}

# Firestore Credentials (optional - if not using WIF)
resource "google_secret_manager_secret" "firestore_credentials" {
  secret_id = "FIRESTORE_CREDENTIALS"
  project   = var.project_id

  replication {
    auto {
    }
  }

  labels = {
    service    = "backend"
    db_type    = "firestore"
    managed_by = "terraform"
  }

  depends_on = [google_project_service.apis]
}

# ==============================================================================
# Supabase Secrets (for Gen AI Prompt Management App)
# ==============================================================================

# Supabase Project URL
resource "google_secret_manager_secret" "supabase_url" {
  secret_id = "SUPABASE_URL"
  project   = var.project_id

  replication {
    auto {
    }
  }

  labels = {
    service    = "prompt-management-app"
    api_type   = "supabase"
    managed_by = "terraform"
  }

  depends_on = [google_project_service.apis]
}

# Supabase Anonymous Key (public key for client-side usage)
resource "google_secret_manager_secret" "supabase_anon_key" {
  secret_id = "SUPABASE_ANON_KEY"
  project   = var.project_id

  replication {
    auto {
    }
  }

  labels = {
    service    = "prompt-management-app"
    api_type   = "supabase"
    key_type   = "public"
    managed_by = "terraform"
  }

  depends_on = [google_project_service.apis]
}

# Supabase Service Role Key (private key for server-side usage)
resource "google_secret_manager_secret" "supabase_service_key" {
  secret_id = "SUPABASE_SERVICE_KEY"
  project   = var.project_id

  replication {
    auto {
    }
  }

  labels = {
    service    = "prompt-management-app"
    api_type   = "supabase"
    key_type   = "private"
    managed_by = "terraform"
  }

  depends_on = [google_project_service.apis]
}

# Grant Cloud Run services access to secrets
resource "google_secret_manager_secret_iam_member" "backend_gemini_key" {
  secret_id = google_secret_manager_secret.gemini_api_key.secret_id
  role      = "roles/secretmanager.secretAccessor"
  member    = "serviceAccount:${google_service_account.cloud_run_backend.email}"
}

# Grant Prompt Management App access to Supabase secrets
resource "google_secret_manager_secret_iam_member" "prompt_mgmt_supabase_url" {
  secret_id = google_secret_manager_secret.supabase_url.secret_id
  role      = "roles/secretmanager.secretAccessor"
  member    = "serviceAccount:${google_service_account.cloud_run_prompt_mgmt.email}"
}

resource "google_secret_manager_secret_iam_member" "prompt_mgmt_supabase_anon_key" {
  secret_id = google_secret_manager_secret.supabase_anon_key.secret_id
  role      = "roles/secretmanager.secretAccessor"
  member    = "serviceAccount:${google_service_account.cloud_run_prompt_mgmt.email}"
}

resource "google_secret_manager_secret_iam_member" "prompt_mgmt_supabase_service_key" {
  secret_id = google_secret_manager_secret.supabase_service_key.secret_id
  role      = "roles/secretmanager.secretAccessor"
  member    = "serviceAccount:${google_service_account.cloud_run_prompt_mgmt.email}"
}

# Note: Secret values should be added after creation via:
# echo -n "YOUR_SECRET_VALUE" | gcloud secrets versions add SECRET_NAME --data-file=-

