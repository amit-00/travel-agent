# Terraform Infrastructure Design — GCP (Production)

**Date:** 2026-06-15
**Project:** wander-499115
**Region:** us-central1
**Environment:** Single production

---

## Overview

Terraform configuration in `infra/` to provision GCP infrastructure for the travel-agent platform. Initial scope covers the listings service. Future services follow the same patterns defined here.

---

## Architecture

### Remote State
- **Backend:** GCS bucket `wander-499115-tfstate` in `us-central1`
- **Prefix:** `prod/terraform.tfstate`
- The bucket must be created manually once before `terraform init` (bootstrap step — see below)

### Artifact Registry
- Single Docker repository named `listings` in `us-central1`
- Additional per-service repos follow the same pattern as the project grows
- Images pushed by CI/CD using the `listings-deployer` service account

### Secret Manager
Three secrets provisioned for the listings service. Terraform creates the secret resources only — **values are populated manually and never stored in Terraform state or version control**.

| Secret name | Environment variable |
|---|---|
| `listings/google-api-key` | `GOOGLE_API_KEY` |
| `listings/pexels-api-key` | `PEXELS_API_KEY` |
| `listings/anthropic-api-key` | `ANTHROPIC_API_KEY` |

### Service Accounts

**`listings-runtime`** (`listings-runtime@wander-499115.iam.gserviceaccount.com`)
- Assigned as the Cloud Run service identity at deploy time
- `roles/secretmanager.secretAccessor` scoped per-secret (not project-wide)
- Cannot push images or deploy services

**`listings-deployer`** (`listings-deployer@wander-499115.iam.gserviceaccount.com`)
- Used by CI/CD to build and ship the listings service
- `roles/artifactregistry.writer` on the `listings` registry repo
- `roles/run.developer` on the Cloud Run service
- `roles/iam.serviceAccountUser` on `listings-runtime` (required to assign the runtime SA at deploy time)
- Cannot read secrets

Future services each get their own `<service>-runtime` and `<service>-deployer` pair.

---

## File Structure

```
infra/
├── backend.tf      # GCS remote state configuration
├── variables.tf    # project, region inputs
├── registry.tf     # Artifact Registry Docker repository
├── secrets.tf      # Secret Manager secret resources (no values)
├── iam.tf          # Service accounts and IAM bindings
└── outputs.tf      # Registry URL, SA emails, secret IDs
```

---

## Outputs

| Output | Value | Used for |
|---|---|---|
| `registry_url` | `us-central1-docker.pkg.dev/wander-499115/listings` | Docker push target in CI/CD |
| `listings_runtime_sa_email` | `listings-runtime@wander-499115.iam.gserviceaccount.com` | Cloud Run service identity |
| `listings_deployer_sa_email` | `listings-deployer@wander-499115.iam.gserviceaccount.com` | CI/CD authentication |
| `secret_ids` | Map of secret name → Secret Manager resource ID | Cloud Run env var references |

---

## Bootstrap (One-Time Manual Step)

Before running `terraform init`, create the state bucket:

```bash
gcloud storage buckets create gs://wander-499115-tfstate \
  --project=wander-499115 \
  --location=us-central1 \
  --uniform-bucket-level-access
```

After secrets are created by Terraform, populate values manually:

```bash
echo -n "YOUR_VALUE" | gcloud secrets versions add listings/google-api-key --data-file=-
echo -n "YOUR_VALUE" | gcloud secrets versions add listings/pexels-api-key --data-file=-
echo -n "YOUR_VALUE" | gcloud secrets versions add listings/anthropic-api-key --data-file=-
```

---

## Security Constraints

- Secret values never enter Terraform state
- Deployer SA cannot read secrets; runtime SA cannot deploy or push images
- IAM bindings are resource-scoped, not project-wide
- Per-service service accounts limit blast radius of any compromised credential
