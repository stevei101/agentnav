# Service Accounts for Cloud Run services
# Dependencies: APIs must be enabled first
resource "google_service_account" "cloud_run_backend" {
  account_id   = "agentnav-backend"
  display_name = "Agentic Navigator Backend Service Account"
  description  = "Service account for backend Cloud Run service"
  project      = var.project_id

  depends_on = [google_project_service.apis]
}

resource "google_service_account" "cloud_run_frontend" {
  account_id   = "agentnav-frontend"
  display_name = "Agentic Navigator Frontend Service Account"
  description  = "Service account for frontend Cloud Run service"
  project      = var.project_id

  depends_on = [google_project_service.apis]
}

resource "google_service_account" "cloud_run_gemma" {
  account_id   = "agentnav-gemma"
  display_name = "Agentic Navigator Gemma GPU Service Account"
  description  = "Service account for Gemma GPU Cloud Run service"
  project      = var.project_id

  depends_on = [google_project_service.apis]
}

# Service account for GitHub Actions (Workload Identity Federation)
resource "google_service_account" "github_actions" {
  account_id   = "github-actions"
  display_name = "GitHub Actions Service Account"
  description  = "Service account for GitHub Actions CI/CD (via Workload Identity Federation)"
  project      = var.project_id

  depends_on = [google_project_service.apis]
}

# IAM roles for Cloud Run services
resource "google_project_iam_member" "backend_firestore_user" {
  project = var.project_id
  role    = "roles/datastore.user"
  member  = "serviceAccount:${google_service_account.cloud_run_backend.email}"
}

resource "google_project_iam_member" "backend_secret_accessor" {
  project = var.project_id
  role    = "roles/secretmanager.secretAccessor"
  member  = "serviceAccount:${google_service_account.cloud_run_backend.email}"
}

resource "google_project_iam_member" "backend_service_invoker" {
  project = var.project_id
  role    = "roles/run.invoker"
  member  = "serviceAccount:${google_service_account.cloud_run_backend.email}"
}

# Gemma service needs GPU access and secret access
resource "google_project_iam_member" "gemma_secret_accessor" {
  project = var.project_id
  role    = "roles/secretmanager.secretAccessor"
  member  = "serviceAccount:${google_service_account.cloud_run_gemma.email}"
}

# GitHub Actions service account permissions (for CI/CD)
resource "google_project_iam_member" "github_actions_artifact_writer" {
  project = var.project_id
  role    = "roles/artifactregistry.writer"
  member  = "serviceAccount:${google_service_account.github_actions.email}"
}

resource "google_project_iam_member" "github_actions_run_admin" {
  project = var.project_id
  role    = "roles/run.admin"
  member  = "serviceAccount:${google_service_account.github_actions.email}"
}

resource "google_project_iam_member" "github_actions_service_account_user" {
  project = var.project_id
  role    = "roles/iam.serviceAccountUser"
  member  = "serviceAccount:${google_service_account.github_actions.email}"
}

resource "google_project_iam_member" "github_actions_storage_admin" {
  project = var.project_id
  role    = "roles/storage.admin"
  member  = "serviceAccount:${google_service_account.github_actions.email}"
}

# Workload Identity Federation Setup
resource "google_iam_workload_identity_pool" "github_actions" {
  project                   = var.project_id
  workload_identity_pool_id = var.workload_identity_pool_id
  display_name              = "GitHub Actions Pool"
  description               = "Workload Identity Pool for GitHub Actions CI/CD"
  location                  = "global"
}

resource "google_iam_workload_identity_pool_provider" "github_actions" {
  project                            = var.project_id
  workload_identity_pool_id          = google_iam_workload_identity_pool.github_actions.workload_identity_pool_id
  workload_identity_pool_provider_id = var.workload_identity_provider_id
  display_name                       = "GitHub Provider"
  description                        = "OIDC provider for GitHub Actions"

  attribute_mapping = {
    "google.subject"       = "assertion.sub"
    "attribute.repository" = "assertion.repository"
    "attribute.actor"       = "assertion.actor"
    "attribute.ref"         = "assertion.ref"
  }

  oidc {
    issuer_uri = "https://token.actions.githubusercontent.com"
  }
}

# Bind GitHub Actions service account to WIF
resource "google_service_account_iam_member" "github_actions_workload_identity" {
  service_account_id = google_service_account.github_actions.name
  role               = "roles/iam.workloadIdentityUser"
  member             = "principalSet://iam.googleapis.com/${google_iam_workload_identity_pool.github_actions.name}/attribute.repository/${var.github_repository}"
}

