# Get current GCP project information
data "google_project" "current" {
  project_id = var.project_id
}

# Get default service account for Cloud Run
data "google_compute_default_service_account" "default" {
  project = var.project_id
}

# Note: data "google_project" "project" is defined in cloud_build.tf to avoid duplication

