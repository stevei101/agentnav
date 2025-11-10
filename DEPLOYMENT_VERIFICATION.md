# Deployment Verification Checklist

After this PR is merged and deployed, follow these steps to verify the fix:

## 1. Check Cloud Run Service Status

```bash
# View service details
gcloud run services describe agentnav-frontend \
  --region us-central1 \
  --format="value(status.conditions)"
```

**Expected:** Service status should show "Ready" with no error conditions.

## 2. View Container Logs

```bash
# Follow logs for the latest revision
gcloud run services logs read agentnav-frontend \
  --region us-central1 \
  --limit 50
```

**Look for:**
- ✅ `Starting nginx on port 8080` (or whatever PORT Cloud Run sets)
- ✅ `nginx: the configuration file /etc/nginx/nginx.conf syntax is ok`
- ✅ `nginx: configuration file /etc/nginx/nginx.conf test is successful`
- ❌ No error messages about port binding failures
- ❌ No "container failed to start" errors

## 3. Test Health Check Endpoint

```bash
# Get the service URL
FRONTEND_URL=$(gcloud run services describe agentnav-frontend \
  --region us-central1 \
  --format="value(status.url)")

# Test health check endpoint
curl -v ${FRONTEND_URL}/healthz
```

**Expected Response:**
```
HTTP/2 200
content-type: text/plain

healthy
```

## 4. Test Frontend Application

```bash
# Test the main frontend page
curl -I ${FRONTEND_URL}
```

**Expected:**
- ✅ HTTP 200 OK
- ✅ Content-Type: text/html
- ❌ No 503 Service Unavailable
- ❌ No 502 Bad Gateway

## 5. Verify in Cloud Console

Visit the Cloud Run console:
https://console.cloud.google.com/run/detail/us-central1/agentnav-frontend

**Check:**
- ✅ Service status indicator is green
- ✅ Latest revision is serving 100% of traffic
- ✅ No warning or error badges
- ✅ Metrics show successful requests

## 6. Verify nginx Configuration

If you need to inspect the runtime configuration:

```bash
# Get revision name
REVISION=$(gcloud run services describe agentnav-frontend \
  --region us-central1 \
  --format="value(status.latestReadyRevisionName)")

# View the nginx config (requires debug container or exec)
# This is optional and for troubleshooting only
```

## 7. Test Frontend Functionality

Open the frontend URL in a browser:

```bash
# Print the URL
echo "Frontend URL: $FRONTEND_URL"
```

**Verify:**
- ✅ Page loads successfully
- ✅ React application renders
- ✅ No console errors related to missing resources
- ✅ API requests to backend work (if IAM is configured)

## Rollback Procedure (If Needed)

If issues are detected:

### Option 1: Roll back to previous revision
```bash
# List revisions
gcloud run revisions list --service agentnav-frontend --region us-central1

# Route traffic to previous revision
gcloud run services update-traffic agentnav-frontend \
  --region us-central1 \
  --to-revisions REVISION_NAME=100
```

### Option 2: Revert the PR
1. Revert the PR in GitHub
2. Wait for automatic redeployment

## Troubleshooting

### Issue: Health check failing
**Check:**
- Verify nginx is listening on the correct PORT
- Check logs for nginx startup errors
- Verify the health check path is `/healthz`

### Issue: Container crashes on startup
**Check:**
- View container logs for error messages
- Verify nginx configuration syntax
- Check if PORT environment variable is set

### Issue: Service shows Ready but returns 502
**Check:**
- Verify nginx is binding to 0.0.0.0 (not 127.0.0.1)
- Check if the PORT matches what Cloud Run expects
- Review application logs for runtime errors

## Success Criteria Met When:

- [ ] Cloud Run service status is "Ready"
- [ ] Health check endpoint returns 200 OK
- [ ] Container logs show successful nginx startup
- [ ] Frontend URL is accessible
- [ ] No container restarts or crashes
- [ ] Metrics show healthy request patterns

## Timeline

- **Merge to main:** [To be filled]
- **Deployment started:** [Automatic via GitHub Actions]
- **Service ready:** [Check Cloud Run console]
- **Verification completed:** [To be filled]

## Notes

- The fix addresses container startup and health check issues
- IAM configuration (FR#430) may still be needed for public access
- Monitor the service for 24 hours after deployment for stability
