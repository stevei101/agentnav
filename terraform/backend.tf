# Terraform Cloud Backend Configuration
# State is stored remotely in Terraform Cloud
# This uses partial configuration - values must be provided via:
#   - Environment variables: TF_CLOUD_ORGANIZATION, TF_WORKSPACE
#   - CLI flags: -backend-config="organization=..." -backend-config="workspaces.name=..."
#   - terraform.tfvars (if using a local backend alternative)
terraform {
  backend "remote" {
    # Organization and workspace must be provided via -backend-config flags or environment variables
    # Do NOT hardcode values here - use partial configuration instead
  }
}

# To initialize with Terraform Cloud backend:
# terraform init \
#   -backend-config="organization=YOUR_ORG" \
#   -backend-config="workspaces.name=YOUR_WORKSPACE"

