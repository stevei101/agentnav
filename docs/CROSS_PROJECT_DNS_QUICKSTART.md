# Quick Start: Cross-Project DNS Setup

This is a quick reference for setting up cross-project DNS for `agentnav.lornu.com`. For detailed documentation, see [CROSS_PROJECT_DNS_SETUP.md](./CROSS_PROJECT_DNS_SETUP.md).

## Quick Setup Steps

### 1. Configure Terraform (Agent Navigator Project)

Edit `terraform/terraform.tfvars`:

```hcl
project_id         = "agentnav-prod"           # Your Agent Navigator project
custom_domain_name = "agentnav.lornu.com"
dns_zone_name      = "lornu-com"
dns_project_id     = "company-dns-prod"        # DNS owner project
enable_dns_records = false                     # Don't auto-create DNS records
```

### 2. Apply Terraform (Agent Navigator Project)

```bash
cd terraform
terraform init
terraform plan
terraform apply
```

### 3. Get DNS Records

```bash
# From Terraform output
terraform output domain_mapping_dns_records

# Or from Cloud Run
gcloud run domain-mappings describe agentnav.lornu.com \
  --region=us-central1 \
  --format="value(status.resourceRecords)"
```

### 4. Create DNS Records (DNS Owner Project)

Switch to the DNS owner project and create records:

**Option A - Using gcloud:**

```bash
# For A records (example IPs - use actual values from step 3)
gcloud dns record-sets create agentnav.lornu.com. \
  --zone=lornu-com \
  --type=A \
  --ttl=300 \
  --rrdatas="216.239.32.21,216.239.34.21" \
  --project=company-dns-prod

# OR for CNAME (use either A or CNAME, not both)
gcloud dns record-sets create agentnav.lornu.com. \
  --zone=lornu-com \
  --type=CNAME \
  --ttl=300 \
  --rrdatas="ghs.googlehosted.com." \
  --project=company-dns-prod
```

**Option B - Using Terraform in DNS Owner Project:**

Create `dns-records.tf` in DNS owner project:

```hcl
data "google_dns_managed_zone" "lornu_zone" {
  name    = "lornu-com"
  project = "company-dns-prod"
}

resource "google_dns_record_set" "agentnav_a" {
  name         = "agentnav.lornu.com."
  managed_zone = data.google_dns_managed_zone.lornu_zone.name
  type         = "A"
  ttl          = 300
  project      = "company-dns-prod"
  rrdatas      = ["216.239.32.21", "216.239.34.21"]  # Use actual IPs from step 3
}
```

### 5. Verify

Wait 5-15 minutes for DNS propagation, then:

```bash
# Test DNS
dig agentnav.lornu.com

# Test HTTPS
curl -I https://agentnav.lornu.com
```

## Optional: Grant Cross-Project IAM

Only needed if you want Terraform to validate DNS zone access:

```bash
# In DNS owner project
gcloud projects add-iam-policy-binding company-dns-prod \
  --member="serviceAccount:github-actions@agentnav-prod.iam.gserviceaccount.com" \
  --role="roles/dns.reader"
```

## Troubleshooting

| Issue | Solution |
|-------|----------|
| Domain mapping pending | Wait for DNS propagation (5-15 min) |
| DNS not resolving | Verify records created with trailing dot (`.`) |
| Permission denied | Grant `roles/dns.reader` in DNS project |
| Certificate pending | Wait up to 24 hours for certificate provisioning |

## Key Points

- ✅ Domain mapping creates automatically in Agent Navigator project
- ✅ DNS records must be created manually in DNS owner project
- ✅ Use `terraform output domain_mapping_dns_records` to get exact values
- ✅ Cloud Run manages TLS certificates automatically
- ✅ Cross-project IAM is optional (only for validation)

## Full Documentation

- [CROSS_PROJECT_DNS_SETUP.md](./CROSS_PROJECT_DNS_SETUP.md) - Complete guide
- [CUSTOM_DOMAIN_SETUP.md](./CUSTOM_DOMAIN_SETUP.md) - Same-project setup
