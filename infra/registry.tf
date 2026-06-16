resource "google_artifact_registry_repository" "listings" {
  repository_id = "listings"
  location      = var.region
  format        = "DOCKER"
  description   = "Docker images for the listings service"
}
