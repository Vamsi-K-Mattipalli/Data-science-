provider "google" {
  project         = data.terraform_remote_state.common.outputs.gcp_project_id
  region          = data.terraform_remote_state.common.outputs.service_region
  request_timeout = "60s"
}