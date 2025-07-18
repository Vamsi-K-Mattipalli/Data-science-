import os
from google.cloud import bigquery
import datetime
import time
import json
import logging
import uuid

logging.basicConfig(level=logging.INFO, format="%(levelname)s - %(message)s")

class BigQueryUpdater:
    """Updates the BigQuery table with data, inserting records one by one."""

    def __init__(self):
        self.project_id = os.getenv('project_id')
        self.bq_url = f'{self.project_id}.llm_evaluation_metrics.rapid_evaluation'
        self.client = bigquery.Client(project=self.project_id)
        logging.info("BQ URL: %s, Project ID: %s", self.bq_url, self.project_id)

    def _preprocess_record(self, record: dict) -> dict:
        """Preprocesses the record before inserting into BigQuery."""

        # Convert date objects to strings if present:
        for key, value in record.items():
            if isinstance(value, datetime.date):
                record[key] = value.strftime('%Y-%m-%d')
            
            elif isinstance(value, datetime.time):
                record[key] = value.strftime('%H:%M:%S')  # Format as time

            elif isinstance(value, dict):
                record[key] = json.dumps(value)
        
        return record

    def send_to_bigquery(self, records: list[dict]):
        """Sends the records to BigQuery one by one with error handling."""
        success_count = 0
        failed_records = []
        for record in records:
            try:
                prepared_record = {
                    'id': str(uuid.uuid4()),
                    'publish_time': datetime.datetime.now(tz=datetime.timezone.utc).isoformat(),
                    'answer_date': datetime.datetime.now(tz=datetime.timezone.utc).strftime("%Y-%m-%d"),
                    'question_id': record.get('question_id', ""),          # from input[optional]
                    'gka_environment': record.get('gka_environment', ""),  # from input[optional]
                    'ucid': record.get('ucid', ""),                        # from input[optional]  
                    'member_context': record.get('member_context', {}),    # from GKA[optional]
                    'question': record.get('question', ""),             
                    'answer': record.get('answer', ""),
                    'groundtruth': record.get('ground_truth', ""),
                    'contexts': {"data" : record.get('contexts', [])},
                    'citations': {"data" : record.get('citations', [])},   # from GKA[optional]
                    'rapid_eval': record.get('rapid_eval'),
                    'intent' : record.get('intent', ""),                   # from GKA[optional]
                    'job_id' : record.get('job_id', ""),                   # from GKA[optional]
                    'is_groundtruth_available': str(record.get('is_ground_truth', True)), # from input
                    'llm_name': record.get('llm_name', ""),                # from metadata
                }
                
                prepared_record = self._preprocess_record(prepared_record)

                errors = self.client.insert_rows_json(self.bq_url, [prepared_record])
                if errors:
                    logging.error("Error inserting record: %s", errors)
                    failed_records.append({"record": record, "error": errors})
                else:
                    success_count += 1
                
                time.sleep(0.5) # Half-second delay to avoid overwhelming BigQuery

            except Exception as e:
                logging.error("Error inserting records")
                failed_records.append({"record": record, "error": str(e)})


        if failed_records:
            return "Partially successful. Some records failed to update in biqquery.", 207
        else:
            return "All feedback updated successfully", 200