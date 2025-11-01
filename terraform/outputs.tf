# Workload Identity Federation Outputs (for GitHub Secrets)
output "wif_provider" {
  description = "Workload Identity Federation Provider resource name"
  value       = google_iam_workload_identity_pool_provider.github_actions.name
  sensitive   = false
}

output "wif_service_account_email" {
  description = "Service account email used by Workload Identity Federation"
  value       = google_service_account.github_actions.email
  sensitive   = false
}

# Artifact Registry Outputs
output "artifact_registry_repository" {
  description = "Artifact Registry repository name"
  value       = google_artifact_registry_repository.main.name
}

output "artifact_registry_url" {
  description = "Artifact Registry repository URL"
  value       = "${google_artifact_registry_repository.main.location}-docker.pkg.dev/${var.project_id}/${google_artifact_registry_repository.main.repository_id}"
  sensitive   = true
}

# Cloud Run Service URLs
output "frontend_service_url" {
  description = "Frontend Cloud Run service URL"
  value       = google_cloud_run_v2_service.frontend.uri
}

output "backend_service_url" {
  description = "Backend Cloud Run service URL"
  value       = google_cloud_run_v2_service.backend.uri
}

output "gemma_service_url" {
  description = "Gemma GPU Cloud Run service URL"
  value       = google_cloud_run_v2_service.gemma.uri
}

# Firestore Outputs
output "firestore_database_id" {
  description = "Firestore database ID"
  value       = google_firestore_database.main.name
}

# Secret Manager Outputs
output "secrets" {
  description = "Secret Manager secret names (for reference)"
  value = {
    gemini_api_key        = google_secret_manager_secret.gemini_api_key.secret_id
    huggingface_token     = google_secret_manager_secret.huggingface_token.secret_id
    firestore_credentials = google_secret_manager_secret.firestore_credentials.secret_id
  }
}

# Project Information
output "project_id" {
  description = "GCP Project ID"
  value       = var.project_id
  sensitive   = true
}

output "project_number" {
  description = "GCP Project Number"
  value       = data.google_project.current.number
}

# Cloud Build Triggers (Connect Repo)
output "cloud_build_triggers" {
  description = "Cloud Build trigger names for Connect Repo"
  value = {
    frontend = var.enable_connect_repo && length(google_cloudbuild_trigger.frontend) > 0 ? google_cloudbuild_trigger.frontend[0].name : null
    backend  = var.enable_connect_repo && length(google_cloudbuild_trigger.backend) > 0 ? google_cloudbuild_trigger.backend[0].name : null
  }
}

