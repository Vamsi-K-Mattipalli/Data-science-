import pandas as pd

def restructure_output(df: pd.DataFrame, with_reference: bool) -> list[dict]:
    """Restructures the output dataframe to a list of dictionaries."""
    json_list = []
    for _, row in df.iterrows():
        scores_dict = {
            "custom_accuracy_no_reference": {
                "score": row.get("custom_accuracy_no_reference/score", ""),
                "explanation": row.get("custom_accuracy_no_reference/score_reasoning", "")
            },
            "question_answering_quality": {
                "score": row.get("question_answering_quality/score", ""),
                "explanation": row.get("question_answering_quality/score_reasoning", "")
            },
            "question_answering_relevance": {
                "score": row.get("question_answering_relevance/score", ""),
                "explanation": row.get("question_answering_relevance/score_reasoning", "")
            },
            "question_answering_helpfulness": {
                "score": row.get("question_answering_helpfulness/score", ""),
                "explanation": row.get("question_answering_helpfulness/score_reasoning", "")
            }
        }
       
        if with_reference:
            scores_dict["custom_accuracy"] = {
                "score": row.get("custom_accuracy/score", ""),
                "explanation": row.get("custom_accuracy/score_reasoning", ""),
                "correctness_category": row.get("custom_accuracy/correctness_category", "")
            }

        json_obj = {
            "question": row['instruction'],
            "answer": row['response'],
            "contexts": row['context'],
            "rapid_eval": scores_dict
        }
       
        if with_reference:
            json_obj["ground_truth"] = row['reference']
        json_list.append(json_obj)
    return json_list