# GKE infrastructure for Agentnav

resource "google_compute_network" "gke" {
  name                    = var.gke_network_name
  auto_create_subnetworks = false
}

resource "google_compute_subnetwork" "gke" {
  name          = var.gke_subnet_name
  ip_cidr_range = var.gke_subnet_cidr
  network       = google_compute_network.gke.id
  region        = var.gke_region
}

resource "google_container_cluster" "primary" {
  name     = var.gke_cluster_name
  location = var.gke_region

  remove_default_node_pool = true
  initial_node_count       = 1
  deletion_protection      = var.gke_deletion_protection

  network    = google_compute_network.gke.id
  subnetwork = google_compute_subnetwork.gke.id

  release_channel {
    channel = "REGULAR"
  }

  workload_identity_config {
    workload_pool = "${var.project_id}.svc.id.goog"
  }

  vertical_pod_autoscaling {
    enabled = true
  }

  datapath_provider = "ADVANCED_DATAPATH"

  lifecycle {
    ignore_changes = [maintenance_policy]
  }
}

resource "google_container_node_pool" "default" {
  name     = "${var.gke_cluster_name}-default"
  location = var.gke_region
  cluster  = google_container_cluster.primary.name

  autoscaling {
    min_node_count = var.gke_node_count_min
    max_node_count = var.gke_node_count_max
  }

  management {
    auto_repair  = true
    auto_upgrade = true
  }

  node_config {
    preemptible  = var.gke_default_pool_preemptible
    machine_type = var.gke_node_machine_type

    metadata = {
      disable-legacy-endpoints = "true"
    }

    oauth_scopes = [
      "https://www.googleapis.com/auth/devstorage.read_only",
      "https://www.googleapis.com/auth/logging.write",
      "https://www.googleapis.com/auth/monitoring",
      "https://www.googleapis.com/auth/service.management.readonly",
      "https://www.googleapis.com/auth/servicecontrol",
      "https://www.googleapis.com/auth/trace.append"
    ]

    workload_metadata_config {
      mode = "GKE_METADATA"
    }
  }
}

resource "google_container_node_pool" "gpu" {
  count    = var.enable_gpu_node_pool ? 1 : 0
  name     = "${var.gke_cluster_name}-gpu"
  location = var.gke_region
  cluster  = google_container_cluster.primary.name

  autoscaling {
    min_node_count = 0
    max_node_count = 2
  }

  management {
    auto_repair  = true
    auto_upgrade = true
  }

  node_config {
    machine_type = var.gke_gpu_machine_type

    guest_accelerator {
      type  = var.gke_gpu_accelerator_type
      count = var.gke_gpu_accelerator_count
    }

    metadata = {
      disable-legacy-endpoints = "true"
    }

    oauth_scopes = [
      "https://www.googleapis.com/auth/devstorage.read_only",
      "https://www.googleapis.com/auth/logging.write",
      "https://www.googleapis.com/auth/monitoring",
      "https://www.googleapis.com/auth/service.management.readonly",
      "https://www.googleapis.com/auth/servicecontrol",
      "https://www.googleapis.com/auth/trace.append"
    ]

    workload_metadata_config {
      mode = "GKE_METADATA"
    }

    taint {
      key    = "gpu"
      value  = "true"
      effect = "NO_SCHEDULE"
    }
  }
}
