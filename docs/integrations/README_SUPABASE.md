# Supabase Authentication Documentation

## Overview

This directory contains documentation for implementing Supabase Google OAuth authentication for the Gen AI Prompt Management App companion service.

## Documentation Files

### 1. [SUPABASE_GOOGLE_OAUTH_SETUP.md](./SUPABASE_GOOGLE_OAUTH_SETUP.md)

**Purpose:** Complete setup guide for configuring Google OAuth in Supabase

**Contents:**

- Prerequisites checklist
- Google Cloud Project configuration (OAuth 2.0 credentials)
- Supabase dashboard configuration
- Environment variable setup (local, GitHub Secrets, GCP Secret Manager)
- Frontend implementation examples
- Testing procedures
- Troubleshooting guide
- Security best practices

**Target Audience:** Developers setting up authentication for the first time

**Estimated Time:** 30-45 minutes to complete setup

---

### 2. [PROMPT_MANAGEMENT_APP_DEPLOYMENT.md](./PROMPT_MANAGEMENT_APP_DEPLOYMENT.md)

**Purpose:** Deployment guide for the Prompt Management App to Cloud Run

**Contents:**

- Architecture overview
- Infrastructure components (Terraform resources)
- Deployment methods (manual and automated)
- Local development setup
- Testing and monitoring
- Security considerations
- Cost optimization tips

**Target Audience:** DevOps engineers and developers deploying to GCP

**Estimated Time:** 1-2 hours for initial deployment

---

## Quick Start

### For Developers

If you want to get started quickly with Supabase authentication:

1. **Read:** [SUPABASE_GOOGLE_OAUTH_SETUP.md](./SUPABASE_GOOGLE_OAUTH_SETUP.md)
2. **Follow:** The step-by-step guide in that document
3. **Test:** Use the testing section to verify your setup

### For DevOps/Platform Engineers

If you're deploying the Prompt Management App:

1. **Read:** [PROMPT_MANAGEMENT_APP_DEPLOYMENT.md](./PROMPT_MANAGEMENT_APP_DEPLOYMENT.md)
2. **Review:** The Terraform infrastructure changes in `terraform/` directory
3. **Run:** The infrastructure tests: `terraform/tests/test_supabase_infrastructure.sh`

---

## Related Documentation

### Infrastructure

- **Terraform Configuration:** `../terraform/cloud_run.tf`, `secret_manager.tf`, `iam.tf`
- **Infrastructure Tests:** `../terraform/tests/test_supabase_infrastructure.sh`
- **Environment Template:** `../.env.example`

### System Documentation

- **[GCP_SETUP_GUIDE.md](./GCP_SETUP_GUIDE.md)** - General GCP setup
- **[GITHUB_SECRETS_TO_GCP_GUIDE.md](./GITHUB_SECRETS_TO_GCP_GUIDE.md)** - Secrets management
- **[CI/CD Documentation](./CONTRIBUTION_GUIDE_PR_DISCIPLINE.md)** - CI/CD pipeline

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│              Google Cloud Platform (GCP)                     │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  ┌────────────────┐  ┌────────────────┐  ┌───────────────┐ │
│  │  Agentnav      │  │  Agentnav      │  │  Prompt Mgmt  │ │
│  │  Frontend      │  │  Backend       │  │  App          │ │
│  │  (React/TS)    │  │  (Python)      │  │  (Node/React) │ │
│  └────────────────┘  └────────────────┘  └───────────────┘ │
│                                                               │
│  ┌────────────────────────────────────────────────────────┐ │
│  │  Google Secret Manager                                  │ │
│  │  - GEMINI_API_KEY                                       │ │
│  │  - SUPABASE_URL                                         │ │
│  │  - SUPABASE_ANON_KEY                                    │ │
│  │  - SUPABASE_SERVICE_KEY                                 │ │
│  └────────────────────────────────────────────────────────┘ │
│                                                               │
└─────────────────────────────────────────────────────────────┘
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

---

## Key Features

✅ **Google OAuth Integration** - Users can sign in with their Google account  
✅ **Secure Secret Management** - All secrets stored in GCP Secret Manager  
✅ **Infrastructure as Code** - Terraform manages all resources  
✅ **Automated Deployment** - CI/CD pipeline deploys to Cloud Run  
✅ **Comprehensive Testing** - 13 infrastructure tests ensure correctness  
✅ **Production-Ready** - Security best practices built-in

---

## Prerequisites

Before using this documentation, ensure you have:

- ✅ A Google Cloud Project
- ✅ A Supabase account and project
- ✅ Access to GitHub repository settings (for secrets)
- ✅ Basic familiarity with OAuth 2.0 concepts
- ✅ Terraform installed (for infrastructure changes)

---

## Support

### Common Issues

**Issue:** OAuth redirect fails  
**Solution:** Verify the redirect URI in Google Cloud Console matches the Supabase callback URL exactly

**Issue:** Secrets not loading in Cloud Run  
**Solution:** Check IAM permissions and verify secrets exist in Secret Manager

**Issue:** Build fails in CI/CD  
**Solution:** Ensure all GitHub Secrets are configured correctly

### Getting Help

1. Check the troubleshooting sections in each guide
2. Review the infrastructure tests output
3. Open an issue on GitHub with detailed error logs

---

## Contributing

When adding or modifying authentication features:

1. Update this documentation
2. Add/update infrastructure tests in `terraform/tests/`
3. Validate Terraform configuration: `terraform validate`
4. Run tests: `bash terraform/tests/test_supabase_infrastructure.sh`
5. Update `.env.example` if new environment variables are needed

---

## Security

**Important Security Notes:**

- Never commit secrets to Git
- Use Secret Manager for all production secrets
- Rotate secrets regularly
- Enable Row Level Security (RLS) in Supabase
- Follow the principle of least privilege for service accounts

See [SUPABASE_GOOGLE_OAUTH_SETUP.md](./SUPABASE_GOOGLE_OAUTH_SETUP.md) for detailed security best practices.

---

## Next Steps

After completing the setup:

1. ✅ Deploy the Prompt Management App to Cloud Run
2. ✅ Test the OAuth flow end-to-end
3. ✅ Configure Row Level Security policies in Supabase
4. ✅ Monitor logs and usage
5. ✅ Set up alerting for authentication failures

---

**Last Updated:** 2025-11-04  
**Version:** 1.0  
**Status:** Production Ready
