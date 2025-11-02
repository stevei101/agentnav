# Security Policy

## Supported Versions

We release patches for security vulnerabilities. The following versions are currently being supported with security updates:

| Version | Supported          |
| ------- | ------------------ |
| Latest  | :white_check_mark: |
| < Latest| :x:                |

## Reporting a Vulnerability

**Please do not report security vulnerabilities through public GitHub issues.**

Instead, please report them privately using one of the following methods:

### GitHub Security Advisories (Recommended)

1. Go to the [Security tab](https://github.com/stevei101/agentnav/security) of this repository
2. Click "Report a vulnerability"
3. Fill out the vulnerability report form with as much detail as possible

### Email Reporting

Alternatively, you can email security reports to the maintainers. Please include:

1. **Type of vulnerability**: (e.g., XSS, SQL injection, authentication bypass, etc.)
2. **Full paths of affected source files**
3. **Location of the affected source code**: (tag/branch/commit or direct URL)
4. **Step-by-step instructions to reproduce the issue**
5. **Proof-of-concept or exploit code** (if possible)
6. **Impact of the issue**: What an attacker might be able to do

### What to Expect

- **Acknowledgment**: We will acknowledge receipt of your vulnerability report within 48 hours.
- **Communication**: We will keep you informed about our progress as we work on a fix.
- **Timeline**: We aim to release a fix within 90 days of disclosure for most vulnerabilities.
- **Credit**: With your permission, we will credit you in the security advisory and release notes.

## Security Best Practices

When contributing to or using Agentic Navigator, please follow these security best practices:

### API Keys and Secrets

- **Never commit API keys or secrets** to the repository
- Use environment variables (`.env` files) for local development
- Store production secrets in **Google Secret Manager**
- The `.env.example` file should only contain placeholders, never real values

### Cloud Run Security

- All services use **Workload Identity (WI)** for authentication to Google Cloud services
- No service account JSON keys are stored in containers
- Secrets are injected at runtime from Secret Manager
- All HTTP traffic is automatically encrypted with TLS/HTTPS

### Dependency Security

- We use automated dependency scanning via **OSV-Scanner** in our CI/CD pipeline
- Keep dependencies up to date
- Review security advisories for all dependencies
- Run `make test` before submitting pull requests

### Infrastructure Security

- All infrastructure is defined as code using **Terraform**
- **TFSec** scans Terraform code for security issues in CI/CD
- Follow the principle of least privilege for IAM roles
- Use **Workload Identity Federation (WIF)** for GitHub Actions authentication

### Code Security

- Input validation is required for all user inputs
- Use parameterized queries to prevent injection attacks
- Sanitize outputs to prevent XSS
- Follow OWASP best practices
- Run security linters before committing code

## Known Security Features

### GitHub Secret Scanning

This repository has GitHub Secret Scanning enabled to detect accidentally committed secrets in:
- Current code
- Pull requests
- Historical commits

If a secret is detected, it will be flagged and should be:
1. Rotated immediately
2. Removed from git history if possible
3. Added to `.gitignore` to prevent future commits

### CI/CD Security Checks

Every pull request runs the following security checks:

1. **TFSec**: Terraform security scanning
2. **OSV-Scanner**: Dependency vulnerability scanning
3. **Linting**: Code quality and security linting
4. **Tests**: Unit and integration tests

All checks must pass before merging.

## Vulnerability Disclosure Policy

We follow a **coordinated disclosure** approach:

1. **Private Disclosure**: Report vulnerabilities privately as described above
2. **Investigation**: We investigate and develop a fix
3. **Patch Development**: We develop and test a security patch
4. **Coordinated Release**: We coordinate the release with you
5. **Public Disclosure**: After the patch is released, we publish a security advisory

We request that you:
- Give us a reasonable amount of time to fix the issue before public disclosure
- Do not exploit the vulnerability beyond what is necessary to demonstrate it
- Do not access, modify, or delete data belonging to others
- Act in good faith to avoid privacy violations and service disruption

## Security Updates

Security updates will be:
- Released as soon as possible after a vulnerability is confirmed
- Announced through GitHub Security Advisories
- Included in release notes with appropriate credit

Subscribe to repository notifications to stay informed about security updates.

## Additional Resources

- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
- [Google Cloud Security Best Practices](https://cloud.google.com/security/best-practices)
- [GitHub Security Features](https://github.com/features/security)
- [Cloud Run Security](https://cloud.google.com/run/docs/securing/securing-services)

## Questions?

If you have questions about security that don't involve reporting a vulnerability, please:
- Open a GitHub issue with the `security` label
- Refer to our [Contributing Guide](CONTRIBUTING.md)

## Thank You

We appreciate the security research community's efforts in responsibly disclosing vulnerabilities. Your contributions help keep Agentic Navigator and its users safe.
