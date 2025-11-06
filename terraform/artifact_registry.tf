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

# Dedicated Artifact Registry for Prompt Vault (us-central1)
resource "google_artifact_registry_repository" "prompt_vault" {
  location      = var.prompt_vault_artifact_registry_location
  repository_id = var.prompt_vault_artifact_registry_repository_id
  description   = "Artifact Registry for Prompt Vault container images"
  format        = "DOCKER"

  labels = {
    environment = var.environment
    project     = "prompt-vault"
  }

  depends_on = [google_project_service.apis]
}

resource "google_artifact_registry_repository_iam_member" "prompt_vault_github_actions_writer" {
  location   = google_artifact_registry_repository.prompt_vault.location
  repository = google_artifact_registry_repository.prompt_vault.name
  role       = "roles/artifactregistry.writer"
  member     = "serviceAccount:${local.github_actions_sa_email}"
}

