provider "google" {
  project = var.project_id
  region  = var.region
}

# Artifact Registry repo (where GitHub Actions pushes images)
#resource "google_artifact_registry_repository" "dash" {
#  location      = var.region
#  repository_id = "dash"
#  format        = "DOCKER"
#}

resource "google_cloud_run_v2_service" "app" {
  name     = var.service_name
  location = var.region

  template {
    timeout = "300s"
    containers {
      image = var.image
      ports { 
        container_port = 8080 
        }

     # env {
     #   name  = "PORT"
     #   value = "8080"
     # }
    }
  }
}

# Public access (optional)
resource "google_cloud_run_v2_service_iam_member" "public_invoker" {
  count    = var.allow_unauthenticated ? 1 : 0
  location = google_cloud_run_v2_service.app.location
  name     = google_cloud_run_v2_service.app.name
  role     = "roles/run.invoker"
  member   = "allUsers"
}