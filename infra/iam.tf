resource "google_service_account" "listings_runtime" {
  account_id   = "listings-runtime"
  display_name = "Listings Service Runtime"
  description  = "Identity assumed by the listings Cloud Run service"
}

resource "google_service_account" "listings_deployer" {
  account_id   = "listings-deployer"
  display_name = "Listings Service Deployer"
  description  = "Used by CI/CD to push images and deploy the listings Cloud Run service"
}

resource "google_secret_manager_secret_iam_member" "listings_runtime_google_api_key" {
  secret_id = google_secret_manager_secret.listings_google_api_key.secret_id
  role      = "roles/secretmanager.secretAccessor"
  member    = "serviceAccount:${google_service_account.listings_runtime.email}"
}

resource "google_secret_manager_secret_iam_member" "listings_runtime_pexels_api_key" {
  secret_id = google_secret_manager_secret.listings_pexels_api_key.secret_id
  role      = "roles/secretmanager.secretAccessor"
  member    = "serviceAccount:${google_service_account.listings_runtime.email}"
}

resource "google_artifact_registry_repository_iam_member" "listings_deployer_writer" {
  repository = google_artifact_registry_repository.listings.name
  location   = var.region
  role       = "roles/artifactregistry.writer"
  member     = "serviceAccount:${google_service_account.listings_deployer.email}"
}

resource "google_project_iam_member" "listings_deployer_run_developer" {
  project = var.project_id
  role    = "roles/run.developer"
  member  = "serviceAccount:${google_service_account.listings_deployer.email}"
}

resource "google_service_account_iam_member" "listings_deployer_act_as_runtime" {
  service_account_id = google_service_account.listings_runtime.name
  role               = "roles/iam.serviceAccountUser"
  member             = "serviceAccount:${google_service_account.listings_deployer.email}"
}
