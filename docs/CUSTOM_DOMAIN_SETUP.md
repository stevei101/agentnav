# Custom Domain Setup Guide for Cloud Run

This guide explains how to configure a custom domain (`agentnav.lornu.com`) for the Cloud Run frontend service using Terraform.

## Overview

Cloud Run automatically manages TLS/SSL certificates - **no cert-manager or external certificate management is needed**. The setup requires:

1. **Cloud Run Domain Mapping** - Maps the custom domain to the Cloud Run service
2. **Cloud DNS Records** - Points the domain to Cloud Run (A and/or CNAME records)

## Prerequisites

1. **Existing Cloud DNS Zone**: The DNS zone for `lornu.com` must already exist in GCP Cloud DNS
   - Check existing zones: `gcloud dns managed-zones list`
   - If missing, create it: `gcloud dns managed-zones create lornu-com --dns-name=lornu.com --description="lornu.com DNS zone"`

2. **Domain Ownership Verification**: The domain must be verified in Google Cloud Console
   - Cloud Run domain mapping requires domain ownership verification
   - Follow: [Cloud Run Domain Mapping Documentation](https://cloud.google.com/run/docs/mapping-custom-domains)

## Terraform Configuration

### Variables

Add to your `terraform.tfvars`:

```hcl
# Custom domain for frontend service
custom_domain_name = "agentnav.lornu.com"

# Cloud DNS managed zone name (must already exist)
# Find with: gcloud dns managed-zones list
dns_zone_name = "lornu-com"
```

### What Gets Created

1. **Cloud Run Domain Mapping** (`google_cloud_run_domain_mapping.frontend_custom_domain`)
   - Maps `agentnav.lornu.com` to `agentnav-frontend` service
   - Cloud Run automatically provisions and manages TLS certificate
   - Provides target DNS records in `status.resource_records`

2. **Cloud DNS A Records** (`google_dns_record_set.frontend_domain_a`)
   - Creates A records pointing to Cloud Run IPs
   - Extracted from domain mapping status

3. **Cloud DNS CNAME Record** (`google_dns_record_set.frontend_domain_cname`) (optional)
   - Created only if Cloud Run provides CNAME records
   - Some configurations use CNAME instead of A records

## Deployment Steps

### 1. Verify DNS Zone Exists

```bash
gcloud dns managed-zones list --project=YOUR_PROJECT_ID
```

If the zone doesn't exist, create it first:

```bash
gcloud dns managed-zones create lornu-com \
  --dns-name=lornu.com \
  --description="lornu.com DNS zone" \
  --project=YOUR_PROJECT_ID
```

### 2. Configure Terraform Variables

Edit `terraform/terraform.tfvars`:

```hcl
custom_domain_name = "agentnav.lornu.com"
dns_zone_name = "lornu-com"  # Adjust to match your actual zone name
```

### 3. Apply Terraform

```bash
cd terraform
terraform init
terraform plan
terraform apply
```

### 4. Verify Domain Mapping

After `terraform apply`:

```bash
# Check domain mapping status
gcloud run domain-mappings describe agentnav.lornu.com \
  --region=us-central1 \
  --project=YOUR_PROJECT_ID

# Check DNS records
# Note: DNS record names in Cloud DNS include a trailing dot
gcloud dns record-sets list \
  --zone=lornu-com \
  --filter="name:agentnav.lornu.com." \
  --project=YOUR_PROJECT_ID
```

### 5. Test Domain Connectivity

Wait for DNS propagation (usually 5-15 minutes), then:

```bash
# Test DNS resolution
dig agentnav.lornu.com
nslookup agentnav.lornu.com

# Test HTTPS connectivity
curl -I https://agentnav.lornu.com
```

## How It Works

1. **Cloud Run Domain Mapping** creates the domain-to-service mapping and automatically:
   - Provisions a managed TLS certificate
   - Provides target DNS records (A and/or CNAME) in `status.resource_records`

2. **Terraform extracts** the DNS records from the domain mapping status

3. **Cloud DNS Records** are created pointing to Cloud Run's infrastructure

4. **DNS propagation** makes the domain publicly accessible (usually 5-15 minutes)

## Troubleshooting

### Domain Mapping Status Check

```bash
gcloud run domain-mappings describe agentnav.lornu.com \
  --region=us-central1 \
  --format="value(status)"
```

Expected status: `ACTIVE` or `READY`

### DNS Propagation Check

```bash
# Check DNS resolution from external server
dig @8.8.8.8 agentnav.lornu.com

# Check from local machine
nslookup agentnav.lornu.com
```

### Common Issues

1. **DNS Zone Not Found**
   - Error: `google_dns_managed_zone.lornu_zone: resource not found`
   - Solution: Create the DNS zone first or verify the `dns_zone_name` variable

2. **Domain Not Verified**
   - Error: Domain ownership verification required
   - Solution: Verify domain ownership in Google Cloud Console

3. **DNS Records Not Created**
   - Check: `terraform output domain_mapping_status`
   - Wait for domain mapping to reach `READY` status before DNS records are available

## Terraform Outputs

After applying, check:

```bash
terraform output custom_domain_url
terraform output domain_mapping_status
```

## Important Notes

- **TLS is Automatic**: Cloud Run handles all TLS/SSL certificate provisioning and renewal
- **No cert-manager Needed**: External certificate management tools are not required
- **DNS Zone Must Exist**: The Cloud DNS zone must be created before Terraform can reference it
- **Propagation Time**: DNS changes typically take 5-15 minutes to propagate globally

## Reference

- [Cloud Run Custom Domains Documentation](https://cloud.google.com/run/docs/mapping-custom-domains)
- [Cloud DNS Documentation](https://cloud.google.com/dns/docs)
- [Terraform Cloud Run Domain Mapping](https://registry.terraform.io/providers/hashicorp/google/latest/docs/resources/cloud_run_domain_mapping)
- [Terraform Cloud DNS Record Set](https://registry.terraform.io/providers/hashicorp/google/latest/docs/resources/dns_record_set)

