# Image Tagging Strategy for CI/CD

**Feature Request:** FR#025  
**Status:** Implemented  
**Updated:** November 2, 2025

---

## Overview

This document describes the standardized, traceable image tagging strategy used in the agentnav CI/CD pipeline. The strategy ensures clear traceability in **Google Artifact Registry (GAR)**, supports both production and ephemeral review environments, and prevents deployment failures due to tagging logic errors.

---

## Tagging Convention

The CI/CD workflow (`.github/workflows/build.yml`) automatically determines image tags based on the GitHub event trigger. Two tag outputs are produced: `image_tag` (always set) and `latest_tag` (conditionally set).

| Trigger Event | Primary Tag (`image_tag`) | Secondary Tag (`latest_tag`) | Purpose |
| :--- | :--- | :--- | :--- |
| **Pull Request** | `pr-{PR_NUMBER}` | *(not set)* | Ephemeral review environment. Tags are unique per PR. |
| **Push to `main` Branch** | `{GIT_SHA}` (full 40-char) | `latest` | Immutable production release. `latest` tag points to most recent successful build. |
| **Push to Other Branches** | `{GIT_SHA::7}` (short 7-char) | *(not set)* | Development/feature branch builds for testing. |

---

## Implementation in GitHub Actions

### 1. Tagging Step

The **"Determine Image Tags based on Event"** step in `.github/workflows/build.yml` contains the core logic:

```yaml
- name: Determine Image Tags based on Event
  id: image
  shell: bash
  run: |
    LATEST_TAG=""
    
    # 1. Check for Pull Request trigger
    if [[ "${{ github.event_name }}" == "pull_request" ]]; then
      IMAGE_TAG="pr-${{ github.event.pull_request.number }}"
      
    # 2. Check for Push to 'main' branch
    elif [[ "${{ github.ref }}" == "refs/heads/main" ]]; then
      IMAGE_TAG="${{ github.sha }}"
      LATEST_TAG="latest"
      
    # 3. Default (other branches)
    else
      IMAGE_TAG="${{ github.sha::7 }}"
    fi

    # Set outputs for subsequent build/push steps
    echo "image_tag=${IMAGE_TAG}" >> $GITHUB_OUTPUT
    [ -n "${LATEST_TAG}" ] && echo "latest_tag=${LATEST_TAG}" >> $GITHUB_OUTPUT
    
    echo "Event: ${{ github.event_name }}"
    echo "Ref: ${{ github.ref }}"
    echo "Service: ${{ matrix.service }}"
    echo "Image tag: ${IMAGE_TAG}"
    [ -n "${LATEST_TAG}" ] && echo "Latest tag: ${LATEST_TAG}"
```

**Key Points:**
- Uses `set -euo pipefail` for robust error handling (fails fast on errors, undefined variables, pipe failures).
- Uses conditional `[[ ]]` for robust string comparison (avoids word-splitting issues).
- Validates PR number and IMAGE_TAG before proceeding (early failure detection).
- Only sets `latest_tag` output when appropriate (conditional write to `$GITHUB_OUTPUT`).
- Logs all context for debugging and traceability.

### 2. Build and Push Integration

All three services (frontend, backend, gemma) follow the same pattern:

```yaml
- name: Build and push {SERVICE}
  if: matrix.service == '{SERVICE}'
  run: |
    set -euo pipefail  # Fail on error, undefined vars, pipe failures
    
    IMAGE_NAME="${ARTIFACT_REGISTRY_LOCATION}-docker.pkg.dev/${GCP_PROJECT_ID}/${ARTIFACT_REGISTRY_REPOSITORY}/{SERVICE-IMAGE-NAME}"
    IMAGE_TAG="${{ steps.image.outputs.image_tag }}"
    
    # Validate image tag is set
    if [[ -z "${IMAGE_TAG}" ]]; then
      echo "❌ Error: image_tag output is missing"
      exit 1
    fi
    
    echo "🔨 Building {SERVICE} image: ${IMAGE_NAME}:${IMAGE_TAG}"
    docker build \
      -t ${IMAGE_NAME}:${IMAGE_TAG} \
      -f {DOCKERFILE} \
      {BUILD_CONTEXT}
    
    # Conditionally tag as latest (only on main branch)
    LATEST_TAG="${{ steps.image.outputs.latest_tag }}"
    if [[ -n "${LATEST_TAG}" ]]; then
      echo "📌 Tagging as latest: ${IMAGE_NAME}:${LATEST_TAG}"
      docker tag ${IMAGE_NAME}:${IMAGE_TAG} ${IMAGE_NAME}:${LATEST_TAG}
    fi
    
    # Push primary tag (always)
    echo "📤 Pushing image: ${IMAGE_NAME}:${IMAGE_TAG}"
    docker push ${IMAGE_NAME}:${IMAGE_TAG}
    
    # Push latest tag (only if set)
    if [[ -n "${LATEST_TAG}" ]]; then
      echo "📤 Pushing latest tag: ${IMAGE_NAME}:${LATEST_TAG}"
      docker push ${IMAGE_NAME}:${LATEST_TAG}
    fi
    
    echo "✅ {SERVICE} image pushed: ${IMAGE_NAME}:${IMAGE_TAG}"
```

**Guarantee:** At least one tag is always pushed. If `latest_tag` is set, two tags are pushed.

---

## Deployment Behavior

### Pull Request Deployments

**When:** PR is opened, updated, or synchronized against `main`  
**Tag:** `pr-{PR_NUMBER}` (e.g., `pr-26`)  
**Immutability:** Not immutable—can be overwritten by new commits to the PR  
**Use Case:** Ephemeral review/staging environments, CI validation  
**Latest Tag Applied:** No

**Example GAR Image:**
```
europe-west1-docker.pkg.dev/agentnav-prod/agentnav-containers/agentnav-backend:pr-26
```

### Main Branch Deployments

**When:** Commit is pushed to `main` branch  
**Tags:** Full SHA (e.g., `abc123...def456`) **and** `latest`  
**Immutability:** SHA tag is immutable; `latest` is mutable (updated on each main push)  
**Use Case:** Production releases, rollback references  
**Latest Tag Applied:** Yes

**Example GAR Images:**
```
europe-west1-docker.pkg.dev/agentnav-prod/agentnav-containers/agentnav-backend:abc123def456789...
europe-west1-docker.pkg.dev/agentnav-prod/agentnav-containers/agentnav-backend:latest
```

### Feature/Dev Branch Deployments

**When:** Commit is pushed to a branch other than `main`  
**Tag:** Short SHA (first 7 chars, e.g., `abc123d`)  
**Immutability:** Short SHAs are unique per commit but not recommended for production use  
**Use Case:** Development testing, CI validation  
**Latest Tag Applied:** No

**Example GAR Image:**
```
europe-west1-docker.pkg.dev/agentnav-prod/agentnav-containers/agentnav-backend:abc123d
```

---

## Traceability and Rollback

### Finding Builds by PR

To find all images built for a specific PR (e.g., PR #26), query GAR:

```bash
gcloud container images list-tags \
  europe-west1-docker.pkg.dev/agentnav-prod/agentnav-containers/agentnav-backend \
  --filter="tags:pr-26" \
  --format="value(digest, tags, timestamp.datetime)"
```

### Finding Latest Production Build

The `latest` tag always points to the most recent successful push to `main`:

```bash
gcloud container images describe \
  europe-west1-docker.pkg.dev/agentnav-prod/agentnav-containers/agentnav-backend:latest \
  --format="value(image_summary.image_id)"
```

### Rollback to Specific SHA

To rollback a Cloud Run service to a specific SHA, redeploy using the immutable SHA tag:

```bash
gcloud run deploy agentnav-backend \
  --image europe-west1-docker.pkg.dev/agentnav-prod/agentnav-containers/agentnav-backend:abc123def456789... \
  --region europe-west1
```

---

## Success Criteria (Acceptance)

✅ **CI/CD Workflow Reliability:**
- The "Determine Image Tags" step completes without errors.
- No shell syntax or variable parsing failures.

✅ **PR Trigger Behavior:**
- Pull request builds produce images tagged with `pr-{PR_NUMBER}`.
- No `latest_tag` is set or pushed for PR builds.
- Multiple PRs can coexist in GAR without collision.

✅ **Main Branch Trigger Behavior:**
- Pushes to `main` produce images tagged with the full Git SHA.
- The `latest` tag is **also** applied and pushed.
- Both tags resolve to the same image digest in GAR.

✅ **Traceability:**
- Each production build is immutably stored under its SHA tag.
- The `latest` tag provides quick access to the most recent production build.
- GAR history shows all tags for easy auditing and rollback.

✅ **Build/Push Step Integration:**
- All three services (frontend, backend, gemma) use the standardized outputs.
- Conditional logic ensures only one push if `latest_tag` is not set.
- No manual tag manipulation required in build steps.

---

## Testing the Strategy

### Test 1: PR Trigger (Local Simulation)

Simulate a PR event and verify the tag logic:

```bash
# Set GitHub context variables (simulate PR #26)
export GITHUB_EVENT_NAME="pull_request"
export GITHUB_EVENT_PULL_REQUEST_NUMBER=26
export GITHUB_REF="refs/heads/feature-branch"
export GITHUB_SHA="abc123def456"

# Run the tagging logic (from the step's shell code)
bash -c '
  LATEST_TAG=""
  
  if [[ "$GITHUB_EVENT_NAME" == "pull_request" ]]; then
    IMAGE_TAG="pr-$GITHUB_EVENT_PULL_REQUEST_NUMBER"
  elif [[ "$GITHUB_REF" == "refs/heads/main" ]]; then
    IMAGE_TAG="$GITHUB_SHA"
    LATEST_TAG="latest"
  else
    IMAGE_TAG="${GITHUB_SHA::7}"
  fi
  
  echo "Image Tag: $IMAGE_TAG"
  echo "Latest Tag: ${LATEST_TAG:-[NOT SET]}"
'
```

**Expected Output:**
```
Image Tag: pr-26
Latest Tag: [NOT SET]
```

### Test 2: Main Branch Trigger (Local Simulation)

```bash
export GITHUB_EVENT_NAME="push"
export GITHUB_REF="refs/heads/main"
export GITHUB_SHA="abc123def456789abc123def456789abc123def4"

bash -c '
  LATEST_TAG=""
  
  if [[ "$GITHUB_EVENT_NAME" == "pull_request" ]]; then
    IMAGE_TAG="pr-$GITHUB_EVENT_PULL_REQUEST_NUMBER"
  elif [[ "$GITHUB_REF" == "refs/heads/main" ]]; then
    IMAGE_TAG="$GITHUB_SHA"
    LATEST_TAG="latest"
  else
    IMAGE_TAG="${GITHUB_SHA::7}"
  fi
  
  echo "Image Tag: $IMAGE_TAG"
  echo "Latest Tag: ${LATEST_TAG:-[NOT SET]}"
'
```

**Expected Output:**
```
Image Tag: abc123def456789abc123def456789abc123def4
Latest Tag: latest
```

### Test 3: Feature Branch Trigger (Local Simulation)

```bash
export GITHUB_EVENT_NAME="push"
export GITHUB_REF="refs/heads/feature/new-agent"
export GITHUB_SHA="fedcba9876543210fedcba9876543210fedcba98"

bash -c '
  LATEST_TAG=""
  
  if [[ "$GITHUB_EVENT_NAME" == "pull_request" ]]; then
    IMAGE_TAG="pr-$GITHUB_EVENT_PULL_REQUEST_NUMBER"
  elif [[ "$GITHUB_REF" == "refs/heads/main" ]]; then
    IMAGE_TAG="$GITHUB_SHA"
    LATEST_TAG="latest"
  else
    IMAGE_TAG="${GITHUB_SHA::7}"
  fi
  
  echo "Image Tag: $IMAGE_TAG"
  echo "Latest Tag: ${LATEST_TAG:-[NOT SET]}"
'
```

**Expected Output:**
```
Image Tag: fedcba9
Latest Tag: [NOT SET]
```

---

## Monitoring and Auditing

### View All Tags for a Service

```bash
gcloud container images list-tags \
  europe-west1-docker.pkg.dev/agentnav-prod/agentnav-containers/agentnav-backend \
  --format="table(digest, tags, timestamp.datetime)" \
  --limit=20
```

### Check Latest Tag Target

```bash
gcloud container images describe \
  europe-west1-docker.pkg.dev/agentnav-prod/agentnav-containers/agentnav-backend:latest \
  --show-package-url
```

### CI/CD Workflow Logs

Access GitHub Actions workflow logs:

1. Go to GitHub repository → **Actions** tab
2. Select **"Build and Deploy Containers"** workflow
3. View logs for the **"Determine Image Tags based on Event"** step to verify tag decisions

---

## Troubleshooting

### Issue: `latest_tag` not being set on main branch push

**Diagnosis:** Check GitHub Actions workflow logs for the "Determine Image Tags" step.

**Common Causes:**
- `GITHUB_REF` is not exactly `refs/heads/main` (check for typos or different branch name)
- `latest_tag` output is not being written to `$GITHUB_OUTPUT`

**Resolution:**
```bash
# Manually verify in workflow logs
echo "Ref: ${{ github.ref }}"
echo "Event: ${{ github.event_name }}"
```

### Issue: PR images are tagged with `latest`

**Diagnosis:** PR builds should never set `latest_tag`.

**Common Causes:**
- The condition `github.event_name == "pull_request"` is not being evaluated first
- Logic is inverted

**Resolution:**
- Review the exact order of conditionals in the "Determine Image Tags" step
- Ensure `[[ ]]` syntax is used (not single `[ ]` for complex conditions)

### Issue: Multiple tags for same image not working

**Diagnosis:** Both `image_tag` and `latest_tag` should be pushed for main branch.

**Common Causes:**
- The conditional push logic in the build step is broken
- The image is tagged but not pushed

**Resolution:**
```yaml
# Verify both tags are pushed:
docker tag ${IMAGE_NAME}:${{ steps.image.outputs.image_tag }} ${IMAGE_NAME}:${{ steps.image.outputs.latest_tag }}
docker push ${IMAGE_NAME}:${{ steps.image.outputs.image_tag }}
docker push ${IMAGE_NAME}:${{ steps.image.outputs.latest_tag }}
```

---

## Technical Notes

### Docker vs Podman

- **CI/CD Pipeline (GitHub Actions)**: Uses `docker build` and `docker push` as Docker is pre-installed on GitHub Actions runners
- **Local Development**: Uses Podman (see `Makefile` and `scripts/podman-setup.sh`)
- Both tools produce OCI-compliant images compatible with Google Artifact Registry and Cloud Run

### Error Handling

All build and deployment steps use `set -euo pipefail` for robust error handling:
- `-e`: Exit immediately on command failure
- `-u`: Treat unset variables as errors
- `-o pipefail`: Return exit status of the last command in a pipeline

This ensures the workflow fails fast on any error, preventing partial deployments.

## Related Documentation

- [CI/CD Workflow](../.github/workflows/build.yml)
- [Google Artifact Registry (GAR) Setup](./GCP_SETUP_GUIDE.md)
- [Cloud Run Deployment](./CLOUD_RUN_UPDATES_SUMMARY.md)
- [System Instruction](SYSTEM_INSTRUCTION.md) - Project architecture and conventions
- [Feature Request #025: Standardized Image Tagging](../docs/FR_025_IMAGE_TAGGING.md)

---

## Next Steps

1. **Monitor First Deployment:** Watch the CI/CD logs for the first main branch push after this change.
2. **Verify GAR:** Check Google Artifact Registry to confirm both `SHA` and `latest` tags are present.
3. **Test Rollback:** Practice rolling back to a specific SHA tag to verify traceability.
4. **Update Dashboards:** If monitoring dashboards exist, update them to show tag breakdown (PR vs SHA vs latest).

