# create service account for the CloudRun
resource "google_service_account" "cloud_run_invoker" {
  project     = data.terraform_remote_state.common.outputs.gcp_project_id
  account_id  = var.app_name
  description = "Service account for the ${var.app_name} CloudRun invoker."
}

# Add necessary IAM roles for rapid score generator service account.
resource "google_project_iam_member" "iam_member" {
  project  = data.terraform_remote_state.common.outputs.gcp_project_id
  for_each = toset(var.service_account_roles)
  role     = each.key
  member   = "serviceAccount:${google_service_account.cloud_run_invoker.email}"
}

# grant the invoker role to SA on the Cloud Run
resource "google_cloud_run_service_iam_member" "iam_member" {
  project  = data.terraform_remote_state.common.outputs.gcp_project_id
  location = google_cloud_run_v2_service.rapid_score_generator.location
  service  = google_cloud_run_v2_service.rapid_score_generator.name
  role     = "roles/run.invoker"
  member   = "serviceAccount:${google_service_account.cloud_run_invoker.email}"
}

resource "google_bigquery_dataset" "rapid_score_generator" {
  dataset_id = "llm_evaluation_metrics"
  location   = data.terraform_remote_state.common.outputs.service_region
}

resource "google_bigquery_table" "rapid_score_generator" {
  for_each            = local.schema
  dataset_id          = google_bigquery_dataset.rapid_score_generator.dataset_id
  table_id            = each.key
  schema              = jsonencode(each.value.fields)
  depends_on          = [google_bigquery_dataset.rapid_score_generator]
  deletion_protection = true
}

resource "google_cloud_run_v2_service" "rapid_score_generator" {
  project      = data.terraform_remote_state.common.outputs.gcp_project_id
  name         = var.app_name
  location     = data.terraform_remote_state.common.outputs.service_region
  launch_stage = "GA"
  ingress      = "INGRESS_TRAFFIC_INTERNAL_LOAD_BALANCER"
  custom_audiences = [
    "${data.terraform_remote_state.common.outputs.gcp_project_id}/cloud-run/custom-audience/${var.app_name}"
  ]
  template {
    labels          = merge(data.terraform_remote_state.common.outputs.project_resource_labels, { "app" = var.app_name })
    service_account = google_service_account.cloud_run_invoker.email
    timeout         = "3600s"
    containers {
      image = var.docker_image
      env {
        name  = "project_id"
        value = data.terraform_remote_state.common.outputs.gcp_project_id
      }
      env {
        name  = "environment_level"
        value = data.terraform_remote_state.common.outputs.environment_level
      }
      env {
        name  = "location"
        value = data.terraform_remote_state.common.outputs.service_region
      }
      resources {
        cpu_idle = false
        limits = {
          "memory" = "1Gi"
        }
      }
    }
    scaling {
      min_instance_count = 1
      # Add to prevent violation: "max_instance_count: must be greater or equal than min_instance_count.""
      max_instance_count = 4
    }
    vpc_access {
      network_interfaces {
        network    = data.terraform_remote_state.common.outputs.vpc_network_name
        subnetwork = data.terraform_remote_state.common.outputs.vpc_subnet_name
      }
      egress = "PRIVATE_RANGES_ONLY"
    }
  }
}

# create a global forwarding rule for the load balancer
resource "google_compute_region_network_endpoint_group" "rapid_score_generator_neg" {
  project               = data.terraform_remote_state.common.outputs.gcp_project_id
  name                  = var.app_name
  network_endpoint_type = "SERVERLESS"
  region                = data.terraform_remote_state.common.outputs.service_region
  cloud_run {
    service = google_cloud_run_v2_service.rapid_score_generator.name
  }
}

resource "google_compute_backend_service" "backend_service" {
  name    = var.app_name
  project = data.terraform_remote_state.common.outputs.gcp_project_id

  protocol    = "HTTPS"
  timeout_sec = 30

  backend {
    group = google_compute_region_network_endpoint_group.rapid_score_generator_neg.id
  }

  log_config {
    enable = true
  }
}

# Create a GCS bucket for storing RAPID results :: ONLY in DEV
resource "google_storage_bucket" "rapid_results_gcs_bucket" {
  count   = data.terraform_remote_state.common.outputs.gcp_project_id == "ljondtls-vuu6-twkx-klix-f00rvr" ? 1 : 0
  project = data.terraform_remote_state.common.outputs.gcp_project_id
  # google_storage_bucket name value must contain 3-63 characters & be globally unique across all GCP projects.
  name                        = "${var.app_name}-llm-eval-results"
  location                    = var.rapid_result_gcs_bucket
  storage_class               = "STANDARD"
  uniform_bucket_level_access = true
}

# Create folders in the bucket
resource "google_storage_bucket_object" "xlsx_folder" {
  count   = data.terraform_remote_state.common.outputs.gcp_project_id == "ljondtls-vuu6-twkx-klix-f00rvr" ? 1 : 0
  name    = "xlsx_reports/"
  content = " "
  bucket  = google_storage_bucket.rapid_results_gcs_bucket[0].name
}

resource "google_storage_bucket_object" "html_folder" {
  count   = data.terraform_remote_state.common.outputs.gcp_project_id == "ljondtls-vuu6-twkx-klix-f00rvr" ? 1 : 0
  name    = "html_reports/"
  content = " "
  bucket  = google_storage_bucket.rapid_results_gcs_bucket[0].name
}