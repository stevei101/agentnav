# Prompt Vault Cloud Run Services
# Separate Terraform file for complete isolation from agentnav services
# All resources use "prompt-vault-" prefix to avoid conflicts

# Service Accounts for Prompt Vault Cloud Run services
resource "google_service_account" "prompt_vault_frontend" {
  account_id   = "prompt-vault-frontend"
  display_name = "Prompt Vault Frontend Service Account"
  description  = "Service account for Prompt Vault frontend Cloud Run service"
  project      = var.project_id

  depends_on = [google_project_service.apis]
}

resource "google_service_account" "prompt_vault_backend" {
  account_id   = "prompt-vault-backend"
  display_name = "Prompt Vault Backend Service Account"
  description  = "Service account for Prompt Vault backend Cloud Run service"
  project      = var.project_id

  depends_on = [google_project_service.apis]
}

# Prompt Vault Frontend Cloud Run Service
resource "google_cloud_run_v2_service" "prompt_vault_frontend" {
  name     = "prompt-vault-frontend"
  location = var.frontend_region  # Use same region as agentnav-frontend (us-central1)
  project  = var.project_id

  depends_on = [google_project_service.apis]

  template {
    service_account = google_service_account.prompt_vault_frontend.email

    scaling {
      min_instance_count = 0
      max_instance_count = 10
    }

    containers {
      name  = "frontend"
      image = "${var.artifact_registry_location}-docker.pkg.dev/${var.project_id}/${var.artifact_registry_repository_id}/prompt-vault-frontend:latest" # Placeholder - updated by CI/CD

      ports {
        container_port = var.frontend_container_port  # Port 80
      }

      env {
        name  = "PORT"
        value = tostring(var.frontend_container_port)
      }

      # Supabase environment variables (from Secret Manager)
      env {
        name = "SUPABASE_URL"
        value_source {
          secret_key_ref {
            secret  = "SUPABASE_URL"
            version = "latest"
          }
        }
      }

      env {
        name = "SUPABASE_ANON_KEY"
        value_source {
          secret_key_ref {
            secret  = "SUPABASE_ANON_KEY"
            version = "latest"
          }
        }
      }

      # Google OAuth for Supabase Sign-in
      env {
        name = "NEXT_PUBLIC_GOOGLE_CLIENT_ID"
        value_source {
          secret_key_ref {
            secret  = "GOOGLE_OAUTH_CLIENT_ID"
            version = "latest"
          }
        }
      }

      resources {
        limits = {
          cpu    = "1"
          memory = "512Mi"
        }
      }

      startup_probe {
        timeout_seconds   = 10
        period_seconds    = 10
        failure_threshold = 24  # 240s total startup window
        tcp_socket {
          port = var.frontend_container_port
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

# Allow unauthenticated access to Prompt Vault frontend
resource "google_cloud_run_service_iam_member" "prompt_vault_frontend_public" {
  location = google_cloud_run_v2_service.prompt_vault_frontend.location
  project  = google_cloud_run_v2_service.prompt_vault_frontend.project
  service  = google_cloud_run_v2_service.prompt_vault_frontend.name
  role     = "roles/run.invoker"
  member   = "allUsers"
}

# Prompt Vault Backend Cloud Run Service (if needed for Supabase Edge Functions alternative)
# Note: If using Supabase Edge Functions exclusively, this may not be needed
resource "google_cloud_run_v2_service" "prompt_vault_backend" {
  name     = "prompt-vault-backend"
  location = var.backend_region  # Use same region as agentnav-backend (europe-west1)
  project  = var.project_id

  depends_on = [google_project_service.apis]

  template {
    service_account = google_service_account.prompt_vault_backend.email

    scaling {
      min_instance_count = 0
      max_instance_count = 10
    }

    containers {
      name  = "backend"
      image = "${var.artifact_registry_location}-docker.pkg.dev/${var.project_id}/${var.artifact_registry_repository_id}/prompt-vault-backend:latest" # Placeholder - updated by CI/CD

      ports {
        container_port = var.backend_container_port  # Port 8080
      }

      env {
        name  = "PORT"
        value = tostring(var.backend_container_port)
      }

      # Supabase environment variables (from Secret Manager)
      env {
        name = "SUPABASE_URL"
        value_source {
          secret_key_ref {
            secret  = "SUPABASE_URL"
            version = "latest"
          }
        }
      }

      env {
        name = "SUPABASE_SERVICE_KEY"
        value_source {
          secret_key_ref {
            secret  = "SUPABASE_SERVICE_KEY"
            version = "latest"
          }
        }
      }

      resources {
        limits = {
          cpu    = "2"
          memory = "1Gi"
        }
      }

      startup_probe {
        timeout_seconds   = 10
        period_seconds    = 10
        failure_threshold = 24
        tcp_socket {
          port = var.backend_container_port
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

# Allow unauthenticated access to Prompt Vault backend (if needed)
# Note: May want to restrict this if backend handles sensitive operations
resource "google_cloud_run_service_iam_member" "prompt_vault_backend_public" {
  location = google_cloud_run_v2_service.prompt_vault_backend.location
  project  = google_cloud_run_v2_service.prompt_vault_backend.project
  service  = google_cloud_run_v2_service.prompt_vault_backend.name
  role     = "roles/run.invoker"
  member   = "allUsers"
}

# IAM roles for Prompt Vault service accounts
# Note: Prompt Vault uses Supabase, not Firestore, so no datastore.user role needed
resource "google_project_iam_member" "prompt_vault_frontend_secret_accessor" {
  project = var.project_id
  role    = "roles/secretmanager.secretAccessor"
  member  = "serviceAccount:${google_service_account.prompt_vault_frontend.email}"
}

resource "google_project_iam_member" "prompt_vault_backend_secret_accessor" {
  project = var.project_id
  role    = "roles/secretmanager.secretAccessor"
  member  = "serviceAccount:${google_service_account.prompt_vault_backend.email}"
}

