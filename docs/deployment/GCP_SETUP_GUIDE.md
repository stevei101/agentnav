# Google Cloud Console & gcloud SDK Setup Guide

## For Agentic Navigator Hackathon Project

This guide walks you through setting up Google Cloud Platform (GCP) and Firebase/Firestore for your hackathon project.

---

## Prerequisites

1. **Google Cloud Account** - Sign up at https://cloud.google.com/free (Free tier available)
2. **gcloud SDK** - Install from https://cloud.google.com/sdk/docs/install
3. **Billing Account** (may be required for some APIs, but hackathon credits often provided)

---

## Step 1: Create a New GCP Project

### Option A: Via Google Cloud Console (Web UI)

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Click the project dropdown at the top
3. Click **"New Project"**
4. Enter project details:
   - **Project Name:** `agentic-navigator` (or your preferred name)
   - **Organization:** (if applicable)
   - **Location:** (if applicable)
5. Click **"Create"**
6. Wait for project creation (may take a minute)
7. **Select the new project** from the dropdown

### Option B: Via gcloud SDK

```bash
# List available projects
gcloud projects list

# Create new project
gcloud projects create agentic-navigator \
  --name="Agentic Navigator" \
  --set-as-default

# Set the project as active
gcloud config set project agentic-navigator
```

**Note:** Replace `agentic-navigator` with your desired project ID (must be globally unique).

---

## Step 2: Enable Required APIs

### Via Cloud Console

1. Go to [APIs & Services > Library](https://console.cloud.google.com/apis/library)
2. Enable the following APIs (search and click "Enable"):
   - ? **Cloud Firestore API**
   - ? **Cloud Run API**
   - ? **Cloud Build API**
   - ? **Artifact Registry API**
   - ? **Secret Manager API**
   - ? **Cloud DNS API** (if using custom domain)
   - ? **Cloud Logging API**
   - ? **Cloud Monitoring API**

### Via gcloud SDK

```bash
# Enable all required APIs at once
gcloud services enable \
  firestore.googleapis.com \
  run.googleapis.com \
  cloudbuild.googleapis.com \
  artifactregistry.googleapis.com \
  secretmanager.googleapis.com \
  dns.googleapis.com \
  logging.googleapis.com \
  monitoring.googleapis.com

# Verify enabled APIs
gcloud services list --enabled
```

---

## Step 3: Set Up Firestore Database

### Via Cloud Console

1. Go to [Firestore](https://console.cloud.google.com/firestore)
2. Click **"Create Database"**
3. Choose **"Native mode"** (recommended for new projects)
4. Select **Location**:
   - **For Hackathon:** Choose closest region (e.g., `us-central`, `us-east1`, `europe-west1`)
   - **Important:** This cannot be changed later!
5. Click **"Create"**
6. Wait for database creation (~1-2 minutes)

### Via gcloud SDK

```bash
# Create Firestore database in Native mode
gcloud firestore databases create \
  --location=us-central \
  --type=firestore-native

# Or for regional (better performance)
gcloud firestore databases create \
  --location=us-central1 \
  --type=firestore-native
```

**Available Locations:**

- `us-central` (Iowa) - Multi-region
- `us-east1` (South Carolina)
- `europe-west1` (Belgium)
- `asia-northeast1` (Tokyo)

---

## Step 4: Create Firestore Collections (Optional)

You can create collections via:

- **Cloud Console:** [Firestore Data](https://console.cloud.google.com/firestore/data)
- **gcloud SDK:** Not directly supported (use REST API or Cloud Console)

**Recommended Collections** (based on your SYSTEM_INSTRUCTION.md):

- `sessions/` - User session data
- `knowledge_cache/` - Cached analysis results
- `agent_context/` - Shared agent context

**Note:** Firestore creates collections automatically when you write data, so this is optional.

---

## Step 5: Get Gemini API Key

### Via Google AI Studio

1. Go to [Google AI Studio](https://aistudio.google.com/app/apikey)
2. Click **"Create API Key"**
3. Select your project: `agentic-navigator`
4. Copy the API key (starts with `AIza...`)
5. **Save it securely** - you'll need it for `.env` file

### Store in Secret Manager (Recommended)

```bash
# Store Gemini API key in Secret Manager
echo -n "YOUR_GEMINI_API_KEY_HERE" | gcloud secrets create GEMINI_API_KEY \
  --data-file=- \
  --replication-policy="automatic"

# Grant access to Cloud Run service account
gcloud secrets add-iam-policy-binding GEMINI_API_KEY \
  --member="serviceAccount:PROJECT_NUMBER-compute@developer.gserviceaccount.com" \
  --role="roles/secretmanager.secretAccessor"
```

---

## Step 6: Set Up Service Account for Cloud Run

### Create Service Account

```bash
# Create service account
gcloud iam service-accounts create agentnav-service \
  --display-name="Agentic Navigator Service Account" \
  --description="Service account for Agentic Navigator Cloud Run service"

# Grant necessary permissions
gcloud projects add-iam-policy-binding agentic-navigator \
  --member="serviceAccount:agentnav-service@agentic-navigator.iam.gserviceaccount.com" \
  --role="roles/firestore.user"

gcloud projects add-iam-policy-binding agentic-navigator \
  --member="serviceAccount:agentnav-service@agentic-navigator.iam.gserviceaccount.com" \
  --role="roles/secretmanager.secretAccessor"
```

**Replace `agentic-navigator` with your project ID.**

---

## Step 7: Configure gcloud SDK

### Initial Setup

```bash
# Authenticate
gcloud auth login

# Set default project
gcloud config set project agentic-navigator

# Set default region/zone
gcloud config set compute/region us-central1
gcloud config set compute/zone us-central1-a

# Configure application default credentials (for local development)
gcloud auth application-default login

# Verify configuration
gcloud config list
```

### Get Project Information

```bash
# Get project ID
gcloud config get-value project

# Get project number
gcloud projects describe $(gcloud config get-value project) --format="value(projectNumber)"

# List all projects
gcloud projects list
```

---

## Step 8: Set Up Firestore Emulator (Local Development)

### Install Emulator

```bash
# Firebase CLI (includes Firestore emulator) via bunx (no global install required)
bunx --bun firebase-tools@latest --help

# Or via gcloud SDK
gcloud components install beta cloud-firestore-emulator
```

### Initialize Firebase Project

```bash
# Login to Firebase
firebase login

# Initialize Firebase in your project directory
firebase init firestore

# Select:
# - Use existing project: agentic-navigator
# - Firestore rules file: firestore.rules (default)
# - Firestore indexes file: firestore.indexes.json (default)
```

### Start Firestore Emulator

```bash
# Start emulator
firebase emulators:start --only firestore

# Or via gcloud SDK
gcloud beta emulators firestore start \
  --host-port=localhost:8080 \
  --project=agentic-navigator
```

**Note:** Your `podman-compose.yml` already includes Firestore emulator configuration.

---

## Step 9: Create Firestore Security Rules

### Via Cloud Console

1. Go to [Firestore Rules](https://console.cloud.google.com/firestore/rules)
2. Click **"Edit Rules"**
3. Add rules (example for development):

```javascript
rules_version = '2';
service cloud.firestore {
  match /databases/{database}/documents {
    // Allow read/write during development (restrict for production!)
    match /{document=**} {
      allow read, write: if request.time < timestamp.date(2025, 12, 31);
    }

    // Production-ready rules (example)
    match /sessions/{sessionId} {
      allow read, write: if request.auth != null;
    }

    match /knowledge_cache/{cacheId} {
      allow read: if true;
      allow write: if request.auth != null;
    }
  }
}
```

4. Click **"Publish"**

### Via Firebase CLI

```bash
# Edit firestore.rules file in your project
# Then deploy
firebase deploy --only firestore:rules
```

---

## Step 10: Set Up Artifact Registry (For Container Images)

```bash
# Create Artifact Registry repository
gcloud artifacts repositories create agentnav-repo \
  --repository-format=docker \
  --location=us-central1 \
  --description="Agentic Navigator container images"

# Configure Docker/Podman authentication
gcloud auth configure-docker us-central1-docker.pkg.dev

# Verify
gcloud artifacts repositories list
```

---

## Step 11: Create .env File for Local Development

Create `.env` file in your project root:

```bash
# Copy template
cp .env.example .env

# Edit .env with your values
cat > .env << EOF
# Cloud Run Compatibility
PORT=8080

# Gemini API
GEMINI_API_KEY=YOUR_GEMINI_API_KEY_FROM_STEP_5

# Firestore
FIRESTORE_EMULATOR_HOST=firestore-emulator:8080
FIRESTORE_PROJECT_ID=agentic-navigator
FIRESTORE_DATABASE_ID=(default)

# Backend
BACKEND_URL=http://agentnav-backend:8080
ENVIRONMENT=development

# Frontend
VITE_API_URL=http://localhost:8080
VITE_GEMINI_API_KEY=YOUR_GEMINI_API_KEY_FROM_STEP_5

# Health Checks
HEALTH_CHECK_PATH=/healthz
EOF
```

**Replace:**

- `YOUR_GEMINI_API_KEY_FROM_STEP_5` with your actual Gemini API key
- `agentic-navigator` with your project ID

---

## Step 12: Verify Setup

### Test Firestore Connection

```bash
# Test with gcloud
gcloud firestore databases list

# Test with Firebase CLI
firebase firestore:indexes --project=agentic-navigator
```

### Test Local Emulator

```bash
# Start emulator
make up  # or: podman-compose up

# Check health
make health

# Access Firestore Emulator UI
open http://localhost:4000
```

---

## Quick Reference Commands

### Project Management

```bash
# Set active project
gcloud config set project PROJECT_ID

# Get current project
gcloud config get-value project

# List all projects
gcloud projects list
```

### Firestore

```bash
# List databases
gcloud firestore databases list

# Export data
gcloud firestore export gs://BUCKET_NAME

# Import data
gcloud firestore import gs://BUCKET_NAME/EXPORT_PATH
```

### Service Accounts

```bash
# List service accounts
gcloud iam service-accounts list

# Create key
gcloud iam service-accounts keys create key.json \
  --iam-account=SERVICE_ACCOUNT_EMAIL
```

### Secrets

```bash
# List secrets
gcloud secrets list

# Access secret value
gcloud secrets versions access latest --secret=GEMINI_API_KEY
```

---

## Hackathon-Specific Tips

### 1. Free Tier Limits

- **Firestore:** 50K reads/day, 20K writes/day (free tier)
- **Cloud Run:** 2 million requests/month (free tier)
- **Storage:** 1GB free storage

### 2. Cost Optimization

- Use Firestore emulator for local development
- Set up billing alerts in Cloud Console
- Monitor usage in [Cloud Console Billing](https://console.cloud.google.com/billing)

### 3. Debugging

```bash
# View Cloud Run logs
gcloud run logs read --service=agentnav-backend --region=us-central1

# View Firestore usage
gcloud firestore operations list

# Monitor API quotas
gcloud services list --enabled | grep firestore
```

### 4. Quick Reset

```bash
# If you need to start over
gcloud projects delete agentic-navigator  # Careful!
gcloud projects undelete agentic-navigator  # Within 30 days
```

---

## Troubleshooting

### Issue: "API not enabled"

```bash
# Enable the API
gcloud services enable API_NAME.googleapis.com
```

### Issue: "Permission denied"

```bash
# Check current user
gcloud auth list

# Re-authenticate
gcloud auth login
gcloud auth application-default login
```

### Issue: "Project not found"

```bash
# Verify project exists
gcloud projects list

# Set correct project
gcloud config set project PROJECT_ID
```

### Issue: "Firestore emulator not starting"

```bash
# Check if port is in use
lsof -i :8080
lsof -i :4000

# Kill process if needed
kill -9 PID

# Restart emulator
firebase emulators:start --only firestore
```

---

## Next Steps

1. ? Complete all steps above
2. ? Run `make setup` in your project directory
3. ? Verify services are running: `make health`
4. ? Start developing!

---

## Useful Links

- [Google Cloud Console](https://console.cloud.google.com/)
- [Firebase Console](https://console.firebase.google.com/)
- [Firestore Documentation](https://cloud.google.com/firestore/docs)
- [Cloud Run Documentation](https://cloud.google.com/run/docs)
- [gcloud CLI Reference](https://cloud.google.com/sdk/gcloud/reference)

---

**Need Help?** Check the [Cloud Run Hackathon Resources](https://run.devpost.com/resources) for additional guidance.
