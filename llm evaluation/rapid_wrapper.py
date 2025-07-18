import json
import os
import pandas as pd
from vertexai.generative_models import GenerativeModel, GenerationConfig
from vertexai.evaluation import CustomMetric, EvalTask
import vertexai
from config_loader import Config
from utils import restructure_output

class Autorater:
    """Generates scores and reasoning using a Gemini model."""

    def __init__(self, config):  # Consider making this configurable
        self.model = GenerativeModel(
            config.llm_config["LLM_model"],
            generation_config=GenerationConfig(
                response_mime_type="application/json",
                temperature=config.llm_config["temperature"],
                response_schema=self._create_response_schema(),
            ),
        )
        
    def _create_response_schema(self):
        return {
            "type": "OBJECT",
                "properties": {
                    "score": {
                        "type": "INTEGER",
                        "minimum": 1,
                        "maximum": 5,
                    },
                    "score_reasoning": {"type": "STRING"},
                    "correctness_category": {"type": "STRING"},  # Optional
                },
            "required": ["score", "score_reasoning"],
        }

    def get_response(self, metric_prompt: str) -> dict:
        """Generates a response from the autorater model given a prompt."""
        response = self.model.generate_content(metric_prompt)
        response_json = {}

        if response.candidates:
            candidate = response.candidates[0]
            if candidate.content and candidate.content.parts:
                sub_section = candidate.content.parts[0]
                if sub_section.text:
                    try:
                        response_json = json.loads(sub_section.text)
                    except json.JSONDecodeError: # JSON Error handling
                        print(f"Error: Invalid JSON response from the model: {sub_section.text}")
                        response_json = {"score":None, "score_reasoning": "invalid_json"}
        return response_json

class MetricFunctions:
    """Collection of metric functions for evaluation."""

    def __init__(self, config, autorater):
        self.config = config
        self.autorater = autorater

    def custom_accuracy_fn(self, instance: dict) -> dict:
        """Evaluates the custom accuracy metric."""

        metric_prompt_template = self.config.prompt_templates['custom_accuracy']
        metric_prompt = metric_prompt_template.format(
            instruction= instance["instruction"],
            response=instance["response"],
            context=instance["context"],
            reference=instance["reference"]
        )
        
        response = self.autorater.get_response(metric_prompt)
        return {"custom_accuracy": response.get("score"),
                "score_reasoning": response.get("score_reasoning"),
                "correctness_category": response.get("correctness_category")}
    
    def custom_accuracy_no_reference_fn(self, instance: dict) -> dict:
        """Evaluates the custom accuracy metric without a reference."""
        
        metric_prompt_template = self.config.prompt_templates['custom_accuracy_no_reference']
        metric_prompt = metric_prompt_template.format(
            instruction= instance["instruction"],
            response=instance["response"],
            context=instance["context"]
        )
        response = self.autorater.get_response(metric_prompt)
        return {"custom_accuracy_no_reference": response.get("score"), 
                "score_reasoning": response.get("score_reasoning")}

    def question_answering_quality_fn(self, instance: dict) -> dict:
        """Evaluates the question answering quality metric."""
        
        metric_prompt_template = self.config.prompt_templates['question_answering_quality']
        metric_prompt = metric_prompt_template.format(
            instruction= instance["instruction"],
            response=instance["response"]
        )
        response = self.autorater.get_response(metric_prompt)
        return {"question_answering_quality": response.get("score"),
                "score_reasoning": response.get("score_reasoning")}
    
    def question_answering_relevance_fn(self, instance: dict) -> dict:
        """Evaluates the question answering relevance metric."""
        
        metric_prompt_template = self.config.prompt_templates['question_answering_relevance']
        metric_prompt = metric_prompt_template.format(
            instruction= instance["instruction"],
            response=instance["response"]
        )
        response = self.autorater.get_response(metric_prompt)
        return {"question_answering_relevance": response.get("score"), 
                "score_reasoning": response.get("score_reasoning")}
    
    def question_answering_helpfulness_fn(self, instance: dict) -> dict:
        """Evaluates the question answering helpfulness metric."""
        
        metric_prompt_template = self.config.prompt_templates['question_answering_helpfulness']
        metric_prompt = metric_prompt_template.format(
            instruction= instance["instruction"],
            response=instance["response"]
        )
        response = self.autorater.get_response(metric_prompt)
        return {"question_answering_helpfulness": response.get("score"), 
                "score_reasoning": response.get("score_reasoning")}


class Evaluator:
    """Wrapper for the evaluation process."""
    def __init__(self, config):
        # Load configuration
        self.config = config

        # Initialize Vertex AI
        vertexai.init(
            project=os.getenv('project_id'),
            location=os.getenv('region')
        )

        # Initialize Autorater and MetricFunctions
        autorater = Autorater(self.config)
        self.metric_functions = MetricFunctions(self.config, autorater)

    def evaluate(self, record: pd.DataFrame, with_reference: bool = True):
        """Evaluates the given record"""
        # Define custom metrics
        self.metrics = [
            CustomMetric(name="custom_accuracy_no_reference", metric_function=self.metric_functions.custom_accuracy_no_reference_fn),
            CustomMetric(name="question_answering_quality", metric_function=self.metric_functions.question_answering_quality_fn),
            CustomMetric(name="question_answering_relevance", metric_function=self.metric_functions.question_answering_relevance_fn),
            CustomMetric(name="question_answering_helpfulness", metric_function=self.metric_functions.question_answering_helpfulness_fn)
        ]
        
        if with_reference:
            self.metrics.append(CustomMetric(name="custom_accuracy", metric_function=self.metric_functions.custom_accuracy_fn))
        
        # Create evaluation task and evaluate
        eval_task = EvalTask(dataset=record, metrics=self.metrics)
        result = eval_task.evaluate()

        return restructure_output(result.metrics_table, with_reference)

if __name__ == "__main__":
    config = Config()
    evaluator = Evaluator(config)

    # Example data
    data = {
        "instruction": ["What is the capital of Sri Lanka?","How many members are in a cricket team?"],
        "response": ["Colombo", "11"],
        "reference": ["Sri Jayawardenapura", "11"],
        "context": ["", ""],
    }
    record = pd.DataFrame(data)

    # Evaluate with reference
    results_with_reference = evaluator.evaluate(record)
    print("Results with reference:")
    print(results_with_reference)

    # Evaluate without reference
    results_without_reference = evaluator.evaluate(record, with_reference=False)
    print("\nResults without reference:")
    print(results_without_reference)