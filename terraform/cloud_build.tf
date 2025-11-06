# Cloud Build Triggers for "Connect Repo" Functionality
# Enables automatic deployments from GitHub to Cloud Run
# This simplifies CI/CD by using Cloud Build's native GitHub integration

# Frontend and Backend services use automatic deployments via Cloud Build triggers
# This enables CI/CD from GitHub to Cloud Run without manual intervention

# Cloud Build Service Account (default, used by Cloud Build)
# Grant necessary permissions
data "google_project" "project" {
  project_id = var.project_id
}

resource "google_project_iam_member" "cloudbuild_service_account_roles" {
  for_each = toset([
    "roles/run.admin",                    # Deploy to Cloud Run
    "roles/iam.serviceAccountUser",       # Use service accounts
    "roles/artifactregistry.writer",      # Push images to Artifact Registry
    "roles/secretmanager.secretAccessor", # Access secrets during build
  ])

  project = var.project_id
  role    = each.value
  member  = "serviceAccount:${data.google_project.project.number}@cloudbuild.gserviceaccount.com"

  depends_on = [google_project_service.apis]
}

# Frontend Cloud Build Trigger (automatic deployment)
resource "google_cloudbuild_trigger" "frontend" {
  count = var.enable_connect_repo ? 1 : 0

  name        = "agentnav-frontend-deploy"
  description = "Automatic deployment trigger for frontend service from GitHub"
  project     = var.project_id

  github {
    owner = split("/", var.github_repository)[0]
    name  = split("/", var.github_repository)[1]

    push {
      branch = "^${var.github_branch}$"
    }
  }

  # Build configuration
  filename = "cloudbuild-frontend.yaml"

  substitutions = {
    _SERVICE_NAME    = google_cloud_run_v2_service.frontend.name
    _REGION          = var.frontend_region
    _PROJECT_ID      = var.project_id
    _ARTIFACT_REGION = var.artifact_registry_location
    _GAR_REPO        = var.artifact_registry_repository_id
    _SERVICE_ACCOUNT = google_service_account.cloud_run_frontend.email
  }

  service_account = "projects/${var.project_id}/serviceAccounts/${data.google_project.project.number}@cloudbuild.gserviceaccount.com"

  depends_on = [
    google_project_service.apis,
    google_cloud_run_v2_service.frontend,
    google_artifact_registry_repository.main,
  ]
}

# Backend Cloud Build Trigger (automatic deployment)
resource "google_cloudbuild_trigger" "backend" {
  count = var.enable_connect_repo ? 1 : 0

  name        = "agentnav-backend-deploy"
  description = "Automatic deployment trigger for backend service from GitHub"
  project     = var.project_id

  github {
    owner = split("/", var.github_repository)[0]
    name  = split("/", var.github_repository)[1]

    push {
      branch = "^${var.github_branch}$"
    }
  }

  # Build configuration
  filename = "cloudbuild-backend.yaml"

  substitutions = {
    _SERVICE_NAME    = google_cloud_run_v2_service.backend.name
    _REGION          = var.backend_region
    _PROJECT_ID      = var.project_id
    _ARTIFACT_REGION = var.artifact_registry_location
    _GAR_REPO        = var.artifact_registry_repository_id
    _SERVICE_ACCOUNT = google_service_account.cloud_run_backend.email
  }

  service_account = "projects/${var.project_id}/serviceAccounts/${data.google_project.project.number}@cloudbuild.gserviceaccount.com"

  depends_on = [
    google_project_service.apis,
    google_cloud_run_v2_service.backend,
    google_artifact_registry_repository.main,
  ]
}

