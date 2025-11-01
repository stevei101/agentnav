variable "project_id" {
  description = "Google Cloud Project ID"
  type        = string
  # This will be set via environment variable or terraform.tfvars
}

variable "default_region" {
  description = "Default GCP region"
  type        = string
  default     = "us-central1"
}

variable "github_repository" {
  description = "GitHub repository in format 'owner/repo' (e.g., 'stevei101/agentnav')"
  type        = string
  default     = "stevei101/agentnav"
}

variable "workload_identity_pool_id" {
  description = "Workload Identity Pool ID for GitHub Actions"
  type        = string
  default     = "github-actions-pool"
}

variable "workload_identity_provider_id" {
  description = "Workload Identity Provider ID for GitHub Actions"
  type        = string
  default     = "github-provider"
}

variable "artifact_registry_location" {
  description = "Location for Artifact Registry (should match region with GPU support)"
  type        = string
  default     = "europe-west1"
}

variable "artifact_registry_repository_id" {
  description = "Artifact Registry repository ID"
  type        = string
  default     = "agentnav-containers"
}

variable "firestore_database_id" {
  description = "Firestore database ID"
  type        = string
  default     = "agentnav-db"
}

variable "frontend_region" {
  description = "Region for frontend Cloud Run service"
  type        = string
  default     = "us-central1"
}

variable "backend_region" {
  description = "Region for backend Cloud Run service"
  type        = string
  default     = "europe-west1"
}

variable "gemma_region" {
  description = "Region for Gemma GPU Cloud Run service (must support GPUs)"
  type        = string
  default     = "europe-west1"
}

variable "environment" {
  description = "Environment name (dev, staging, prod)"
  type        = string
  default     = "prod"
}

variable "domain_name" {
  description = "Custom domain name for Cloud Run services (optional)"
  type        = string
  default     = ""
}

