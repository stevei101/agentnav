# Get current GCP project information
data "google_project" "current" {
  project_id = var.project_id
}

# Get default service account for Cloud Run
data "google_compute_default_service_account" "default" {
  project = var.project_id
}

# Check if APIs are enabled (dependency for other resources)
# Note: Resources will depend on google_project_service.apis implicitly

# Project data for Cloud Build (separate from current to avoid conflicts)
data "google_project" "project" {
  project_id = var.project_id
}

