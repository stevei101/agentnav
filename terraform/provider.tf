provider "google" {
  project     = var.project_id
  region      = var.default_region
  credentials = var.google_credentials != "" ? var.google_credentials : null
}

