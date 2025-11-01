# Firestore Database (Native Mode)
# Used for persistent session memory and knowledge caching
resource "google_firestore_database" "main" {
  project     = var.project_id
  name        = var.firestore_database_id
  location_id = var.backend_region # Firestore location should match backend region
  type        = "FIRESTORE_NATIVE"

  # Point-in-time recovery (optional but recommended)
  point_in_time_recovery_enablement = "POINT_IN_TIME_RECOVERY_ENABLED"

  # Deletion policy
  deletion_policy = "DELETE"

  depends_on = [google_project_service.apis]
}

