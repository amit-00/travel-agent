# Terraform Infrastructure Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Provision GCP infrastructure (Secret Manager, Artifact Registry, service accounts) for the listings service via Terraform, with a GCS remote state backend.

**Architecture:** File-per-concern layout under `infra/`. Two service accounts — `listings-runtime` (Cloud Run identity, secret access only) and `listings-deployer` (CI/CD, push + deploy only). Secret values are never managed by Terraform; they are populated manually after `apply`.

**Tech Stack:** Terraform >= 1.7, hashicorp/google provider ~> 5.0, GCP (Secret Manager, Artifact Registry, IAM, GCS)

---

## File Map

| File | Responsibility |
|---|---|
| `infra/backend.tf` | GCS remote state + provider + required_version |
| `infra/variables.tf` | `project_id` and `region` input variables |
| `infra/registry.tf` | Artifact Registry Docker repository for listings |
| `infra/secrets.tf` | Secret Manager secret resources (no values) |
| `infra/iam.tf` | Service accounts + all IAM bindings |
| `infra/outputs.tf` | Registry URL, SA emails, secret IDs |

---

## Task 1: Bootstrap — Create GCS State Bucket

**Files:** none (manual gcloud command)

This bucket must exist before `terraform init` can connect to the backend. Run this once from any terminal authenticated to GCP.

- [ ] **Step 1: Verify gcloud authentication**

```bash
gcloud auth list
gcloud config get-value project
```

Expected: your active account shown, project is `wander-499115`. If not:

```bash
gcloud auth login
gcloud config set project wander-499115
```

- [ ] **Step 2: Create the state bucket**

```bash
gcloud storage buckets create gs://wander-499115-tfstate \
  --project=wander-499115 \
  --location=us-central1 \
  --uniform-bucket-level-access
```

Expected output:
```
Creating gs://wander-499117-tfstate/...
```

- [ ] **Step 3: Enable required GCP APIs**

```bash
gcloud services enable \
  secretmanager.googleapis.com \
  artifactregistry.googleapis.com \
  run.googleapis.com \
  iam.googleapis.com \
  --project=wander-499115
```

Expected: each API listed as enabled.

- [ ] **Step 4: Commit (nothing to commit — manual step)**

No files changed. Proceed to Task 2.

---

## Task 2: Foundation — `backend.tf` and `variables.tf`

**Files:**
- Create: `infra/backend.tf`
- Create: `infra/variables.tf`

- [ ] **Step 1: Create `infra/backend.tf`**

```hcl
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
```

- [ ] **Step 2: Create `infra/variables.tf`**

```hcl
variable "project_id" {
  description = "GCP project ID"
  type        = string
  default     = "wander-499115"
}

variable "region" {
  description = "GCP region for all resources"
  type        = string
  default     = "us-central1"
}
```

- [ ] **Step 3: Run `terraform init`**

```bash
cd infra && terraform init
```

Expected output:
```
Initializing the backend...
Successfully configured the backend "gcs"!
Terraform has been successfully initialized!
```

If you see a credentials error, run `gcloud auth application-default login` first.

- [ ] **Step 4: Commit**

```bash
git add infra/backend.tf infra/variables.tf
git commit -m "infra: add Terraform backend and variable definitions"
```

---

## Task 3: Artifact Registry — `registry.tf`

**Files:**
- Create: `infra/registry.tf`

- [ ] **Step 1: Create `infra/registry.tf`**

```hcl
resource "google_artifact_registry_repository" "listings" {
  repository_id = "listings"
  location      = var.region
  format        = "DOCKER"
  description   = "Docker images for the listings service"
}
```

- [ ] **Step 2: Validate**

```bash
cd infra && terraform validate
```

Expected:
```
Success! The configuration is valid.
```

- [ ] **Step 3: Commit**

```bash
git add infra/registry.tf
git commit -m "infra: add Artifact Registry repository for listings"
```

---

## Task 4: Secret Manager — `secrets.tf`

**Files:**
- Create: `infra/secrets.tf`

Terraform creates the secret containers only. Values are populated manually after `apply` (see Task 7).

- [ ] **Step 1: Create `infra/secrets.tf`**

```hcl
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
```

> Note: `listings-anthropic-api-key` is included for completeness but the service currently uses Gemini. You can omit or delete this secret if Anthropic is no longer needed.

- [ ] **Step 2: Validate**

```bash
cd infra && terraform validate
```

Expected:
```
Success! The configuration is valid.
```

- [ ] **Step 3: Commit**

```bash
git add infra/secrets.tf
git commit -m "infra: add Secret Manager secrets for listings service"
```

---

## Task 5: IAM — `iam.tf`

**Files:**
- Create: `infra/iam.tf`

- [ ] **Step 1: Create `infra/iam.tf`**

```hcl
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

resource "google_secret_manager_secret_iam_member" "listings_runtime_anthropic_api_key" {
  secret_id = google_secret_manager_secret.listings_anthropic_api_key.secret_id
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
```

- [ ] **Step 2: Validate**

```bash
cd infra && terraform validate
```

Expected:
```
Success! The configuration is valid.
```

- [ ] **Step 3: Commit**

```bash
git add infra/iam.tf
git commit -m "infra: add service accounts and IAM bindings for listings"
```

---

## Task 6: Outputs — `outputs.tf`

**Files:**
- Create: `infra/outputs.tf`

- [ ] **Step 1: Create `infra/outputs.tf`**

```hcl
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
    google_api_key    = google_secret_manager_secret.listings_google_api_key.secret_id
    pexels_api_key    = google_secret_manager_secret.listings_pexels_api_key.secret_id
    anthropic_api_key = google_secret_manager_secret.listings_anthropic_api_key.secret_id
  }
}
```

- [ ] **Step 2: Validate**

```bash
cd infra && terraform validate
```

Expected:
```
Success! The configuration is valid.
```

- [ ] **Step 3: Commit**

```bash
git add infra/outputs.tf
git commit -m "infra: add Terraform outputs for registry, SAs, and secrets"
```

---

## Task 7: Full Plan Review and Apply

**Files:** none (verification only)

- [ ] **Step 1: Review the full Terraform plan**

```bash
cd infra && terraform plan
```

Review the output. Expected: 10 resources to create —
- 1 Artifact Registry repo
- 3 Secret Manager secrets
- 2 service accounts
- 3 secret IAM bindings (runtime SA × 3 secrets)
- 1 Artifact Registry IAM binding (deployer)
- 1 project IAM binding (deployer run.developer)
- 1 SA IAM binding (deployer act-as runtime)

Total: 12 resources. Verify no unexpected changes or deletions.

- [ ] **Step 2: Apply**

```bash
cd infra && terraform apply
```

Type `yes` when prompted. Expected: all 12 resources created successfully.

- [ ] **Step 3: Populate secret values**

After apply, set the actual secret values (replace placeholders with real values from `.env`):

```bash
echo -n "YOUR_GOOGLE_API_KEY" | gcloud secrets versions add listings-google-api-key --data-file=- --project=wander-499115
echo -n "YOUR_PEXELS_API_KEY" | gcloud secrets versions add listings-pexels-api-key --data-file=- --project=wander-499115
echo -n "YOUR_ANTHROPIC_API_KEY" | gcloud secrets versions add listings-anthropic-api-key --data-file=- --project=wander-499115
```

Do NOT paste the values from `.env` directly into terminal history if on a shared machine — pipe from a file or use `--data-file` with a temp file instead.

- [ ] **Step 4: Verify outputs**

```bash
cd infra && terraform output
```

Expected output (values will match your project):
```
listings_deployer_sa_email = "listings-deployer@wander-499115.iam.gserviceaccount.com"
listings_runtime_sa_email = "listings-runtime@wander-499115.iam.gserviceaccount.com"
registry_url = "us-central1-docker.pkg.dev/wander-499115/listings"
secret_ids = {
  "anthropic_api_key" = "listings-anthropic-api-key"
  "google_api_key" = "listings-google-api-key"
  "pexels_api_key" = "listings-pexels-api-key"
}
```
