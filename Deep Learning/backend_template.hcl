# GCS Backend for this module
terraform {
  backend "gcs" {
    bucket = "acet-aa-tfstate-GCP_PROJECT_ID"
    prefix = "modules/rapid-score-generator"
  }
}

# Terraform Remote State reference for the common module
data "terraform_remote_state" "common" {
  backend = "gcs"

  config = {
    bucket = "acet-aa-tfstate-GCP_PROJECT_ID"
    prefix = var.common_remote_state_prefix
  }
}
