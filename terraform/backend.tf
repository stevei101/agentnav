# Terraform Cloud Backend Configuration
# State is stored remotely in Terraform Cloud
terraform {
  backend "remote" {
    organization = "CHANGE_ME"  # Set via environment variable TF_CLOUD_ORGANIZATION

    workspaces {
      name = "CHANGE_ME"  # Set via environment variable TF_WORKSPACE
    }
  }
}

# Note: To initialize with Terraform Cloud:
# terraform init \
#   -backend-config="organization=YOUR_ORG" \
#   -backend-config="workspaces.name=YOUR_WORKSPACE"

