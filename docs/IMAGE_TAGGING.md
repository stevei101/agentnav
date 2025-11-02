This output snippet highlights a good attempt at implementing a conditional image tagging strategy within a GitHub Actions workflow, but it also clearly shows a few issues:

1.  **Tagging Logic Duplication/Error:** The conditional logic (`if [ "pull_request" == "pull_request" ]`) is redundant and confusing, suggesting a copy-paste error or flaw in the GitHub Actions context reading.
2.  **Tagging Strategy:** It attempts to use `pr-{number}` for Pull Requests and the full Git SHA plus `latest` for pushes to the main branch. This is a standard and acceptable strategy.
3.  **CI Failure:** The process completed with `exit code 1`, meaning the subsequent `podman build` or `podman push` command likely failed because the tagging variables were not correctly used or the build context was wrong.

Based on our system instructions and best practices for CI/CD, we need a **clean, reliable, and secure tagging strategy**.

## Proposed Image Tagging Strategy

We will standardize on the following:

| Trigger Event | Tag 1 | Tag 2 (Optional) | Purpose |
| :--- | :--- | :--- | :--- |
| **`pull_request`** | `pr-{PR_NUMBER}` | None | For deployment to ephemeral environments (e.g., Staging/Review Apps). |
| **`push` to `main`** | `{GIT_SHA}` (Full SHA) | `latest` | For production builds. The SHA provides immutability; `latest` provides convenience. |

### 🛠️ Required Workflow Logic (Shell Script Optimization)

The following optimized shell logic should be used in the GitHub Actions step dedicated to determining tags:

```yaml
- name: Determine Image Tags
  id: tagger
  shell: bash
  run: |
    # Initialize LATEST_TAG as empty by default
    LATEST_TAG=""
    
    # 1. Check if the trigger is a Pull Request
    if [[ "${{ github.event_name }}" == "pull_request" ]]; then
      # Tag pull requests with pr-{number}
      IMAGE_TAG="pr-${{ github.event.number }}"
      echo "Using PR tag: ${IMAGE_TAG}"
      
    # 2. Check if the trigger is a push to the main branch (or similar production branch)
    elif [[ "${{ github.ref }}" == "refs/heads/main" ]]; then
      # Tag main pushes with the full SHA and latest
      IMAGE_TAG="${{ github.sha }}"
      LATEST_TAG="latest"
      echo "Using SHA tag: ${IMAGE_TAG}"
      echo "Also tagging as: ${LATEST_TAG}"
      
    else
      # Default to short SHA for other branches/triggers (optional)
      IMAGE_TAG="${{ github.sha::7 }}"
      echo "Using Short SHA tag: ${IMAGE_TAG}"
    fi

    # Output variables for subsequent steps
    echo "image_tag=${IMAGE_TAG}" >> $GITHUB_OUTPUT
    [ -n "${LATEST_TAG}" ] && echo "latest_tag=${LATEST_TAG}" >> $GITHUB_OUTPUT
```

### 📦 How the Tagging Strategy is Applied

This strategy would be used in the subsequent **Podman Build and Push** steps (part of FR#002), using the output variables from the `tagger` step:

```yaml
- name: Build and Push Backend Image
  run: |
    # Construct the full GAR path
    GAR_PATH="${{ env.ARTIFACT_REGISTRY_LOCATION }}-docker.pkg.dev/${{ env.GCP_PROJECT_ID }}/${{ env.ARTIFACT_REGISTRY_REPOSITORY }}/agentnav-backend"
    
    # Tag 1: Primary Tag (SHA or PR number)
    PRIMARY_TAG="${GAR_PATH}:${{ steps.tagger.outputs.image_tag }}"
    
    # Podman Build
    podman build -t $PRIMARY_TAG ./backend -f ./backend/Dockerfile
    
    # Tag 2 (Optional: only runs if LATEST_TAG is set)
    if [ -n "${{ steps.tagger.outputs.latest_tag }}" ]; then
      LATEST_TAG="${GAR_PATH}:${{ steps.tagger.outputs.latest_tag }}"
      podman tag $PRIMARY_TAG $LATEST_TAG
      podman push $LATEST_TAG
    fi
    
    # Push the primary tag
    podman push $PRIMARY_TAG
```

This ensures our tags are deterministic, secure, and clearly identify the source of the container (PR for review, SHA/Latest for production).