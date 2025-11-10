# Gen AI Prompt Management App - Deployment Guide

This document describes how to deploy the Gen AI Prompt Management App as a companion service to the Agentic Navigator system.

## Overview

The Gen AI Prompt Management App is a separate application that provides a user interface for managing and testing AI prompts. It integrates with the main Agentic Navigator backend and uses Supabase for authentication and data persistence.

### Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      Google Cloud Run                        │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────┐  │
│  │   Frontend   │  │   Backend    │  │  Prompt Mgmt App │  │
│  │  (React/TS)  │  │   (Python)   │  │  (Node/React)    │  │
│  │              │  │              │  │                  │  │
│  │  Port: 80    │  │  Port: 8080  │  │  Port: 80        │  │
│  └──────────────┘  └──────────────┘  └──────────────────┘  │
│                                                               │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
                   ┌──────────────────────┐
                   │   Google Services    │
                   ├──────────────────────┤
                   │ • Firestore          │
                   │ • Secret Manager     │
                   │ • Artifact Registry  │
                   └──────────────────────┘
                              │
                              ▼
                   ┌──────────────────────┐
                   │      Supabase        │
                   ├──────────────────────┤
                   │ • PostgreSQL DB      │
                   │ • Google OAuth       │
                   │ • Row Level Security │
                   └──────────────────────┘
```

## Prerequisites

Before deploying the Prompt Management App, ensure you have:

1. ✅ A Supabase project created
2. ✅ Google OAuth configured in Supabase (see [SUPABASE_GOOGLE_OAUTH_SETUP.md](./SUPABASE_GOOGLE_OAUTH_SETUP.md))
3. ✅ Terraform infrastructure provisioned (automatic via CI/CD)
4. ✅ The Prompt Management App repository cloned
5. ✅ Container image built and pushed to Artifact Registry

## Repository Structure

The Prompt Management App is maintained in a separate repository: https://github.com/stevei101/Genaipromptmanagementapp

However, the deployment infrastructure is managed within this repository (`stevei101/agentnav`) to maintain consistency with the existing CI/CD pipeline.

## Infrastructure Components

### 1. Service Account

**Resource:** `google_service_account.cloud_run_prompt_mgmt`

- **Account ID:** `agentnav-prompt-mgmt`
- **Purpose:** Identity for the Cloud Run service
- **Permissions:**
  - `roles/secretmanager.secretAccessor` - Access Supabase secrets
  - `roles/run.invoker` - Invoke Cloud Run services

### 2. Supabase Secrets

**Resources:**

- `google_secret_manager_secret.supabase_url`
- `google_secret_manager_secret.supabase_anon_key`
- `google_secret_manager_secret.supabase_service_key`

**Location:** Google Secret Manager

**Setup Instructions:**

```bash
# Set your GCP project ID
export PROJECT_ID="your-gcp-project-id"

# Add Supabase URL
echo -n "https://your-project-ref.supabase.co" | \
  gcloud secrets versions add SUPABASE_URL --data-file=- --project=$PROJECT_ID

# Add Supabase Anonymous Key
echo -n "your-anon-key-here" | \
  gcloud secrets versions add SUPABASE_ANON_KEY --data-file=- --project=$PROJECT_ID

# Add Supabase Service Key (KEEP THIS SECRET!)
echo -n "your-service-role-key-here" | \
  gcloud secrets versions add SUPABASE_SERVICE_KEY --data-file=- --project=$PROJECT_ID
```

### 3. Cloud Run Service

**Resource:** `google_cloud_run_v2_service.prompt_mgmt`

- **Service Name:** `prompt-management-app`
- **Region:** `us-central1` (same as frontend)
- **Container Port:** `80`
- **Scaling:**
  - Min instances: 0 (scale to zero)
  - Max instances: 10
- **Resources:**
  - CPU: 1 vCPU
  - Memory: 512Mi

**Environment Variables:**

- `PORT` - Container port (set by Cloud Run)
- `NEXT_PUBLIC_SUPABASE_URL` - Supabase project URL (from Secret Manager)
- `NEXT_PUBLIC_SUPABASE_ANON_KEY` - Supabase anonymous key (from Secret Manager)
- `SUPABASE_SERVICE_KEY` - Supabase service role key (from Secret Manager)
- `ENVIRONMENT` - Deployment environment (prod/staging/dev)

## Deployment Methods

### Option 1: Manual Deployment (One-time Setup)

If you need to deploy manually before CI/CD is configured:

```bash
# 1. Set variables
export PROJECT_ID="your-gcp-project-id"
export REGION="us-central1"
export IMAGE_TAG="latest"  # Or specific version

# 2. Build and push container (from the prompt management app repo)
cd /path/to/prompt-management-app
podman build -t prompt-management-app:$IMAGE_TAG .
podman tag prompt-management-app:$IMAGE_TAG \
  $REGION-docker.pkg.dev/$PROJECT_ID/agentnav-containers/prompt-management-app:$IMAGE_TAG
podman push $REGION-docker.pkg.dev/$PROJECT_ID/agentnav-containers/prompt-management-app:$IMAGE_TAG

# 3. Deploy to Cloud Run
gcloud run deploy prompt-management-app \
  --image=$REGION-docker.pkg.dev/$PROJECT_ID/agentnav-containers/prompt-management-app:$IMAGE_TAG \
  --region=$REGION \
  --platform=managed \
  --port=80 \
  --timeout=300s \
  --service-account=agentnav-prompt-mgmt@$PROJECT_ID.iam.gserviceaccount.com \
  --set-secrets=NEXT_PUBLIC_SUPABASE_URL=SUPABASE_URL:latest,NEXT_PUBLIC_SUPABASE_ANON_KEY=SUPABASE_ANON_KEY:latest,SUPABASE_SERVICE_KEY=SUPABASE_SERVICE_KEY:latest \
  --allow-unauthenticated
```

### Option 2: Automated Deployment via CI/CD (Recommended)

The CI/CD pipeline automatically deploys the Prompt Management App when changes are pushed to the repository.

**GitHub Actions Workflow Steps:**

1. Authenticate to GCP using Workload Identity Federation
2. Build the container image using Podman
3. Tag with commit SHA
4. Push to Artifact Registry
5. Deploy to Cloud Run with Terraform-managed configuration

**Required GitHub Secrets:**

Add these to your GitHub repository settings:

| Secret Name            | Description               |
| ---------------------- | ------------------------- |
| `SUPABASE_URL`         | Supabase project URL      |
| `SUPABASE_ANON_KEY`    | Supabase anonymous key    |
| `SUPABASE_SERVICE_KEY` | Supabase service role key |

## Local Development

For local development of the Prompt Management App:

### 1. Clone the Repository

```bash
git clone https://github.com/stevei101/Genaipromptmanagementapp.git
cd Genaipromptmanagementapp
```

### 2. Set Up Environment Variables

Create a `.env` file:

```bash
# Supabase Configuration
NEXT_PUBLIC_SUPABASE_URL=https://your-project-ref.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=your-anon-key-here
SUPABASE_SERVICE_KEY=your-service-role-key-here

# Backend API URL (for integration with agentnav)
NEXT_PUBLIC_API_URL=http://localhost:8080
```

### 3. Install Dependencies

```bash
bun install
```

### 4. Run Development Server

```bash
bun run dev
```

The app will be available at `http://localhost:3000`

### 5. Testing with Agentnav Backend

To test integration with the agentnav backend:

```bash
# Terminal 1: Start agentnav backend
cd /path/to/agentnav
make up

# Terminal 2: Start prompt management app
cd /path/to/Genaipromptmanagementapp
bun run dev
```

## Testing the Deployment

### 1. Verify Service is Running

```bash
# Get service URL
gcloud run services describe prompt-management-app \
  --region=us-central1 \
  --format='value(status.url)'

# Test health endpoint (if available)
curl https://your-service-url.run.app/health
```

### 2. Test Google OAuth Flow

1. Navigate to the service URL
2. Click "Sign in with Google"
3. Complete the OAuth flow
4. Verify you're redirected back and logged in
5. Check Supabase dashboard for new user entry

### 3. Verify Secret Access

Check Cloud Run logs to ensure secrets are loaded:

```bash
gcloud run services logs read prompt-management-app \
  --region=us-central1 \
  --limit=50
```

Look for log entries confirming Supabase connection.

## Monitoring and Debugging

### View Logs

```bash
# Recent logs
gcloud run services logs read prompt-management-app \
  --region=us-central1 \
  --limit=100

# Follow logs in real-time
gcloud run services logs tail prompt-management-app \
  --region=us-central1
```

### Common Issues

#### Issue: "Supabase URL not configured"

**Solution:** Verify secrets are populated in Secret Manager:

```bash
gcloud secrets versions access latest --secret=SUPABASE_URL
```

#### Issue: OAuth redirect fails

**Solution:**

1. Verify the redirect URI in Google Cloud Console matches Supabase callback URL
2. Check Supabase logs: Dashboard > Logs > Auth Logs

#### Issue: Service won't start

**Solution:**

1. Check the container logs for errors
2. Verify the container image was built correctly
3. Ensure the PORT environment variable is being read

## Security Considerations

### 1. Secret Management

✅ **DO:**

- Store all secrets in Google Secret Manager
- Use IAM to control access to secrets
- Rotate secrets regularly

❌ **DON'T:**

- Commit secrets to Git
- Share service role keys
- Use secrets in client-side code (except anon key)

### 2. Authentication

✅ **DO:**

- Enable Row Level Security (RLS) in Supabase
- Use the service role key only in server-side code
- Implement proper authorization checks

❌ **DON'T:**

- Expose the service role key in the browser
- Skip RLS policy configuration
- Trust client-side authentication alone

### 3. Network Security

✅ **DO:**

- Use HTTPS for all communication (provided by Cloud Run)
- Enable CORS only for trusted origins
- Implement rate limiting

## Updating the Deployment

### Update Secrets

```bash
# Update a secret
echo -n "new-secret-value" | \
  gcloud secrets versions add SUPABASE_URL --data-file=-

# Cloud Run will automatically use the new version
```

### Update Container Image

```bash
# Build new version
podman build -t prompt-management-app:v2 .

# Tag and push
podman tag prompt-management-app:v2 \
  us-central1-docker.pkg.dev/$PROJECT_ID/agentnav-containers/prompt-management-app:v2
podman push us-central1-docker.pkg.dev/$PROJECT_ID/agentnav-containers/prompt-management-app:v2

# Update service
gcloud run services update prompt-management-app \
  --image=us-central1-docker.pkg.dev/$PROJECT_ID/agentnav-containers/prompt-management-app:v2 \
  --region=us-central1
```

### Rollback Deployment

```bash
# List revisions
gcloud run revisions list --service=prompt-management-app --region=us-central1

# Rollback to previous revision
gcloud run services update-traffic prompt-management-app \
  --to-revisions=REVISION_NAME=100 \
  --region=us-central1
```

## Cost Optimization

### Scale to Zero

The service is configured to scale to zero when not in use, minimizing costs:

```yaml
scaling:
  min_instance_count: 0
  max_instance_count: 10
```

### Resource Limits

Resources are set conservatively:

```yaml
resources:
  cpu: 1
  memory: 512Mi
```

Adjust based on actual usage patterns.

### Monitoring Costs

```bash
# View service metrics
gcloud run services describe prompt-management-app \
  --region=us-central1 \
  --format='yaml(status.traffic)'
```

## Additional Resources

- [Supabase Google OAuth Setup Guide](./SUPABASE_GOOGLE_OAUTH_SETUP.md)
- [GCP Setup Guide](./GCP_SETUP_GUIDE.md)
- [Agentic Navigator Documentation](../README.md)
- [Supabase Documentation](https://supabase.com/docs)
- [Cloud Run Documentation](https://cloud.google.com/run/docs)

## Support

For issues or questions:

1. Check the [troubleshooting section](#monitoring-and-debugging)
2. Review Cloud Run logs
3. Check Supabase dashboard logs
4. Open an issue in the GitHub repository

---

**Last Updated:** 2025-11-04
