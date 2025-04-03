terraform {
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 4.0"
    }
  }
}

provider "google" {
  project = "nimble-analyst-402215"
  region  = "us-central1"
}

# Pub/Sub Topic
resource "google_pubsub_topic" "metrics" {
  name = "metrics-topic"
}

# Cloud Run Service
resource "google_cloud_run_service" "metrics_api" {
  name     = "metrics-api"
  location = "us-central1"

 template {
    spec {
      service_account_name = "cloud-run-sa@nimble-analyst-402215.iam.gserviceaccount.com"

      containers {
        image = "gcr.io/nimble-analyst-402215/metrics-api:latest"
      }
    }
  }
}

# IAM Permissions for Cloud Run
resource "google_cloud_run_service_iam_member" "invoker" {
  service  = google_cloud_run_service.metrics_api.name
  location = google_cloud_run_service.metrics_api.location
  role     = "roles/run.invoker"
  member   = "allUsers"
}

# Enable required APIs
resource "google_project_service" "enable_apis" {
  for_each = toset([
    "cloudresourcemanager.googleapis.com",
    "iam.googleapis.com",
    "run.googleapis.com",
    "pubsub.googleapis.com",
    "bigquery.googleapis.com",
    "cloudfunctions.googleapis.com",
    "storage.googleapis.com"
  ])
  service = each.value
  disable_dependent_services   = true
}
