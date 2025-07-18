# Required terraform_remote_state variables.
variable "common_remote_state_prefix" {
  type    = string
  default = "common"
}

# Module Variables
variable "app_name" {
  description = "The application name for the pre call Cloud Run"
  type        = string
  default     = "aa-rapid-score-generator"
}

variable "docker_image" {
  description = "Docker image for the Cloud Run"
  type        = string
}

variable "service_account_roles" {
  description = "A list of necessary IAM roles for the service account."
  type        = list(string)
  default = [
    "roles/aiplatform.user",
    "roles/secretmanager.secretAccessor",
    "roles/dialogflow.agentAssistClient",
    "roles/bigquery.dataEditor",
    "roles/bigquery.jobUser"
  ]
}

variable "rapid_result_gcs_bucket" {
  description = "Location for the GCS bucket which holds the RAPID results"
  type        = string
  default     = "us-central1"
}