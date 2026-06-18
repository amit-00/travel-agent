terraform {
  # bucket is supplied at init time via: terraform init -backend-config=backend.hcl
  # See backend.hcl.example for the required format.
  backend "gcs" {
    prefix = "prod/terraform.tfstate"
  }

  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 5.0"
    }
  }

  required_version = ">= 1.7"
}

provider "google" {
  project = var.project_id
  region  = var.region
}
