# Enable Required Google Cloud APIs
# These APIs must be enabled for the infrastructure to function

resource "google_project_service" "apis" {
  for_each = toset([
    # Cloud Run
    "run.googleapis.com",

    # Artifact Registry
    "artifactregistry.googleapis.com",

    # Firestore
    "firestore.googleapis.com",

    # Secret Manager
    "secretmanager.googleapis.com",

    # IAM (for service accounts, WIF, etc.)
    "iam.googleapis.com",

    # Cloud Resource Manager (for project operations)
    "cloudresourcemanager.googleapis.com",

    # Service Usage (for API management)
    "serviceusage.googleapis.com",

    # Cloud Build (for Connect Repo / automatic deployments)
    "cloudbuild.googleapis.com",

    # Cloud DNS API (required for custom domain DNS records)
    "dns.googleapis.com",
  ])

  project = var.project_id
  service = each.value

  disable_on_destroy = false # Keep APIs enabled even if Terraform destroys resources

  timeouts {
    create = "10m"
    update = "10m"
  }
}

