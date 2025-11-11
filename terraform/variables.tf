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

# TODO: Uncomment when WIF resources are uncommented in iam.tf
# variable "workload_identity_pool_id" {
#   description = "Workload Identity Pool ID for GitHub Actions"
#   type        = string
#   default     = "github-actions-pool"
# }
#
# variable "workload_identity_provider_id" {
#   description = "Workload Identity Provider ID for GitHub Actions"
#   type        = string
#   default     = "github-provider"
# }

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

variable "environment" {
  description = "Environment name (dev, staging, prod)"
  type        = string
  default     = "prod"
}

variable "github_branch" {
  description = "GitHub branch to deploy from (e.g., 'main', 'production')"
  type        = string
  default     = "main"
}

variable "enable_connect_repo" {
  description = "Enable Cloud Run Connect Repo for automatic deployments from GitHub"
  type        = bool
  default     = true
}

variable "frontend_container_port" {
  description = "Container port for frontend Cloud Run service"
  type        = number
  default     = 80
}

variable "backend_container_port" {
  description = "Container port for backend Cloud Run service"
  type        = number
  default     = 8080
}

variable "enable_staging_environment" {
  description = "Enable staging environment Cloud Run services for PR testing and validation."
  type        = bool
  default     = true # Enabled to support staging deployments for PRs
}

variable "custom_domain_name" {
  description = "Custom domain name for the frontend service (e.g., 'agentnav.lornu.com')"
  type        = string
  default     = "agentnav.lornu.com"
}

variable "dns_zone_name" {
  description = "Name of the Cloud DNS managed zone for the custom domain (e.g., 'lornu-com' or 'lornu-zone')"
  type        = string
  default     = "lornu-com"
}

# DNS zone project is now read from Secret Manager (DNS_ZONE_PROJECT_ID)
# This provides better security for cross-project configuration

variable "manage_dns_in_this_project" {
  description = "If true, Terraform will create Cloud DNS record sets in the project where Terraform runs. If false, the required DNS records will be output for manual creation in the DNS owner project."
  type        = bool
  default     = false # Default to false for cross-project DNS setup
}

variable "gke_region" {
  description = "Region for the primary GKE cluster"
  type        = string
  default     = "europe-west1"
}

variable "gke_cluster_name" {
  description = "Name of the primary GKE cluster"
  type        = string
  default     = "agentnav-gke"
}

variable "gke_network_name" {
  description = "Name of the VPC network used by GKE"
  type        = string
  default     = "agentnav-gke-network"
}

variable "gke_subnet_name" {
  description = "Name of the subnet used by GKE"
  type        = string
  default     = "agentnav-gke-subnet"
}

variable "gke_subnet_cidr" {
  description = "CIDR range for the GKE subnet"
  type        = string
  default     = "10.20.0.0/20"
}

variable "gke_node_machine_type" {
  description = "Machine type for the default GKE node pool"
  type        = string
  default     = "e2-standard-4"
}

variable "gke_node_count_min" {
  description = "Minimum number of nodes in the default node pool"
  type        = number
  default     = 2
}

variable "gke_node_count_max" {
  description = "Maximum number of nodes in the default node pool"
  type        = number
  default     = 5
}

variable "enable_gpu_node_pool" {
  description = "Whether to provision a GPU-enabled node pool for Gemma workloads"
  type        = bool
  default     = false
}

variable "gke_gpu_machine_type" {
  description = "Machine type for the GPU node pool"
  type        = string
  default     = "g2-standard-8"
}

variable "gke_gpu_accelerator_type" {
  description = "GPU accelerator type for the GPU node pool"
  type        = string
  default     = "nvidia-l4"
}

variable "gke_gpu_accelerator_count" {
  description = "Number of GPU accelerators per node"
  type        = number
  default     = 1
}


variable "gke_deletion_protection" {
  description = "Enable deletion protection on the primary GKE cluster"
  type        = bool
  default     = false
}

variable "gke_default_pool_preemptible" {
  description = "Whether nodes in the default GKE node pool should be preemptible"
  type        = bool
  default     = false
}
