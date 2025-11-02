# Workload Identity vs Workload Identity Federation - Clarification

## Summary

Based on expert review, the project uses **two distinct identity mechanisms** that serve different purposes:

## 1. Workload Identity Federation (WIF) - For CI/CD

**Purpose:** Secure authentication for GitHub Actions to access GCP during deployment.

**Where Used:** GitHub Actions runner (CI/CD pipeline)

**How It Works:**

- GitHub Actions uses WIF to impersonate a GCP Service Account (the "Deployment Service Account")
- Eliminates need for static, long-lived Service Account JSON keys stored as GitHub Secrets
- Access is temporary, tied to GitHub Action runtime, and revocable
- Required IAM roles: `roles/run.admin` (deploy Cloud Run), `roles/artifactregistry.writer` (push containers)

**Setup:** Configured via Terraform (FR#007)

**Benefits:**

- ? No static credentials in GitHub Secrets
- ? Improved security posture
- ? Temporary, scoped access
- ? Modern best practice for CI/CD

---

## 2. Workload Identity (WI) - For Cloud Run Services

**Purpose:** Secure authentication for running Cloud Run services to access other GCP services.

**Where Used:** Running Cloud Run containers (backend, frontend, gemma-service)

**How It Works:**

- Each Cloud Run service has a built-in Service Account (defaults to Compute Engine default Service Account, or custom Service Account)
- By granting this Service Account minimum necessary IAM roles, the running code automatically authenticates
- No API keys, Service Account JSON files, or credential files needed in the container
- Fully managed by GCP

**Required IAM Roles:**

- Backend Service Account:
  - `roles/datastore.user` (Firestore read/write)
  - `roles/secretmanager.secretAccessor` (Secret Manager access)
- Gemma Service Account:
  - `roles/secretmanager.secretAccessor` (if accessing Secret Manager)
  - Custom IAM policy for A2A communication (if restricting to backend Service Account only)

**Benefits:**

- ? No credentials in container images
- ? Automatic authentication
- ? Least-privilege access via IAM roles
- ? Standard Cloud Run best practice

---

## Summary Table

| Identity Mechanism                     | Where Used            | Purpose                                            | Setup Method                          |
| :------------------------------------- | :-------------------- | :------------------------------------------------- | :------------------------------------ |
| **Workload Identity Federation (WIF)** | GitHub Actions Runner | CI/CD authentication (deploy, push containers)     | Terraform (FR#007)                    |
| **Workload Identity (WI)**             | Cloud Run Services    | Runtime authentication (Firestore, Secret Manager) | Terraform (Service Account IAM roles) |

**Both are necessary** and represent modern GCP security best practices.

---

## Documentation Updates

Updated files to reflect this distinction:

- ? `docs/SYSTEM_INSTRUCTION.md` - Added comprehensive "Identity & Authentication Architecture" section
- ? `.github/agents/agentnav-gh-copilot-agent.md` - Updated infrastructure table

---

## Key Takeaway

- **WIF** = CI/CD authentication (GitHub Actions ? GCP)
- **WI** = Runtime authentication (Cloud Run service ? other GCP services)

Both are critical for a secure, modern GCP deployment.
