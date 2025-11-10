# Cross-Project DNS Setup Guide

This guide explains how to configure custom domain `agentnav.lornu.com` when the DNS zone is managed in a separate GCP project via the infrastructure repository at `https://github.com/stevei101/infrastructure`.

## Overview

**Problem:** The Agent Navigator project needs to map `agentnav.lornu.com` to its Cloud Run frontend service, but the `lornu.com` DNS zone is managed in a different GCP project via the infrastructure repository.

**Solution:** Use cross-project IAM permissions and coordinate between two repositories:
- **agentnav repository** - Creates the Cloud Run domain mapping and outputs required DNS records
- **infrastructure repository** - Creates the actual DNS records in the zone

## Architecture

```
┌─────────────────────────────────────┐  ┌─────────────────────────────────────┐
│          agentnav Project           │  │        infrastructure Project       │
│                                     │  │                                     │
│  ┌─────────────────────────────┐   │  │  ┌─────────────────────────────┐   │
│  │     Cloud Run Service       │   │  │  │      Cloud DNS Zone         │   │
│  │   agentnav-frontend         │   │  │  │       lornu.com             │   │
│  │                             │   │  │  │                             │   │
│  │  ┌─────────────────────┐   │   │  │  │   ┌─────────────────────┐   │   │
│  │  │   Domain Mapping    │   │   │  │  │   │   DNS Records       │   │   │
│  │  │ agentnav.lornu.com  │───┼───┼──┼──┼──▶│ A: 1.2.3.4          │   │   │
│  │  │                     │   │   │  │  │   │ AAAA: ::1           │   │   │
│  │  └─────────────────────┘   │   │  │  │   └─────────────────────┘   │   │
│  └─────────────────────────────┘   │  │  └─────────────────────────────┘   │
└─────────────────────────────────────┘  └─────────────────────────────────────┘
```

## Step-by-Step Setup

### Phase 1: IAM Setup (Infrastructure Project)

**Action Required:** In the infrastructure project where the DNS zone is managed, grant cross-project permissions.

```bash
# In infrastructure project (where lornu.com DNS zone exists)
export INFRASTRUCTURE_PROJECT_ID="your-infrastructure-project-id"
export AGENTNAV_PROJECT_ID="your-agentnav-project-id"

# Grant DNS reader access to agentnav project's Terraform service account
gcloud projects add-iam-policy-binding $INFRASTRUCTURE_PROJECT_ID \
  --member="serviceAccount:terraform@${AGENTNAV_PROJECT_ID}.iam.gserviceaccount.com" \
  --role="roles/dns.reader"

# If you want agentnav Terraform to manage DNS records directly (not recommended for security)
# gcloud projects add-iam-policy-binding $INFRASTRUCTURE_PROJECT_ID \
#   --member="serviceAccount:terraform@${AGENTNAV_PROJECT_ID}.iam.gserviceaccount.com" \
#   --role="roles/dns.admin"
```

### Phase 2: Configure agentnav Repository

**Action Required:** Add DNS Zone Project ID to Secret Manager using the GitHub Actions workflow.

**Run the DNS Secrets Management Workflow:**
1. Go to `Actions` tab in agentnav repository
2. Select `Manage DNS Configuration Secrets` workflow
3. Click `Run workflow` with these inputs:
   - **dns_zone_project_id:** `your-infrastructure-project-id`
   - **action:** `create-or-update`

**What this does:**
- Creates `DNS_ZONE_PROJECT_ID` secret in Google Secret Manager
- Terraform reads this secret to determine which project hosts the DNS zone
- When `DNS_ZONE_PROJECT_ID` is set, `manage_dns_in_this_project` defaults to `false` for cross-project setup

**Alternative (Manual):**
```bash
# Using gcloud CLI
echo -n "your-infrastructure-project-id" | gcloud secrets create DNS_ZONE_PROJECT_ID \
  --data-file=- --replication-policy=automatic \
  --project=your-agentnav-project-id
```

### Phase 3: Deploy agentnav Infrastructure

**Action Required:** Trigger Terraform deployment via GitHub Actions.

**Method 1: Push to main branch (auto-apply)**
```bash
# Commit your changes and push to main
git add terraform/
git commit -m "Configure cross-project DNS for agentnav.lornu.com"
git push origin main

# GitHub Actions will automatically run terraform apply
```

**Method 2: Create Pull Request (plan only)**
```bash
# Create feature branch and push
git checkout -b feature/cross-project-dns
git add .github/workflows/terraform.yml terraform/ docs/
git commit -m "Configure cross-project DNS for agentnav.lornu.com"
git push origin feature/cross-project-dns

# Create PR - GitHub Actions will run terraform plan and comment results
# Verify the plan shows the correct cross-project DNS configuration
```

**Method 3: Get DNS records from Terraform Cloud**
```bash
# After deployment, check Terraform Cloud workspace outputs
# Or use Terraform CLI with remote backend:
terraform init
terraform output dns_records_for_manual_creation
```

**Expected Output:**
```json
{
  "domain_name": "agentnav.lornu.com",
  "zone_name": "lornu-com",
  "zone_project": "your-infrastructure-project-id",
  "records": [
    {
      "name": "agentnav.lornu.com.",
      "type": "A",
      "ttl": 300,
      "rrdatas": ["142.251.46.84"]
    },
    {
      "name": "agentnav.lornu.com.",
      "type": "AAAA", 
      "ttl": 300,
      "rrdatas": ["2607:f8b0:4004:c1b::52"]
    }
  ]
}
```

### Phase 4: Create DNS Records (Infrastructure Repository)

**Action Required:** Add DNS records to the infrastructure repository's Terraform configuration.

In the infrastructure repository, add these resources:

```hcl
# infrastructure repository - dns.tf or similar
data "google_dns_managed_zone" "lornu_zone" {
  name = "lornu-com"
  project = var.project_id  # infrastructure project ID
}

# A record for agentnav subdomain
resource "google_dns_record_set" "agentnav_a" {
  name         = "agentnav.lornu.com."
  managed_zone = data.google_dns_managed_zone.lornu_zone.name
  type         = "A"
  ttl          = 300
  project      = var.project_id

  # Copy these IP addresses from agentnav terraform output
  rrdatas = [
    "142.251.46.84",  # Replace with actual IPs from agentnav output
  ]
}

# AAAA record for IPv6 (if provided by Cloud Run)
resource "google_dns_record_set" "agentnav_aaaa" {
  count        = length(var.agentnav_ipv6_addresses) > 0 ? 1 : 0
  name         = "agentnav.lornu.com."
  managed_zone = data.google_dns_managed_zone.lornu_zone.name
  type         = "AAAA"
  ttl          = 300
  project      = var.project_id

  rrdatas = var.agentnav_ipv6_addresses  # Variable for IPv6 addresses
}
```

Add to `variables.tf` in infrastructure repository:

```hcl
variable "agentnav_ipv4_addresses" {
  description = "IPv4 addresses for agentnav.lornu.com A records from Cloud Run domain mapping"
  type        = list(string)
  default     = []
}

variable "agentnav_ipv6_addresses" {
  description = "IPv6 addresses for agentnav.lornu.com AAAA records from Cloud Run domain mapping"
  type        = list(string)
  default     = []
}
```

### Phase 5: Deploy Infrastructure Changes

**Action Required:** Apply Terraform in the infrastructure repository.

```bash
# In infrastructure repository (github.com/stevei101/infrastructure)
# Follow the same GitHub Actions pattern as agentnav if applicable, or run locally:
terraform init
terraform plan -var='agentnav_ipv4_addresses=["142.251.46.84"]'
terraform apply

# Or commit and push if infrastructure repo uses GitHub Actions too
git add .
git commit -m "Add DNS records for agentnav.lornu.com"
git push origin main
```

### Phase 6: Verification

**Action Required:** Verify the domain mapping is working.

```bash
# Test DNS resolution
nslookup agentnav.lornu.com
dig agentnav.lornu.com

# Test HTTPS connectivity
curl -I https://agentnav.lornu.com

# Verify Cloud Run domain mapping status
gcloud run domain-mappings list --region=us-central1
```

## GitHub Actions Integration

The agentnav repository uses GitHub Actions for Terraform deployment via `.github/workflows/terraform.yml`:

- **Terraform Cloud Backend:** Uses remote state management
- **Workload Identity Federation:** Authenticates to GCP without service account keys  
- **Automated Workflow:**
  - **Pull Requests:** Runs `terraform plan` and comments results
  - **Main Branch Push:** Runs `terraform apply` automatically
  - **Validation:** Includes `terraform fmt`, `terraform validate`, `tflint`, and `tfsec`

### Required Configuration

**GitHub Repository Secrets** (already configured):
| Secret | Description | Example |
|--------|-------------|---------|
| `GCP_PROJECT_ID` | agentnav GCP project ID | `agentnav-prod-12345` |
| `TF_CLOUD_ORGANIZATION` | Terraform Cloud org name | `your-org-name` |
| `TF_WORKSPACE` | Terraform Cloud workspace | `agentnav-prod` |
| `TF_API_TOKEN` | Terraform Cloud API token | `***` |
| `WIF_PROVIDER` | Workload Identity Federation provider | `projects/123/locations/.../providers/github` |
| `WIF_SERVICE_ACCOUNT` | WIF service account email | `terraform@agentnav-prod-12345.iam.gserviceaccount.com` |

**Google Secret Manager Secrets** (created via workflow):
| Secret | Description | Created By |
|--------|-------------|------------|
| `DNS_ZONE_PROJECT_ID` | Infrastructure project ID where DNS zone exists | `Manage DNS Configuration Secrets` workflow |

## Configuration Reference

### agentnav Repository Variables

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `dns_zone_name` | Name of Cloud DNS managed zone | `"lornu-com"` | No |
| `manage_dns_in_this_project` | Whether to create DNS records in this project | `true` | No |
| `custom_domain_name` | Custom domain for frontend service | `"agentnav.lornu.com"` | No |

> **Note:** The DNS zone project is configured via the `DNS_ZONE_PROJECT_ID` secret in Secret Manager, not via a Terraform variable.
### Cross-Project IAM Requirements

**Minimum Required Roles:**
- `roles/dns.reader` - Allows agentnav Terraform to read DNS zone information
- `roles/dns.admin` - (Optional) Allows agentnav Terraform to create DNS records directly

**Service Account:** `terraform@{agentnav-project-id}.iam.gserviceaccount.com`

## Troubleshooting

### Common Issues

**1. "Permission denied" when reading DNS zone**
```
Error: Error when reading or editing managed zone "lornu-com": googleapi: Error 403: Forbidden
```
**Solution:** Ensure IAM permissions are granted in the infrastructure project.

**2. "Domain mapping stuck in 'Mapping'"**
```
Status: Mapping
```
**Solution:** Check that DNS records point to the correct Cloud Run IP addresses.

**3. "Certificate provisioning failed"**
```
Status: Failed to provision certificate
```
**Solution:** Verify DNS records are propagated globally and accessible from Google's certificate authority.

### Verification Commands

```bash
# Check domain mapping status
gcloud run domain-mappings describe agentnav.lornu.com --region=us-central1

# Check DNS propagation
dig @8.8.8.8 agentnav.lornu.com
dig @1.1.1.1 agentnav.lornu.com

# Check certificate status
echo | openssl s_client -servername agentnav.lornu.com -connect agentnav.lornu.com:443 2>/dev/null | openssl x509 -noout -dates
```

## Security Considerations

1. **Least Privilege:** Only grant `roles/dns.reader` unless DNS record management is required
2. **Service Account Security:** Use Workload Identity Federation instead of service account keys
3. **DNS Zone Protection:** Keep DNS zone management in the infrastructure repository for centralized control
4. **Certificate Management:** Let Cloud Run handle TLS certificates automatically

## Maintenance

### Updating IP Addresses

When Cloud Run changes IP addresses (rare), update the DNS records:

1. Get new IP addresses from agentnav repository: `terraform output dns_records_for_manual_creation`
2. Update infrastructure repository variables or Terraform configuration
3. Apply changes: `terraform apply`

### Certificate Renewal

Cloud Run automatically renews TLS certificates. No manual intervention required.

## Alternative Approaches

### Option 1: Delegate Subdomain Management

Create a separate DNS zone for `agentnav.lornu.com` in the agentnav project:

**Pros:** Full control in agentnav project
**Cons:** Requires NS record delegation in infrastructure project

### Option 2: Service Account Key Sharing

Share infrastructure project service account key with agentnav CI/CD:

**Pros:** Simple configuration
**Cons:** Security risk, violates least privilege principle

### Option 3: Manual DNS Management

Skip Terraform for DNS records, create manually:

**Pros:** No cross-project IAM required
**Cons:** Violates Infrastructure as Code principles

## Recommended Approach

The cross-project IAM approach documented above is recommended because:
- ✅ Maintains security boundaries
- ✅ Follows Infrastructure as Code principles  
- ✅ Provides centralized DNS zone management
- ✅ Uses Google Cloud native IAM features
- ✅ Supports automated certificate management

---

**Next Steps:**
1. Configure IAM permissions in infrastructure project
2. Update agentnav repository Terraform variables
3. Apply agentnav Terraform to create domain mapping
4. Extract DNS record requirements from Terraform output
5. Update infrastructure repository with DNS records
6. Apply infrastructure Terraform changes
7. Verify domain mapping and certificate provisioning