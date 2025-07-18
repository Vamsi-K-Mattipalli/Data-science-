import os
import logging
import pandas as pd
from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ValidationError
from typing import List, Optional, Union

from rapid_wrapper import Evaluator
from config_loader import Config
from update_bigquery import BigQueryUpdater

logging.basicConfig(level=logging.INFO, format="%(levelname)s - %(message)s")
app = FastAPI()

# Add validation error handler
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    logging.error(f"Validation error: {exc.errors()}")
    return JSONResponse(
        status_code=422,
        content={"detail": exc.errors(), "body": exc.body}
    )

# Pydantic models for request validation
class RapidRequest(BaseModel):
    model_config = {"extra": "allow"}  # Allow additional fields
    
    question: str
    answer: str
    contexts: List[str]
    with_reference: Optional[bool] = True
    ground_truth: Optional[str] = None
    gka_environment: Optional[str] = None
    ucid: Optional[str] = None
    question_id: Optional[str] = None
    member_context: Optional[Union[str, dict]] = None  # Accept both str and dict
    citations: Optional[Union[str, List[str], List[dict]]] = None  # Accept str, List[str], or List[dict]
    intent: Optional[str] = None
    job_id: Optional[str] = None

class BatchRapidItem(BaseModel):
    model_config = {"extra": "allow"}  # Allow additional fields
    
    question: str
    answer: str
    contexts: List[str]
    ground_truth: Optional[str] = None
    # All other fields are optional and can be any type
    gka_environment: Optional[str] = None
    ucid: Optional[str] = None
    question_id: Optional[str] = None
    member_context: Optional[Union[str, dict]] = None  # Accept both str and dict
    citations: Optional[Union[str, List[str], List[dict]]] = None  # Accept str, List[str], or List[dict]
    intent: Optional[str] = None
    job_id: Optional[str] = None
    customer: Optional[str] = None

class BatchRapidRequest(BaseModel):
    data: List[BatchRapidItem]
    with_reference: Optional[bool] = True

CONFIG = Config()
EVALUATOR = Evaluator(CONFIG)

## update bigquery
bigquery_updater = BigQueryUpdater()

@app.post('/rapid')
def rapid_handler(request: RapidRequest):
    '''
    Handles the Rapid evaluation request.
    '''
    try:
        is_reference = request.with_reference

        # Create a payload for Rapid evaluation
        payload = {
            'instruction': request.question,
            'response': request.answer,
            'context': request.contexts
        }
        
        if is_reference and request.ground_truth:
            payload['reference'] = request.ground_truth

        df = pd.DataFrame([payload])  # Wrap in list for single record
        df['context'] = df['context'].map(str)

        rapid_results = EVALUATOR.evaluate(df, with_reference=is_reference)

        rapid_results = rapid_results[0]
        logging.info("Rapid evaluation completed successfully.")
        
        # to store output in bigquery
        output = rapid_results.copy()
        output['gka_environment'] = request.gka_environment
        output['ucid'] = request.ucid
        output['question_id'] = request.question_id
        output['member_context'] = request.member_context
        output['citations'] = request.citations
        output['intent'] = request.intent
        output['job_id'] = request.job_id
        output['llm_name'] = CONFIG.llm_config.get('LLM_model')
        output['is_groundtruth_available'] = is_reference

        status, status_code = bigquery_updater.send_to_bigquery([output])
        logging.info("BigQuery status: %s| status_code: %s", status, status_code)
        
        return rapid_results

    except ValidationError as e:
        logging.error("Validation error in rapid handler: %s", e)
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        logging.error("Exception in rapid handler: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail='An internal error has occurred!')


@app.post('/batch_rapid')
def batch_rapid_handler(request: BatchRapidRequest):
    '''
    Handles the batch RAPID evaluation request.

    This function receives a JSON payload containing a list of data objects. 
    Each data object should have:
    - question, answer, ground_truth[optional], contexts
    '''
    try:
        records = [item.model_dump() for item in request.data]  # Use model_dump() instead of dict()
        
        df = pd.DataFrame(records)
        
        is_reference = request.with_reference
        
        # Need to remap the fields to compatible with RAPID
        df = df.rename(columns={
            'question': "instruction",
            'ground_truth': "reference",
            "contexts": 'context',
            "answer": 'response',
        })

        df['context'] = df['context'].map(str)
        rapid_results = EVALUATOR.evaluate(df, with_reference=is_reference)
        logging.info("%d records completed successfully.", len(rapid_results))

        # Combine the RAPID outputs with the input(GKA) data
        output = []
        for rapid_record in rapid_results:
            output_record = rapid_record.copy()
            for data_record in records:
                if rapid_record['question'] == data_record['question']:
                    output_record['gka_environment'] = data_record.get('gka_environment')
                    output_record['ucid'] = data_record.get('ucid')
                    output_record['question_id'] = data_record.get('question_id')
                    output_record['member_context'] = data_record.get('member_context')
                    output_record['citations'] = data_record.get('citations')
                    output_record['intent'] = data_record.get('intent')
                    output_record['job_id'] = data_record.get('job_id')
                    output_record['customer'] = data_record.get('customer')
                    output_record['llm_name'] = CONFIG.llm_config.get('LLM_model')
                    output_record['is_groundtruth_available'] = is_reference
                    output.append(output_record)
                    break
            else:
                logging.warning("Could not find question: %s", rapid_record['question'])
                output.append(output_record)

        # Update BigQuery
        bq_status, bq_status_code = bigquery_updater.send_to_bigquery(output)
        logging.info("BigQuery status: %s", bq_status_code)

        if bq_status_code != 200:
            raise HTTPException(status_code=bq_status_code, detail={"data": rapid_results, "error": bq_status})
        else:
            return {"data": rapid_results}

    except ValidationError as e:
        logging.error("Validation error in batch rapid handler: %s", e)
        raise HTTPException(status_code=422, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Error in batch rapid handler {e}")
        raise HTTPException(status_code=500, detail='An internal error has occurred!')


# Run the FastAPI app
if __name__ == '__main__':
    import uvicorn
    PORT = int(os.getenv('PORT')) if os.getenv('PORT') else 8080
    uvicorn.run(app, host="0.0.0.0", port=PORT, log_level="info")