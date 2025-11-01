# Google Artifact Registry Repository
# Stores all Podman-built container images
resource "google_artifact_registry_repository" "main" {
  location      = var.artifact_registry_location
  repository_id = var.artifact_registry_repository_id
  description   = "Artifact Registry for Agentic Navigator container images"
  format        = "DOCKER"

  labels = {
    environment = var.environment
    project     = "agentnav"
  }

  depends_on = [google_project_service.apis]
}

# IAM binding for GitHub Actions to push images
resource "google_artifact_registry_repository_iam_member" "github_actions_writer" {
  location   = google_artifact_registry_repository.main.location
  repository = google_artifact_registry_repository.main.name
  role       = "roles/artifactregistry.writer"
  member     = "serviceAccount:${local.github_actions_sa_email}"
}

