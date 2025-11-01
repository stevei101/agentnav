# Terraform Cloud Backend Configuration
# State is stored remotely in Terraform Cloud
terraform {
  cloud {
    organization = "disposable-org"
    workspaces {
      name = "agentnav"
    }
  }
}

