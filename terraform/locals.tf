locals {
  github_actions_sa_email = data.google_service_account.github_actions.email
  
  # DNS project ID - use separate project if specified, otherwise use main project
  dns_project_id = var.dns_project_id != "" ? var.dns_project_id : var.project_id
  
  # Is this a cross-project DNS setup?
  is_cross_project_dns = var.dns_project_id != "" && var.dns_project_id != var.project_id
}

