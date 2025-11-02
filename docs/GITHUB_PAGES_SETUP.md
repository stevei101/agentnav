# GitHub Pages Setup Guide

This guide explains how to enable and configure GitHub Pages for the Agentic Navigator repository.

## Prerequisites

- Repository must be **public** (GitHub Pages is not available for private repositories on free plans)
- You must have **admin** access to the repository

## Setup Instructions

### Option 1: Using the docs/ Directory (Recommended)

This option serves the documentation directly from the `docs/` folder.

1. **Go to Repository Settings**
   - Navigate to https://github.com/stevei101/agentnav/settings

2. **Enable GitHub Pages**
   - Scroll down to the "Pages" section in the left sidebar
   - Under "Source", select **Deploy from a branch**
   - Under "Branch", select:
     - Branch: `main`
     - Folder: `/docs`
   - Click **Save**

3. **Wait for Deployment**
   - GitHub will automatically build and deploy your site
   - This usually takes 1-2 minutes
   - You'll see a notification when the site is live

4. **Access Your Documentation**
   - Your site will be available at: `https://stevei101.github.io/agentnav/`
   - GitHub will display the URL at the top of the Pages settings

### Option 2: Using GitHub Actions (Advanced)

For more control over the build process, you can use GitHub Actions to deploy to GitHub Pages.

1. **Create a GitHub Actions Workflow**

Create `.github/workflows/deploy-docs.yml`:

```yaml
name: Deploy Documentation to GitHub Pages

on:
  push:
    branches: [ main ]
    paths:
      - 'docs/**'
      - '.github/workflows/deploy-docs.yml'

permissions:
  contents: read
  pages: write
  id-token: write

jobs:
  deploy:
    runs-on: ubuntu-latest
    environment:
      name: github-pages
      url: ${{ steps.deployment.outputs.page_url }}
    steps:
      - name: Checkout
        uses: actions/checkout@v4

      - name: Setup Pages
        uses: actions/configure-pages@v4

      - name: Upload artifact
        uses: actions/upload-pages-artifact@v3
        with:
          path: 'docs'

      - name: Deploy to GitHub Pages
        id: deployment
        uses: actions/deploy-pages@v4
```

2. **Enable GitHub Pages with Actions**
   - Go to Settings → Pages
   - Under "Source", select **GitHub Actions**
   - The workflow will automatically deploy on push to main

## Documentation Structure

The `docs/` directory should contain:

```
docs/
├── index.html or README.md     # Landing page (auto-rendered by GitHub)
├── ARCHITECTURE_DIAGRAM_GUIDE.md
├── DUAL_CATEGORY_STRATEGY.md
├── GCP_SETUP_GUIDE.md
├── GPU_SETUP_GUIDE.md
├── HACKATHON_SUBMISSION_GUIDE.md
├── local-development.md
├── SECURITY.md                 # Copy from root (optional)
└── ... other documentation files
```

### Creating a Landing Page

GitHub Pages can automatically render Markdown files. However, for a custom landing page, create `docs/index.html`:

```html
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Agentic Navigator Documentation</title>
    <style>
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
            max-width: 800px;
            margin: 0 auto;
            padding: 2rem;
            line-height: 1.6;
        }
        h1 { color: #1a202c; }
        a { color: #3182ce; text-decoration: none; }
        a:hover { text-decoration: underline; }
        .doc-list { list-style: none; padding: 0; }
        .doc-list li { margin: 1rem 0; }
    </style>
</head>
<body>
    <h1>Agentic Navigator Documentation</h1>
    <p>Multi-agent knowledge explorer for complex documents and codebases.</p>
    
    <h2>Quick Links</h2>
    <ul class="doc-list">
        <li><a href="https://github.com/stevei101/agentnav">GitHub Repository</a></li>
        <li><a href="local-development.html">Local Development Guide</a></li>
        <li><a href="GCP_SETUP_GUIDE.html">GCP Setup Guide</a></li>
        <li><a href="GPU_SETUP_GUIDE.html">GPU Setup Guide</a></li>
        <li><a href="HACKATHON_SUBMISSION_GUIDE.html">Hackathon Submission Guide</a></li>
    </ul>
    
    <h2>Architecture</h2>
    <ul class="doc-list">
        <li><a href="SYSTEM_INSTRUCTION.html">System Architecture</a></li>
        <li><a href="DUAL_CATEGORY_STRATEGY.html">Multi-Agent Strategy</a></li>
        <li><a href="ARCHITECTURE_DIAGRAM_GUIDE.html">Architecture Diagram Guide</a></li>
    </ul>
</body>
</html>
```

## Custom Domain (Optional)

If you want to use a custom domain (e.g., `docs.agentnav.com`):

1. **Add CNAME File**

Create `docs/CNAME` with your domain:
```
docs.agentnav.com
```

2. **Configure DNS**
   - Add a CNAME record pointing to `stevei101.github.io`
   - Or add A records pointing to GitHub's IP addresses:
     ```
     185.199.108.153
     185.199.109.153
     185.199.110.153
     185.199.111.153
     ```

3. **Enable HTTPS**
   - GitHub Pages automatically provides HTTPS for custom domains
   - It may take a few hours for the certificate to be issued

## Jekyll Configuration (Optional)

GitHub Pages uses Jekyll by default. To customize:

1. **Create `docs/_config.yml`:**

```yaml
title: Agentic Navigator
description: Multi-agent AI system for knowledge exploration
theme: minima
# or use a GitHub-supported theme:
# theme: jekyll-theme-cayman

# Exclude files from processing
exclude:
  - README.md
  - LICENSE

# Markdown processor
markdown: kramdown
```

2. **Disable Jekyll (if using plain HTML/Markdown):**

Create `docs/.nojekyll` (empty file):
```bash
touch docs/.nojekyll
```

## Verification

After setup, verify your GitHub Pages site:

1. **Check Deployment Status**
   - Go to Settings → Pages
   - Look for the green checkmark and URL

2. **View Site**
   - Visit `https://stevei101.github.io/agentnav/`
   - Verify all documentation pages are accessible

3. **Check Actions (if using GitHub Actions)**
   - Go to Actions tab
   - Verify the "Deploy Documentation" workflow succeeds

## Troubleshooting

### Site Not Building

- **Check the Actions tab** for build errors
- Ensure the `docs/` folder exists and contains valid files
- Verify the branch and folder settings are correct

### 404 Errors

- Check file paths are correct (case-sensitive)
- Ensure `index.html` or `README.md` exists in `docs/`
- Wait a few minutes for deployment to complete

### Custom Domain Not Working

- Verify DNS records are correct
- Check that `CNAME` file contains only the domain name
- Wait up to 24 hours for DNS propagation
- Verify HTTPS certificate is issued (may take a few hours)

## Best Practices

1. **Keep Documentation Up to Date**
   - Update docs when making code changes
   - Review documentation in pull requests

2. **Use Relative Links**
   - Link between documentation pages with relative paths
   - Example: `[Setup Guide](GCP_SETUP_GUIDE.md)`

3. **Include Navigation**
   - Add a navigation menu to your landing page
   - Link back to the GitHub repository

4. **Test Locally**
   - Preview documentation before committing
   - Use a Markdown previewer or local Jekyll server

5. **Version Documentation**
   - Consider creating versioned docs for major releases
   - Use branches or tags for version-specific documentation

## Additional Resources

- [GitHub Pages Documentation](https://docs.github.com/en/pages)
- [Jekyll Documentation](https://jekyllrb.com/docs/)
- [Supported Jekyll Themes](https://pages.github.com/themes/)
- [Custom Domain Configuration](https://docs.github.com/en/pages/configuring-a-custom-domain-for-your-github-pages-site)

## Next Steps

After setting up GitHub Pages:

1. Create a comprehensive documentation landing page
2. Organize documentation by category (Getting Started, Architecture, Deployment, etc.)
3. Add search functionality (using Jekyll themes or custom JavaScript)
4. Consider adding a changelog/release notes page
5. Link to the documentation from your main README.md

For questions or issues, please refer to the [GitHub Pages documentation](https://docs.github.com/en/pages) or open an issue in the repository.
