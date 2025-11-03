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

# Hugging Face Token (optional - for private Gemma models)
resource "google_secret_manager_secret" "huggingface_token" {
  secret_id = "HUGGINGFACE_TOKEN"
  project   = var.project_id

  replication {
    auto {
    }
  }

  labels = {
    service    = "gemma"
    api_type   = "huggingface"
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

resource "google_secret_manager_secret_iam_member" "gemma_huggingface_token" {
  secret_id = google_secret_manager_secret.huggingface_token.secret_id
  role      = "roles/secretmanager.secretAccessor"
  member    = "serviceAccount:${google_service_account.cloud_run_gemma.email}"
}

# Optional: Add secret versions via Terraform
# WARNING: Secret values in Terraform state are visible to anyone with state access
# For production, consider using gcloud CLI or GitHub Actions workflow instead
# 
# To use Terraform for secret values:
# 1. Add variables to terraform.tfvars (never commit this file!)
# 2. Uncomment the google_secret_manager_secret_version resources below
# 3. Run: terraform apply

# resource "google_secret_manager_secret_version" "gemini_api_key_version" {
#   count       = var.gemini_api_key != "" ? 1 : 0
#   secret      = google_secret_manager_secret.gemini_api_key.id
#   secret_data = var.gemini_api_key
# 
#   lifecycle {
#     create_before_destroy = true
#   }
# }
# 
# resource "google_secret_manager_secret_version" "huggingface_token_version" {
#   count       = var.huggingface_token != "" ? 1 : 0
#   secret      = google_secret_manager_secret.huggingface_token.id
#   secret_data = var.huggingface_token
# 
#   lifecycle {
#     create_before_destroy = true
#   }
# }

# Note: For manual secret management (recommended for security):
# echo -n "YOUR_SECRET_VALUE" | gcloud secrets versions add SECRET_NAME --data-file=-

