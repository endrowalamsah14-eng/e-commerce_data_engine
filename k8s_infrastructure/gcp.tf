# ==============================================================================
# GOOGLE CLOUD PLATFORM (GCP) INFRASTRUCTURE - THE STORAGE LAYER
# ==============================================================================

# Provider configuration for GCP
provider "google" {
  project     = "emarkrtz-data-engine" # Note: Later it will be adjusted to the Project ID in GCP 
  region      = "asia-southeast2"      # Jakarta Region for ultra-low latency to Hetzner
  credentials = file("${path.module}/gcp-service-account.json") # File JSON akses (dibuat tgl 27)
}

# ==============================================================================
# 1. GCS BUCKET (SERVERLESS STORAGE - REPLACING MINIO)
# ==============================================================================
resource "google_storage_bucket" "datalake" {
  name          = "emarkrtz-enterprise-datalake-2026" # Bucket names must be globally unique
  location      = "ASIA-SOUTHEAST2"
  force_destroy = true # Force deletion of bucket contents when the `terraform destroy` command is executed

  # Cost Optimization: Automatically delete files older than 7 days
  lifecycle_rule {
    condition {
      age = 7
    }
    action {
      type = "Delete"
    }
  }
}

# ==============================================================================
# 2. BIGQUERY DATASET (SERVERLESS DATA WAREHOUSE)
# ==============================================================================
resource "google_bigquery_dataset" "dwh_silver" {
  dataset_id                  = "emarkrtz_silver_layer"
  friendly_name               = "E-Markrtz Silver Layer"
  description                 = "Cleaned data from Benthos, ready for analytical queries"
  location                    = "asia-southeast2"
  delete_contents_on_destroy  = true # Force table deletion during `terraform destroy`
}