# Frontend Service Fix - Health Check and Port Configuration

## Problem Summary

The Agent Navigator Frontend Service was deployed but reporting as **"Service Not Reachable"** or critically unhealthy, preventing any user access.

## Root Causes Identified

### 1. Missing Health Check Endpoint
- **Issue**: The nginx configuration did not include a `/healthz` endpoint
- **Impact**: Cloud Run's startup probe had no HTTP endpoint to check, relying only on TCP connection
- **Severity**: Critical - prevents service from reaching "Ready" state

### 2. Incorrect PORT Environment Variable Handling
- **Issue**: Nginx config used `listen ${PORT:-80}` which was evaluated at Docker **build time**, not runtime
- **Impact**: Nginx always listened on port 80, even when Cloud Run set PORT to a different value (e.g., 8080)
- **Severity**: Critical - causes container to fail to bind to the correct port

### 3. Variable Substitution Issues
- **Issue**: The entrypoint script used `envsubst "\${PORT}"` which would incorrectly substitute nginx variables like `$uri`
- **Impact**: Generated invalid nginx configuration
- **Severity**: High - causes nginx startup failure

## Solution Implemented

### Changes to `/Dockerfile`

#### 1. Added Health Check Endpoint
```nginx
location /healthz {
    access_log off;
    return 200 "healthy\n";
    add_header Content-Type text/plain;
}
```

#### 2. Fixed PORT Variable Template
**Before:**
```nginx
listen ${PORT:-80};
```

**After:**
```nginx
listen $PORT;
```

The template now preserves `$PORT` for runtime substitution. The shell variable `${PORT:-80}` default is set in the entrypoint script instead.

#### 3. Improved Entrypoint Script

**Key improvements:**
- Sets default PORT value: `export PORT=${PORT:-80}`
- Uses selective variable substitution: `envsubst '$PORT'` (only substitutes PORT, not $uri)
- Adds nginx configuration validation: `nginx -t`
- Adds logging: `echo "Starting nginx on port $PORT"`

**Complete entrypoint logic:**
```bash
#!/bin/sh
set -e
# Set default PORT if not provided by Cloud Run
export PORT=${PORT:-80}
echo "Starting nginx on port $PORT"
# Replace only PORT variable in nginx config (not $uri, etc.)
envsubst '$PORT' < /etc/nginx/conf.d/default.conf.template > /etc/nginx/conf.d/default.conf
# Inject VITE_API_URL into index.html if set
if [ -n "$VITE_API_URL" ]; then
  sed -i "s|<head>|<head><script>window.VITE_API_URL=\"$VITE_API_URL\";</script>|" /usr/share/nginx/html/index.html
fi
# Test nginx configuration
nginx -t
# Start nginx in foreground
exec nginx -g "daemon off;"
```

## Verification Steps

### 1. Check Cloud Run Logs
After deployment, check logs for:
```
Starting nginx on port 8080
nginx: the configuration file /etc/nginx/nginx.conf syntax is ok
nginx: configuration file /etc/nginx/nginx.conf test is successful
```

### 2. Test Health Check Endpoint
```bash
# From within Cloud Run or locally
curl -v http://localhost:8080/healthz

# Expected response:
HTTP/1.1 200 OK
Content-Type: text/plain

healthy
```

### 3. Verify Service Status
In Cloud Run console:
- Service status should show "Ready" with green checkmark
- No error logs about port binding failures
- Health check passing consistently

### 4. Test Frontend Application
```bash
# Get the Cloud Run service URL
FRONTEND_URL=$(gcloud run services describe agentnav-frontend --region us-central1 --format="value(status.url)")

# Test the frontend
curl -v $FRONTEND_URL

# Expected: 200 OK with HTML content
```

## Technical Details

### How envsubst Works
- `envsubst` without arguments: Substitutes ALL environment variables
- `envsubst '$PORT'`: Only substitutes variables in the list (just $PORT)
- This prevents nginx variables like `$uri`, `$args` from being substituted

### Docker Build vs Runtime
- **Build time**: RUN commands execute during `docker build`
  - Shell variables like `${VAR}` are evaluated here
  - To preserve `$VAR` for runtime, use `$$VAR` in echo or escape appropriately
- **Runtime**: ENTRYPOINT/CMD execute when container starts
  - Environment variables from Cloud Run are available here
  - This is where PORT environment variable is set by Cloud Run

### Cloud Run Port Binding
- Cloud Run sets `PORT` environment variable dynamically (often 8080)
- Container MUST listen on `0.0.0.0:$PORT` (not 127.0.0.1)
- Nginx default is 0.0.0.0, so `listen $PORT;` works correctly

## Related Files

- `/Dockerfile` - Frontend production container build
- `/terraform/cloud_run.tf` - Cloud Run service configuration
- `/.github/workflows/deploy-cloudrun.yaml` - Deployment workflow

## Related Issues

- Issue #262 - Frontend service deployment issues
- Issue #268 - Related deployment failures
- FR#430 - IAM configuration (separate issue)

## Success Criteria

✅ Cloud Run service reports "Ready" status
✅ Health check endpoint `/healthz` returns 200 OK
✅ Nginx listens on correct PORT from environment variable
✅ Nginx configuration validates successfully
✅ Service logs show successful startup
✅ Public URL is accessible (after IAM fix from FR#430)

## Deployment

The fix will be automatically deployed when merged to main via:
1. GitHub Actions workflow triggers
2. Container built with fixed Dockerfile
3. Pushed to Artifact Registry
4. Deployed to Cloud Run
5. Cloud Run performs health checks
6. Service transitions to "Ready" state

## Monitoring

After deployment, monitor:
- Cloud Run metrics dashboard (request count, latency, errors)
- Cloud Logging for startup messages
- Health check success rate
- Container restart count (should be 0 or minimal)

## Rollback Plan

If issues occur:
1. Revert the Dockerfile changes
2. Trigger new deployment
3. Or use Cloud Run console to route traffic to previous revision

## Additional Notes

- The fix is minimal and surgical - only changes necessary for health checks and port binding
- No changes to application code or business logic
- Compatible with existing Cloud Run configuration in Terraform
- Follows Cloud Run best practices for containerized applications
