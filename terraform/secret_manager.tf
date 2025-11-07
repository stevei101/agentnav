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

# Grant Cloud Run services access to secrets
resource "google_secret_manager_secret_iam_member" "backend_gemini_key" {
  secret_id = google_secret_manager_secret.gemini_api_key.secret_id
  role      = "roles/secretmanager.secretAccessor"
  member    = "serviceAccount:${google_service_account.cloud_run_backend.email}"
}

# Note: Secret values should be added after creation via:
# echo -n "YOUR_SECRET_VALUE" | gcloud secrets versions add SECRET_NAME --data-file=-

