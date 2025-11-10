# Workload Identity Federation Outputs (for GitHub Secrets)
# TODO: Uncomment when WIF resources are imported into Terraform state
# output "wif_provider" {
#   description = "Workload Identity Federation Provider resource name"
#   value       = google_iam_workload_identity_pool_provider.github_actions.name
#   sensitive   = false
# }

output "wif_service_account_email" {
  description = "Service account email used by Workload Identity Federation"
  value       = local.github_actions_sa_email
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

# Staging Environment Outputs
output "frontend_staging_service_url" {
  description = "Staging Frontend Cloud Run service URL"
  value       = var.enable_staging_environment ? google_cloud_run_v2_service.frontend_staging[0].uri : null
}

output "backend_staging_service_url" {
  description = "Staging Backend Cloud Run service URL"
  value       = var.enable_staging_environment ? google_cloud_run_v2_service.backend_staging[0].uri : null
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
    firestore_credentials = google_secret_manager_secret.firestore_credentials.secret_id
    supabase_url          = google_secret_manager_secret.supabase_url.secret_id
    supabase_anon_key     = google_secret_manager_secret.supabase_anon_key.secret_id
    supabase_service_key  = google_secret_manager_secret.supabase_service_key.secret_id
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

# Custom Domain Outputs
output "custom_domain_url" {
  description = "Custom domain URL for frontend service"
  value       = "https://${var.custom_domain_name}"
  depends_on  = [google_cloud_run_domain_mapping.frontend_custom_domain]
}

output "domain_mapping_status" {
  description = "Status of Cloud Run domain mapping"
  value       = google_cloud_run_domain_mapping.frontend_custom_domain.status
  sensitive   = false
}

# DNS Records for Manual Creation (Cross-Project Setup)
output "dns_records_for_manual_creation" {
  description = "DNS records that need to be created manually in the infrastructure repository when manage_dns_in_this_project=false"
  sensitive   = true # Contains sensitive data from Secret Manager
  value = var.manage_dns_in_this_project ? null : {
    domain_name  = var.custom_domain_name
    zone_name    = var.dns_zone_name
    zone_project = data.google_secret_manager_secret_version.dns_zone_project_id.secret_data
    last_updated = timestamp() # Track when these IPs were last retrieved

    # Group records by type for easier navigation and creation
    records_by_type = try(
      {
        A = [
          for record in google_cloud_run_domain_mapping.frontend_custom_domain.status[0].resource_records :
          {
            name    = "${var.custom_domain_name}."
            type    = record.type
            ttl     = 300
            rrdatas = [record.rrdata]
          }
          if record.type == "A"
        ]
        AAAA = [
          for record in google_cloud_run_domain_mapping.frontend_custom_domain.status[0].resource_records :
          {
            name    = "${var.custom_domain_name}."
            type    = record.type
            ttl     = 300
            rrdatas = [record.rrdata]
          }
          if record.type == "AAAA"
        ]
      },
      {
        A    = []
        AAAA = []
      }
    )
  }
}

# Current Cloud Run Domain Mapping IP Addresses (for monitoring)
output "current_cloud_run_ips" {
  description = "Current IP addresses assigned by Cloud Run (monitor for changes)"
  value = try(
    {
      a_records = [
        for record in google_cloud_run_domain_mapping.frontend_custom_domain.status[0].resource_records :
        record.rrdata if record.type == "A"
      ]
      aaaa_records = [
        for record in google_cloud_run_domain_mapping.frontend_custom_domain.status[0].resource_records :
        record.rrdata if record.type == "AAAA"
      ]
      last_checked = timestamp()
    },
    {
      a_records    = []
      aaaa_records = []
      last_checked = timestamp()
    }
  )
}
