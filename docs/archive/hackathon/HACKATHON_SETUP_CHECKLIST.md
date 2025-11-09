# Quick Setup Checklist for Hackathon

Use this checklist to quickly set up your GCP project for the hackathon.

## ? Setup Checklist

### 1. Google Cloud Project

- [ ] Create GCP project: `agentic-navigator` (or your name)
- [ ] Set project as default: `gcloud config set project PROJECT_ID`
- [ ] Note your project ID: `_______________________________`

### 2. Enable APIs

```bash
gcloud services enable \
  firestore.googleapis.com \
  run.googleapis.com \
  cloudbuild.googleapis.com \
  artifactregistry.googleapis.com \
  secretmanager.googleapis.com
```

### 3. Firestore Database

- [ ] Create Firestore database (Native mode)
- [ ] Choose location: `us-central1` (or your preferred region)
- [ ] Database created: `[ ] Yes`

### 4. Gemini API Key

- [ ] Go to: https://aistudio.google.com/app/apikey
- [ ] Create API key
- [ ] Copy API key: `_______________________________`
- [ ] (Optional) Store in Secret Manager

### 5. Service Account

```bash
gcloud iam service-accounts create agentnav-service \
  --display-name="Agentic Navigator Service Account"
```

### 6. gcloud SDK Setup

```bash
gcloud auth login
gcloud auth application-default login
gcloud config set project YOUR_PROJECT_ID
```

### 7. Firestore Emulator

```bash
npm install -g firebase-tools  # or use gcloud components
firebase login
firebase init firestore
```

### 8. Environment Variables

- [ ] Create `.env` file
- [ ] Add `GEMINI_API_KEY=your_key_here`
- [ ] Add `FIRESTORE_PROJECT_ID=your_project_id`

### 9. Test Setup

```bash
make setup    # Build and start services
make health   # Check service health
```

### 10. Verify

- [ ] Frontend accessible: http://localhost:3000
- [ ] Backend accessible: http://localhost:8080
- [ ] Firestore UI accessible: http://localhost:4000
- [ ] Health check works: http://localhost:8080/healthz

---

## ?? Quick Commands

```bash
# One-time setup
make setup

# Daily development
make up          # Start services
make logs        # View logs
make down        # Stop services

# Testing
make test        # Run tests
make health      # Check health

# Cleanup
make clean       # Remove everything
```

---

## ?? Important Values to Save

- **Project ID:** `_______________________________`
- **Project Number:** `_______________________________`
- **Gemini API Key:** `_______________________________`
- **Firestore Location:** `_______________________________`

---

## ?? Common Issues

**"API not enabled"**
? Run: `gcloud services enable API_NAME.googleapis.com`

**"Permission denied"**
? Run: `gcloud auth login && gcloud auth application-default login`

**"Port already in use"**
? Run: `lsof -i :8080` and kill process if needed

---

**Full guide:** See `docs/GCP_SETUP_GUIDE.md` for detailed instructions.
