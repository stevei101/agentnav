# Cross-Project Cloud DNS Integration Guide

This guide explains how to configure Cloud Run custom domain mapping when the DNS zone is hosted in a **different Google Cloud Project** from your Agent Navigator deployment project.

## Problem Statement

The Agent Navigator application requires a custom domain (`agentnav.lornu.com`) for its production endpoint. However, the primary DNS zone (`lornu.com`) is managed in a separate Google Cloud Project. This creates a cross-project dependency that requires special configuration.

## Architecture Overview

```
┌─────────────────────────────────────┐
│  DNS Owner Project                  │
│  (e.g., "company-dns-prod")        │
│                                     │
│  ┌───────────────────────────────┐ │
│  │  Cloud DNS Zone               │ │
│  │  Zone: lornu.com              │ │
│  │                               │ │
│  │  Records:                     │ │
│  │  - agentnav.lornu.com. A      │ │
│  │  - agentnav.lornu.com. CNAME  │ │
│  └───────────────────────────────┘ │
└─────────────────────────────────────┘
                 ▲
                 │ DNS Records Created
                 │ Manually or via Terraform
                 │
┌─────────────────────────────────────┐
│  Agent Navigator Project            │
│  (e.g., "agentnav-prod")           │
│                                     │
│  ┌───────────────────────────────┐ │
│  │  Cloud Run Domain Mapping     │ │
│  │  Domain: agentnav.lornu.com   │ │
│  │  Service: agentnav-frontend   │ │
│  │                               │ │
│  │  Status: Provides DNS Records │ │
│  └───────────────────────────────┘ │
│                                     │
│  ┌───────────────────────────────┐ │
│  │  Cloud Run Service            │ │
│  │  Name: agentnav-frontend      │ │
│  └───────────────────────────────┘ │
└─────────────────────────────────────┘
```

## Prerequisites

1. **Access to Both Projects**: You need appropriate permissions in both projects
2. **DNS Zone Exists**: The DNS zone must already exist in the DNS owner project
3. **Cloud Run Service Deployed**: The Agent Navigator Cloud Run service must be deployed

## Solution Overview

The solution involves three main steps:

1. **Configure Terraform** to reference the cross-project DNS zone
2. **Apply Terraform** to create the Cloud Run domain mapping
3. **Create DNS Records** manually in the DNS owner project

## Step 1: Configure Terraform Variables

Edit your `terraform/terraform.tfvars` file:

```hcl
# Your Agent Navigator project ID
project_id = "agentnav-prod"

# Custom domain configuration
custom_domain_name = "agentnav.lornu.com"
dns_zone_name      = "lornu-com"

# Cross-project DNS configuration
dns_project_id     = "company-dns-prod"  # The project where DNS zone is hosted
enable_dns_records = false               # Disable automatic DNS record creation
```

**Key Variables:**

- `dns_project_id`: The project ID where the Cloud DNS zone is hosted
- `enable_dns_records = false`: Prevents Terraform from attempting to create DNS records in the DNS owner project (which would fail without proper IAM permissions)

## Step 2: Optional - Grant Cross-Project IAM Permissions

This step is **optional** and only needed if you want Terraform to validate DNS zone access. It's not required for the domain mapping to work.

### In the DNS Owner Project:

Grant the Agent Navigator project's Terraform/GitHub Actions service account read access to the DNS zone:

```bash
# Set variables
DNS_PROJECT_ID="company-dns-prod"
AGENTNAV_PROJECT_ID="agentnav-prod"
GITHUB_ACTIONS_SA="github-actions@${AGENTNAV_PROJECT_ID}.iam.gserviceaccount.com"

# Grant DNS reader role
gcloud projects add-iam-policy-binding ${DNS_PROJECT_ID} \
  --member="serviceAccount:${GITHUB_ACTIONS_SA}" \
  --role="roles/dns.reader" \
  --condition=None

# Verify the binding
gcloud projects get-iam-policy ${DNS_PROJECT_ID} \
  --flatten="bindings[].members" \
  --filter="bindings.members:serviceAccount:${GITHUB_ACTIONS_SA}"
```

**Note:** `roles/dns.reader` is a read-only role that allows Terraform to validate the DNS zone exists but does not allow creating or modifying records.

## Step 3: Apply Terraform in Agent Navigator Project

In your Agent Navigator project, apply Terraform to create the domain mapping:

```bash
cd terraform
terraform init
terraform plan
terraform apply
```

This will create:
- The `google_cloud_run_domain_mapping` resource
- Output the required DNS records for manual creation

**Verify the domain mapping:**

```bash
gcloud run domain-mappings describe agentnav.lornu.com \
  --region=us-central1 \
  --project=${AGENTNAV_PROJECT_ID}
```

## Step 4: Get Required DNS Records

After Terraform apply, get the DNS records that need to be created:

```bash
# Get DNS records from Terraform output
terraform output domain_mapping_dns_records

# Alternative: Get from Cloud Run directly
gcloud run domain-mappings describe agentnav.lornu.com \
  --region=us-central1 \
  --project=${AGENTNAV_PROJECT_ID} \
  --format="value(status.resourceRecords)"
```

Example output:
```json
[
  {
    "name": "agentnav.lornu.com.",
    "rrdata": "216.239.32.21",
    "type": "A",
    "ttl": 300
  },
  {
    "name": "agentnav.lornu.com.",
    "rrdata": "216.239.34.21",
    "type": "A",
    "ttl": 300
  },
  {
    "name": "agentnav.lornu.com.",
    "rrdata": "ghs.googlehosted.com.",
    "type": "CNAME",
    "ttl": 300
  }
]
```

## Step 5: Create DNS Records in DNS Owner Project

Now create the DNS records in the DNS owner project. You have two options:

### Option A: Manual Creation via gcloud

```bash
# Switch to DNS owner project
DNS_PROJECT_ID="company-dns-prod"
DNS_ZONE_NAME="lornu-com"

# Create A records (if provided by Cloud Run)
gcloud dns record-sets create agentnav.lornu.com. \
  --zone=${DNS_ZONE_NAME} \
  --type=A \
  --ttl=300 \
  --rrdatas="216.239.32.21,216.239.34.21" \
  --project=${DNS_PROJECT_ID}

# OR Create CNAME record (if provided by Cloud Run - use either A or CNAME, not both)
gcloud dns record-sets create agentnav.lornu.com. \
  --zone=${DNS_ZONE_NAME} \
  --type=CNAME \
  --ttl=300 \
  --rrdatas="ghs.googlehosted.com." \
  --project=${DNS_PROJECT_ID}
```

### Option B: Using Terraform in DNS Owner Project

Create a separate Terraform configuration in the DNS owner project:

```hcl
# dns-owner-project/terraform/agentnav_dns.tf

# Reference existing DNS zone
data "google_dns_managed_zone" "lornu_zone" {
  name    = "lornu-com"
  project = "company-dns-prod"
}

# Create A records for agentnav.lornu.com
resource "google_dns_record_set" "agentnav_a" {
  name         = "agentnav.lornu.com."
  managed_zone = data.google_dns_managed_zone.lornu_zone.name
  type         = "A"
  ttl          = 300
  project      = "company-dns-prod"
  
  rrdatas = [
    "216.239.32.21",
    "216.239.34.21"
  ]
}

# OR Create CNAME record (use either A or CNAME, not both)
resource "google_dns_record_set" "agentnav_cname" {
  name         = "agentnav.lornu.com."
  managed_zone = data.google_dns_managed_zone.lornu_zone.name
  type         = "CNAME"
  ttl          = 300
  project      = "company-dns-prod"
  
  rrdatas = ["ghs.googlehosted.com."]
}
```

Apply the Terraform configuration:

```bash
cd dns-owner-project/terraform
terraform init
terraform plan
terraform apply
```

## Step 6: Verify Domain Mapping

Wait for DNS propagation (typically 5-15 minutes), then verify:

```bash
# Test DNS resolution
dig agentnav.lornu.com
nslookup agentnav.lornu.com

# Test HTTPS connectivity
curl -I https://agentnav.lornu.com

# Check certificate
openssl s_client -connect agentnav.lornu.com:443 -servername agentnav.lornu.com
```

## Step 7: Monitor Domain Mapping Status

Check the domain mapping status in the Agent Navigator project:

```bash
# Get domain mapping status
gcloud run domain-mappings describe agentnav.lornu.com \
  --region=us-central1 \
  --project=${AGENTNAV_PROJECT_ID}

# Check certificate provisioning
gcloud run domain-mappings describe agentnav.lornu.com \
  --region=us-central1 \
  --project=${AGENTNAV_PROJECT_ID} \
  --format="value(status.conditions)"
```

Expected status: `ACTIVE` or `READY`

## IAM Requirements Summary

### In Agent Navigator Project:
- **GitHub Actions Service Account** needs:
  - `roles/run.admin` - To create domain mapping
  - `roles/iam.serviceAccountUser` - To deploy to Cloud Run

### In DNS Owner Project (Optional):
- **Agent Navigator Service Account** needs:
  - `roles/dns.reader` - To validate DNS zone (read-only)
  
### For DNS Record Creation:
- **Manual Approach**: User needs `roles/dns.admin` in DNS owner project
- **Terraform Approach**: Service Account needs `roles/dns.admin` in DNS owner project

## Troubleshooting

### Domain Mapping Shows "CertificatePending"

```bash
# Check certificate status
gcloud run domain-mappings describe agentnav.lornu.com \
  --region=us-central1 \
  --format="value(status.conditions[0].message)"
```

**Solution:** Wait for DNS propagation and certificate provisioning (can take up to 24 hours, typically 15-30 minutes).

### DNS Not Resolving

```bash
# Check if records exist
gcloud dns record-sets list \
  --zone=${DNS_ZONE_NAME} \
  --filter="name:agentnav.lornu.com." \
  --project=${DNS_PROJECT_ID}
```

**Solution:** Verify records were created correctly with trailing dot (`.`) in the name.

### Permission Denied Errors

**Error:** `Permission denied on resource project DNS_PROJECT_ID`

**Solution:** Grant `roles/dns.reader` to the service account in the DNS owner project (see Step 2).

### Cloud Run Domain Mapping Not Ready

```bash
# Get detailed status
gcloud run domain-mappings describe agentnav.lornu.com \
  --region=us-central1 \
  --format=yaml
```

**Common Issues:**
- DNS records not created or incorrect
- Domain ownership not verified
- Cloud Run service not deployed

## Security Considerations

1. **Least Privilege IAM**: Only grant necessary permissions
   - Use `roles/dns.reader` (read-only) when possible
   - Only grant `roles/dns.admin` when DNS record creation is needed

2. **Service Account Scoping**: 
   - The GitHub Actions service account should only have permissions in the Agent Navigator project
   - DNS owner project should maintain separate access controls

3. **Audit Logging**: Enable Cloud Audit Logs in both projects to track DNS and domain mapping changes

## Alternative: Single-Project Setup

If you have the ability to move the DNS zone to the Agent Navigator project, you can simplify the setup:

```hcl
# terraform/terraform.tfvars

project_id         = "agentnav-prod"
custom_domain_name = "agentnav.lornu.com"
dns_zone_name      = "lornu-com"
# dns_project_id not needed - defaults to project_id
# enable_dns_records = true (default)
```

With this configuration, Terraform will automatically create DNS records in the same project.

## Success Criteria

- [ ] Terraform successfully creates `google_cloud_run_domain_mapping` resource
- [ ] DNS records created in DNS owner project
- [ ] Domain mapping status shows `ACTIVE` or `READY`
- [ ] `https://agentnav.lornu.com` resolves and serves the frontend service
- [ ] TLS certificate is valid and automatically provisioned by Cloud Run

## Related Documentation

- [Custom Domain Setup Guide](./CUSTOM_DOMAIN_SETUP.md)
- [GCP Setup Guide](./GCP_SETUP_GUIDE.md)
- [Terraform First Apply Guide](./TERRAFORM_FIRST_APPLY.md)
- [Cloud Run Custom Domains Documentation](https://cloud.google.com/run/docs/mapping-custom-domains)
- [Cloud DNS Cross-Project Setup](https://cloud.google.com/dns/docs/access-control)

## Support

For issues or questions:
1. Check the troubleshooting section above
2. Review Terraform outputs: `terraform output domain_mapping_dns_records`
3. Check Cloud Run domain mapping status
4. Verify DNS records in DNS owner project
