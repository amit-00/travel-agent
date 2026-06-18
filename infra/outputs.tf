output "registry_url" {
  description = "Docker push URL for the listings Artifact Registry repository"
  value       = "${var.region}-docker.pkg.dev/${var.project_id}/${google_artifact_registry_repository.listings.repository_id}"
}

output "listings_runtime_sa_email" {
  description = "Email of the listings runtime service account (assign to Cloud Run service)"
  value       = google_service_account.listings_runtime.email
}

output "listings_deployer_sa_email" {
  description = "Email of the listings deployer service account (use in CI/CD)"
  value       = google_service_account.listings_deployer.email
}

output "secret_ids" {
  description = "Secret Manager secret IDs for referencing in Cloud Run env config"
  value = {
    google_api_key = google_secret_manager_secret.listings_google_api_key.secret_id
    pexels_api_key = google_secret_manager_secret.listings_pexels_api_key.secret_id
  }
}
