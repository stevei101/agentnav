---
applies_to:
  - terraform/**/*
  - "*.tf"
  - scripts/deploy*.sh
  - scripts/setup*.sh
---

# Infrastructure & Terraform Instructions

## Technology Stack
- **Terraform 1.5+** for Infrastructure as Code (IaC)
- **Terraform Cloud** for state management and execution
- **Google Cloud Platform (GCP)** as cloud provider
- **Workload Identity Federation (WIF)** for secure GitHub Actions authentication
- **GitHub Actions** for CI/CD automation

## Terraform Best Practices

### Module Structure
- Use modules for reusable components
- Always use variables for configurable values
- Document all resources with comments
- Use data sources for existing resources
- Version lock providers

**Example:**
```hcl
# terraform/modules/cloud_run/main.tf
variable "service_name" {
  description = "Name of the Cloud Run service"
  type        = string
}

resource "google_cloud_run_service" "service" {
  name     = var.service_name
  location = var.region
  
  template {
    spec {
      containers {
        image = var.container_image
        
        # CRITICAL: Cloud Run sets PORT automatically
        env {
          name  = "PORT"
          value = "8080"
        }
      }
    }
  }
}
```

### State Management
- State stored in Terraform Cloud
- Never commit `.tfstate` files
- Use workspaces for environment separation (dev, staging, prod)
- Lock state during modifications

## GCP Infrastructure Components

### Cloud Run Services

#### Frontend Service
- **Region:** us-central1
- **CPU:** 1 vCPU
- **Memory:** 512Mi
- **Port:** 80 (Nginx)
- **Timeout:** 300s
- **Min Instances:** 0 (serverless scaling)

#### Backend Service
- **Region:** europe-west1
- **CPU:** 1 vCPU
- **Memory:** 1Gi
- **Port:** 8080
- **Timeout:** 300s
- **Min Instances:** 0

#### Gemma GPU Service
- **Region:** europe-west1
- **CPU:** GPU (NVIDIA L4)
- **GPU Type:** nvidia-l4
- **GPU Count:** 1
- **Memory:** 16Gi
- **Port:** 8080
- **Timeout:** 300s
- **Min Instances:** 0
- **Max Instances:** 2 (GPU instances are expensive)

**Example Terraform:**
```hcl
resource "google_cloud_run_service" "gemma_service" {
  name     = "gemma-service"
  location = "europe-west1"
  
  template {
    spec {
      containers {
        image = var.gemma_image
        
        resources {
          limits = {
            cpu    = "1"
            memory = "16Gi"
          }
        }
      }
      
      # GPU configuration
      node_selector = {
        "cloud.google.com/gke-accelerator" = "nvidia-l4"
      }
    }
    
    metadata {
      annotations = {
        "run.googleapis.com/gpu-type"  = "nvidia-l4"
        "run.googleapis.com/gpu-count" = "1"
      }
    }
  }
}
```

### Google Artifact Registry (GAR)
- Centralized container registry (replaces GCR)
- Store all Podman-built images
- Versioned with Git SHA tags
- Clean up old images with lifecycle policies

### Firestore
- NoSQL document database
- Collections: sessions, knowledge_cache, agent_context, agent_prompts
- Used for persistent session memory and agent state
- Configure indexes for common queries

### Secret Manager
- Store all sensitive credentials
- Never embed credentials in code/containers
- Secrets include:
  - GEMINI_API_KEY
  - FIRESTORE_CREDENTIALS
  - SUPABASE_URL, SUPABASE_ANON_KEY, SUPABASE_SERVICE_KEY

### Cloud DNS & TLS
- Domain: agentnav.lornu.com (or configured domain)
- TLS/SSL managed automatically by Cloud Run
- HTTPS-only enforcement

## Identity & Authentication

### Workload Identity Federation (WIF)
For GitHub Actions CI/CD authentication:
- GitHub Actions authenticates to GCP without static keys
- Service Account with roles: `run.admin`, `artifactregistry.writer`
- Configured in Terraform

**Example:**
```hcl
resource "google_iam_workload_identity_pool" "github_pool" {
  workload_identity_pool_id = "github-pool"
  display_name              = "GitHub Actions Pool"
}

resource "google_iam_workload_identity_pool_provider" "github_provider" {
  workload_identity_pool_id          = google_iam_workload_identity_pool.github_pool.workload_identity_pool_id
  workload_identity_pool_provider_id = "github-provider"
  
  attribute_mapping = {
    "google.subject"       = "assertion.sub"
    "attribute.repository" = "assertion.repository"
  }
  
  oidc {
    issuer_uri = "https://token.actions.githubusercontent.com"
  }
}
```

### Workload Identity (WI)
For Cloud Run service-to-service authentication:
- Running containers use built-in Service Accounts
- No credentials in container images
- Backend SA needs: `datastore.user`, `secretmanager.secretAccessor`

**Example:**
```hcl
resource "google_service_account" "backend_sa" {
  account_id   = "backend-service"
  display_name = "Backend Service Account"
}

resource "google_project_iam_member" "backend_firestore" {
  project = var.project_id
  role    = "roles/datastore.user"
  member  = "serviceAccount:${google_service_account.backend_sa.email}"
}
```

## CI/CD Pipeline

### GitHub Actions Workflow
1. Push code to GitHub
2. GitHub Actions workflow triggers
3. Authenticate via WIF
4. Terraform Cloud provisions/updates infrastructure
5. Podman builds container images, pushes to GAR
6. Deploy to Cloud Run

### Required GitHub Secrets
- `GCP_PROJECT_ID`
- `GEMINI_API_KEY`
- `TF_API_TOKEN`
- `TF_CLOUD_ORGANIZATION`
- `TF_WORKSPACE`
- `WIF_PROVIDER`
- `WIF_SERVICE_ACCOUNT`
- `SUPABASE_URL`, `SUPABASE_ANON_KEY`, `SUPABASE_SERVICE_KEY`

## Deployment Commands

### Deploy Frontend
```bash
gcloud run deploy agentnav-frontend \
  --image gcr.io/$PROJECT_ID/agentnav-frontend:$GITHUB_SHA \
  --region us-central1 \
  --platform managed \
  --port 80 \
  --timeout 300s
```

### Deploy Backend
```bash
gcloud run deploy agentnav-backend \
  --image gcr.io/$PROJECT_ID/agentnav-backend:$GITHUB_SHA \
  --region europe-west1 \
  --platform managed \
  --port 8080 \
  --timeout 300s \
  --set-env-vars PORT=8080,GEMINI_API_KEY=$GEMINI_API_KEY \
  --set-secrets GEMINI_API_KEY=GEMINI_API_KEY:latest
```

### Deploy Gemma GPU Service
```bash
gcloud run deploy gemma-service \
  --image $REGION-docker.pkg.dev/$PROJECT_ID/$GAR_REPO/gemma-service:$GITHUB_SHA \
  --region europe-west1 \
  --platform managed \
  --cpu gpu \
  --memory 16Gi \
  --gpu-type nvidia-l4 \
  --gpu-count 1 \
  --port 8080 \
  --timeout 300s
```

## Security Best Practices

1. **Secret Management:** Use Secret Manager, never embed credentials
2. **IAM:** Use least-privilege roles for all service accounts
3. **Authentication:** WIF for CI/CD, WI for runtime
4. **Encryption:** Enable encryption at rest for Firestore
5. **Network:** Use VPC Service Controls for sensitive resources

## Common Pitfalls

❌ **Mistake:** Embedding service account JSON keys in containers
✅ **Solution:** Use Workload Identity (WI) with Cloud Run Service Accounts

❌ **Mistake:** Using static keys in GitHub Secrets for CI/CD
✅ **Solution:** Use Workload Identity Federation (WIF)

❌ **Mistake:** Not setting PORT environment variable
✅ **Solution:** Always set PORT in Cloud Run service definition

❌ **Mistake:** Hardcoding project IDs or regions
✅ **Solution:** Use Terraform variables for all configurable values

## Monitoring & Observability

- Cloud Logging for all services
- Cloud Monitoring for metrics (latency, error rate, request count)
- Firestore metrics (read/write operations)
- Custom metrics via Cloud Monitoring API
- Set up alerts for critical failures

## Cost Optimization

- Set `min-instances=0` for services that can scale to zero
- Use GPU instances sparingly (expensive)
- Clean up old container images in GAR
- Set TTL on Firestore cached entries
- Monitor and optimize Cloud Run request durations
