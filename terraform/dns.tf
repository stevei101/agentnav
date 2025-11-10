# Cloud DNS and Cloud Run Domain Mapping Configuration
# Manages custom domain (agentnav.lornu.com) for Cloud Run frontend service
#
# NOTE: Cloud Run automatically manages TLS/SSL certificates - no cert-manager needed!
# This configuration creates:
# 1. Cloud Run Domain Mapping (provides target DNS records)
# 2. Cloud DNS A/CNAME records (points domain to Cloud Run)

# Cloud DNS Zone for lornu.com domain
# NOTE: The DNS zone must already exist in GCP Cloud DNS.
# If it doesn't exist, create it manually first:
#   gcloud dns managed-zones create lornu-com --dns-name=lornu.com --description="lornu.com DNS zone"
# Or import it into Terraform state if it was created outside of Terraform.
data "google_dns_managed_zone" "lornu_zone" {
  name    = var.dns_zone_name
  project = var.project_id

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
resource "google_dns_record_set" "frontend_domain_a" {
  # DNS record names must include trailing dot for Cloud DNS
  name         = "${var.custom_domain_name}."
  managed_zone = data.google_dns_managed_zone.lornu_zone.name
  type         = "A"
  ttl          = 300
  project      = var.project_id

  # Extract A record IPs from Cloud Run domain mapping status
  # The status.resource_records contains the target DNS records provided by Cloud Run
  # Use count to only create this resource when A records are available
  count = try(
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
resource "google_dns_record_set" "frontend_domain_cname" {
  count = try(
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
  project      = var.project_id

  rrdatas = [
    for record in google_cloud_run_domain_mapping.frontend_custom_domain.status[0].resource_records :
    record.rrdata if record.type == "CNAME"
  ]

  depends_on = [google_cloud_run_domain_mapping.frontend_custom_domain]
}
