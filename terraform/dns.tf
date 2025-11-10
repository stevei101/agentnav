# Cloud DNS and Cloud Run Domain Mapping Configuration
# Manages custom domain (agentnav.lornu.com) for Cloud Run frontend service
#
# NOTE: Cloud Run automatically manages TLS/SSL certificates - no cert-manager needed!
# This configuration creates:
# 1. Cloud Run Domain Mapping (provides target DNS records)
# 2. Cloud DNS A/CNAME records (points domain to Cloud Run)

# Read DNS Zone Project ID from Secret Manager
data "google_secret_manager_secret_version" "dns_zone_project_id" {
  secret  = google_secret_manager_secret.dns_zone_project_id.secret_id
  project = var.project_id
}

# Cloud DNS Zone for lornu.com domain
# NOTE: The DNS zone is managed in the infrastructure repository (github.com/stevei101/infrastructure).
# This data source references the zone which may be in a different project.
# Cross-project access requires appropriate IAM permissions.
data "google_dns_managed_zone" "lornu_zone" {
  name    = var.dns_zone_name
  project = data.google_secret_manager_secret_version.dns_zone_project_id.secret_data

  # Ensure DNS API is enabled before attempting to read the zone
  depends_on = [google_project_service.apis]
}

# Cloud Run Domain Mapping for agentnav.lornu.com
# This resource creates the domain mapping and provides target DNS records
# in its status.resource_records output
resource "google_cloud_run_domain_mapping" "frontend_custom_domain" {
  location = var.frontend_region
  name     = var.custom_domain_name
  project  = var.project_id

  metadata {
    namespace = var.project_id
  }

  spec {
    route_name = google_cloud_run_v2_service.frontend.name
  }

  depends_on = [
    google_cloud_run_v2_service.frontend,
    google_project_service.apis,
  ]
}

# Cloud DNS A Records for agentnav.lornu.com
# Cloud Run provides these IP addresses in the domain mapping status
# We extract A records from the domain mapping status
# NOTE: Only create these records if manage_dns_in_this_project is true
resource "google_dns_record_set" "frontend_domain_a" {
  # DNS record names must include trailing dot for Cloud DNS
  name         = "${var.custom_domain_name}."
  managed_zone = data.google_dns_managed_zone.lornu_zone.name
  type         = "A"
  ttl          = 300
  project      = data.google_secret_manager_secret_version.dns_zone_project_id.secret_data

  # Extract A record IPs from Cloud Run domain mapping status
  # The status.resource_records contains the target DNS records provided by Cloud Run
  # Use count to only create this resource when A records are available AND we manage DNS in this project
  count = var.manage_dns_in_this_project && try(
    length([
      for record in google_cloud_run_domain_mapping.frontend_custom_domain.status[0].resource_records :
      record.rrdata if record.type == "A"
    ]) > 0,
    false
  ) ? 1 : 0

  rrdatas = [
    for record in google_cloud_run_domain_mapping.frontend_custom_domain.status[0].resource_records :
    record.rrdata if record.type == "A"
  ]

  depends_on = [google_cloud_run_domain_mapping.frontend_custom_domain]
}

# Cloud DNS CNAME Record for agentnav.lornu.com (if Cloud Run provides one)
# Some Cloud Run configurations use CNAME instead of or in addition to A records
# NOTE: Only create these records if manage_dns_in_this_project is true
resource "google_dns_record_set" "frontend_domain_cname" {
  count = var.manage_dns_in_this_project && try(
    length([
      for record in google_cloud_run_domain_mapping.frontend_custom_domain.status[0].resource_records :
      record.rrdata if record.type == "CNAME"
    ]) > 0,
    false
  ) ? 1 : 0

  # DNS record names must include trailing dot for Cloud DNS
  name         = "${var.custom_domain_name}."
  managed_zone = data.google_dns_managed_zone.lornu_zone.name
  type         = "CNAME"
  ttl          = 300
  project      = data.google_secret_manager_secret_version.dns_zone_project_id.secret_data

  rrdatas = [
    for record in google_cloud_run_domain_mapping.frontend_custom_domain.status[0].resource_records :
    record.rrdata if record.type == "CNAME"
  ]

  depends_on = [google_cloud_run_domain_mapping.frontend_custom_domain]
}
