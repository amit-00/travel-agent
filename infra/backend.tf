terraform {
  backend "gcs" {
    bucket = "wander-499115-tfstate"
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
