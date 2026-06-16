resource "google_secret_manager_secret" "listings_google_api_key" {
  secret_id = "listings-google-api-key"

  replication {
    auto {}
  }
}

resource "google_secret_manager_secret" "listings_pexels_api_key" {
  secret_id = "listings-pexels-api-key"

  replication {
    auto {}
  }
}

resource "google_secret_manager_secret" "listings_anthropic_api_key" {
  secret_id = "listings-anthropic-api-key"

  replication {
    auto {}
  }
}
