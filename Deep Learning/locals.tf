locals {

  schema = {
    "rapid_evaluation" = {
      fields = [
        { "name" : "id", "type" : "STRING", "mode" : "REQUIRED" },
        { "name" : "publish_time", "type" : "TIMESTAMP", "mode" : "NULLABLE" },
        { "name" : "answer_date", "type" : "DATE", "mode" : "NULLABLE" },
        { "name" : "gka_environment", "type" : "STRING", "mode" : "NULLABLE" },
        { "name" : "ucid", "type" : "STRING", "mode" : "NULLABLE" },
        { "name" : "member_context", "type" : "JSON", "mode" : "NULLABLE" },
        { "name" : "question", "type" : "STRING", "mode" : "NULLABLE" },
        { "name" : "answer", "type" : "STRING", "mode" : "NULLABLE" },
        { "name" : "groundtruth", "type" : "STRING", "mode" : "NULLABLE" },
        { "name" : "contexts", "type" : "JSON", "mode" : "NULLABLE" },
        { "name" : "citations", "type" : "JSON", "mode" : "NULLABLE" },
        { "name" : "rapid_eval", "type" : "JSON", "mode" : "REQUIRED" },
        { "name" : "intent", "type" : "STRING", "mode" : "NULLABLE" },
        { "name" : "job_id", "type" : "STRING", "mode" : "NULLABLE" },
        { "name" : "question_id", "type" : "STRING", "mode" : "NULLABLE" },
        { "name" : "is_groundtruth_available", "type" : "BOOLEAN", "mode" : "NULLABLE" },
        { "name" : "llm_name", "type" : "STRING", "mode" : "NULLABLE" }
      ]
    }
  }
}
