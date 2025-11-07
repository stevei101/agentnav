provider "google" {
  project = var.project_id
  region  = var.default_region
  # credentials will be loaded from GOOGLE_CREDENTIALS env var if set
}

