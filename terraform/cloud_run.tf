# Cloud Run Services
# These are blueprints - actual container images are deployed via CI/CD

# Frontend Cloud Run Service
resource "google_cloud_run_v2_service" "frontend" {
  name     = "agentnav-frontend"
  location = var.frontend_region
  project  = var.project_id

  depends_on = [google_project_service.apis]

  template {
    service_account = google_service_account.cloud_run_frontend.email

    scaling {
      min_instance_count = 0
      max_instance_count = 10
    }

    containers {
      name  = "frontend"
      image = "${var.artifact_registry_location}-docker.pkg.dev/${var.project_id}/${var.artifact_registry_repository_id}/agentnav-frontend:latest" # Placeholder - updated by CI/CD

      ports {
        container_port = var.frontend_container_port
      }

      resources {
        limits = {
          cpu    = "1"
          memory = "512Mi"
        }
      }
    }

    timeout = "300s"
  }

  traffic {
    percent = 100
    type    = "TRAFFIC_TARGET_ALLOCATION_TYPE_LATEST"
  }
}

# Allow unauthenticated access to frontend
resource "google_cloud_run_service_iam_member" "frontend_public" {
  location = google_cloud_run_v2_service.frontend.location
  project  = google_cloud_run_v2_service.frontend.project
  service  = google_cloud_run_v2_service.frontend.name
  role     = "roles/run.invoker"
  member   = "allUsers"
}

# Backend Cloud Run Service
resource "google_cloud_run_v2_service" "backend" {
  name     = "agentnav-backend"
  location = var.backend_region
  project  = var.project_id

  depends_on = [google_project_service.apis]

  template {
    service_account = google_service_account.cloud_run_backend.email

    scaling {
      min_instance_count = 0
      max_instance_count = 10
    }

    containers {
      name  = "backend"
      image = "${var.artifact_registry_location}-docker.pkg.dev/${var.project_id}/${var.artifact_registry_repository_id}/agentnav-backend:latest" # Placeholder - updated by CI/CD

      ports {
        container_port = var.backend_container_port
      }

      env {
        name = "GEMINI_API_KEY"
        value_source {
          secret_key_ref {
            secret  = google_secret_manager_secret.gemini_api_key.secret_id
            version = "latest"
          }
        }
      }

      env {
        name  = "GEMMA_SERVICE_URL"
        value = google_cloud_run_v2_service.gemma.uri
      }

      env {
        name  = "FIRESTORE_PROJECT_ID"
        value = var.project_id
      }

      env {
        name  = "FIRESTORE_DATABASE_ID"
        value = var.firestore_database_id
      }

      env {
        name  = "ENVIRONMENT"
        value = var.environment
      }

      env {
        name  = "A2A_PROTOCOL_ENABLED"
        value = "true"
      }

      resources {
        limits = {
          cpu    = "4"
          memory = "8Gi"
        }
      }
    }

    timeout = "300s"
  }

  traffic {
    percent = 100
    type    = "TRAFFIC_TARGET_ALLOCATION_TYPE_LATEST"
  }
}

# Allow unauthenticated access to backend (or configure auth as needed)
resource "google_cloud_run_service_iam_member" "backend_public" {
  location = google_cloud_run_v2_service.backend.location
  project  = google_cloud_run_v2_service.backend.project
  service  = google_cloud_run_v2_service.backend.name
  role     = "roles/run.invoker"
  member   = "allUsers"
}

# Gemma GPU Cloud Run Service
resource "google_cloud_run_v2_service" "gemma" {
  name     = "gemma-service"
  location = var.gemma_region
  project  = var.project_id

  depends_on = [google_project_service.apis]

  template {
    service_account = google_service_account.cloud_run_gemma.email

    scaling {
      min_instance_count = 0
      max_instance_count = 2 # GPU instances are expensive
    }

    containers {
      name  = "gemma"
      image = "${var.gemma_region}-docker.pkg.dev/${var.project_id}/${var.artifact_registry_repository_id}/gemma-service:latest" # Placeholder

      ports {
        container_port = var.gemma_container_port
      }

      env {
        name  = "MODEL_NAME"
        value = "google/gemma-7b-it"
      }

      env {
        name = "HUGGINGFACE_TOKEN"
        value_source {
          secret_key_ref {
            secret  = google_secret_manager_secret.huggingface_token.secret_id
            version = "latest"
          }
        }
      }

      env {
        name  = "USE_8BIT_QUANTIZATION"
        value = "false"
      }

      # GPU Configuration
      resources {
        limits = {
          cpu    = "4"
          memory = "16Gi"
        }
        cpu_idle = false
      }
    }

    timeout = "300s"
  }

  traffic {
    percent = 100
    type    = "TRAFFIC_TARGET_ALLOCATION_TYPE_LATEST"
  }

  # Note: GPU configuration (gpu_type, gpu_count) must be set via gcloud CLI
  # as Terraform google provider doesn't fully support GPU in Cloud Run v2 yet
  # The deployment script should include: --gpu-type=nvidia-l4 --gpu-count=1
}

# GPU annotation for Gemma service (using annotation since Terraform doesn't support GPU directly)
# This requires gcloud CLI to set GPU after creation
resource "google_cloud_run_service_iam_member" "gemma_public" {
  location = google_cloud_run_v2_service.gemma.location
  project  = google_cloud_run_v2_service.gemma.project
  service  = google_cloud_run_v2_service.gemma.name
  role     = "roles/run.invoker"
  member   = "allUsers"
}

# ============================================
# STAGING ENVIRONMENT CLOUD RUN SERVICES
# ============================================

# Staging Frontend Cloud Run Service
resource "google_cloud_run_v2_service" "frontend_staging" {
  count    = var.enable_staging_environment ? 1 : 0
  name     = "agentnav-frontend-staging"
  location = var.frontend_region
  project  = var.project_id

  depends_on = [google_project_service.apis]

  template {
    service_account = google_service_account.cloud_run_frontend.email

    scaling {
      min_instance_count = 0
      max_instance_count = 5 # Lower limit for staging
    }

    containers {
      name  = "frontend"
      image = "${var.artifact_registry_location}-docker.pkg.dev/${var.project_id}/${var.artifact_registry_repository_id}/agentnav-frontend:latest" # Placeholder - CI/CD deploys with pr-{number} tags during PR testing

      ports {
        container_port = var.frontend_container_port
      }

      resources {
        limits = {
          cpu    = "1"
          memory = "512Mi"
        }
      }
    }

    timeout = "300s"
  }

  traffic {
    percent = 100
    type    = "TRAFFIC_TARGET_ALLOCATION_TYPE_LATEST"
  }
}

# Allow unauthenticated access to staging frontend
resource "google_cloud_run_service_iam_member" "frontend_staging_public" {
  count    = var.enable_staging_environment ? 1 : 0
  location = google_cloud_run_v2_service.frontend_staging[0].location
  project  = google_cloud_run_v2_service.frontend_staging[0].project
  service  = google_cloud_run_v2_service.frontend_staging[0].name
  role     = "roles/run.invoker"
  member   = "allUsers"
}

# Staging Backend Cloud Run Service
resource "google_cloud_run_v2_service" "backend_staging" {
  count    = var.enable_staging_environment ? 1 : 0
  name     = "agentnav-backend-staging"
  location = var.backend_region
  project  = var.project_id

  depends_on = [google_project_service.apis]

  template {
    service_account = google_service_account.cloud_run_backend.email

    scaling {
      min_instance_count = 0
      max_instance_count = 5 # Lower limit for staging
    }

    containers {
      name  = "backend"
      image = "${var.artifact_registry_location}-docker.pkg.dev/${var.project_id}/${var.artifact_registry_repository_id}/agentnav-backend:latest" # Placeholder - CI/CD deploys with pr-{number} tags during PR testing

      ports {
        container_port = var.backend_container_port
      }

      env {
        name = "GEMINI_API_KEY"
        value_source {
          secret_key_ref {
            secret  = google_secret_manager_secret.gemini_api_key.secret_id
            version = "latest"
          }
        }
      }

      env {
        name  = "GEMMA_SERVICE_URL"
        value = google_cloud_run_v2_service.gemma.uri
      }

      env {
        name  = "FIRESTORE_PROJECT_ID"
        value = var.project_id
      }

      env {
        name  = "FIRESTORE_DATABASE_ID"
        value = var.firestore_database_id
      }

      env {
        name  = "ENVIRONMENT"
        value = "staging"
      }

      env {
        name  = "A2A_PROTOCOL_ENABLED"
        value = "true"
      }

      resources {
        limits = {
          cpu    = "4"
          memory = "8Gi"
        }
      }
    }

    timeout = "300s"
  }

  traffic {
    percent = 100
    type    = "TRAFFIC_TARGET_ALLOCATION_TYPE_LATEST"
  }
}

# Allow unauthenticated access to staging backend
resource "google_cloud_run_service_iam_member" "backend_staging_public" {
  count    = var.enable_staging_environment ? 1 : 0
  location = google_cloud_run_v2_service.backend_staging[0].location
  project  = google_cloud_run_v2_service.backend_staging[0].project
  service  = google_cloud_run_v2_service.backend_staging[0].name
  role     = "roles/run.invoker"
  member   = "allUsers"
}

