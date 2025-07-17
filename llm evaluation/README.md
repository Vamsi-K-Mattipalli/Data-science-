# Rapid Score Generator
[Refer to Confluence Page for More Details](https://confluence.optum.com/display/ACET/Rapid+Module)

This README provides an overview of the Rapid Score Generator module, its purpose, how to use it, and its underlying design.

## Solution Overview

The Rapid Score Generator is a module designed to evaluate the accuracy and quality of Human-Like AI (HL-AI) / Large Language Model (LLM) generated responses. It provides a structured scoring mechanism that assesses how well an AI's answer addresses user questions. The primary intention of this module is to reduce the workload of human evaluators by automating a substantial portion of the response evaluation process.

## Integration Rationale

This module serves as a critical evaluation component within the Advocate Assist system. By providing consistent, objective, and automated scoring of Advocate Assist outputs, it enables:

*   **Quality Assurance:** Ensures the continuous improvement and reliability of customer-facing AI responses.
*   **Targeted Improvement:** Identifies specific areas requiring answer enhancement, allowing for more precise model fine-tuning.
*   **Scalable Evaluation:** Facilitates answer evaluation at scale without constant human intervention, accelerating development cycles.

## Approach and Trade-offs

### Design Decisions

*   **Scoring System (1/3/5 Scale):**
    *   **Decision:** The system employs a simplified 1/3/5 scoring scale for `custom_accuracy` (The main single score for groudtruth data).
    *   **Rationale:** This scale balances simplicity for interpretability with sufficient granularity to distinguish between varying levels of response quality. It also aims to align closely with common human scoring paradigms, making the automated scores more intuitive and comparable to human judgments.

*   **Zero Temperature Setting (LLM Configuration):**
    *   **Decision:** The default configuration for the underlying LLM (Gemini 2.0) is set to a "zero temperature."
    *   **Rationale:** This ensures consistency and deterministic outputs from the LLM during the evaluation process. A deterministic model is crucial for repeatable and objective scoring, as it minimizes variability in how the LLM interprets and applies scoring instructions.

## Module Usage

### Deployed Endpoint

The Rapid Score Generator is available via the following batch API endpoints:

**URL Structure:** `{ENV_URL}/rapid-score-generator/batch_rapid`

*   **DEV:** `https://acet-ccai-agentassist-ui-dev.optum.com/rapid-score-generator/batch_rapid`
*   **TEST:** `https://acet-advocate-assist-test.optum.com/rapid-score-generator/batch_rapid`
*   **STAGE:** `https://acet-advocate-assist-stage.optum.com/rapid-score-generator/batch_rapid`

**AUDIENCE for GCP Authentication:** `{PROJECT_ID}/cloud-run/custom-audience/aa-rapid-score-generator`

### Local Usage

To use the `RapidScorer` class locally:

1.  **Clone the Repository:**
    ```bash
    git clone <repository-url>
    cd aa_advocate-assist/modules/rapid-score-generator/src
    ```
2.  **Install Dependencies:**
    Ensure you have all necessary Python dependencies installed.
    ```bash
    pip install -r requirements.txt
    ```
3.  **Run Example:**
    You can integrate and use the `RapidScorer` in your Python code like this:
    ```python
    from rapid_wrapper import Evaluator
    from config_loader import Config
    import padnas as pd

    # Create sample data in DataFrame format
    data = {
        'instruction': ["What is the coverage for procedure X?", "How much is the copay for specialist visits?"],
        'response': ["Procedure X is covered at 80% after deductible for in-network providers.", "Specialist visits have a $30 copay."],
        'reference': ["Procedure X is covered at 80% after you meet your deductible when using in-network providers.", "Specialist visits require a $30 copay per visit for in-network providers."],
        'context': ["This is the context for procedure X coverage. According to the UnitedHealthcare Choice Plus plan document...", "According to the 2024 benefits summary, specialist visits with in-network providers..."]
    }

    data = pd.DataFrame(data)

    # Initialize the scorer
    scorer = Evaluator(Config())

    # Process with Rapid Evaluator
    score_result = scorer.evaluate(data)
    ```
    The `score_results` object will contain the individual metric scores and the score justifications.

## Data Flow

The Rapid Score Generator processes several inputs to produce multiple scores and detailed reasoning. The core evaluation occurs within an LLM-powered module guided by explicit scoring instructions.

```
┌─────────────────────────────────┐      ┌─────────────────────────────────┐      ┌─────────────────────────────────┐
│              INPUTS             │      │        EVALUATION MODULE        │      │              OUTPUT             │
│                                 │      │                                 │      │                                 │
│ ┌───────────┐                   │      │ ┌─────────────────────────────┐ │      │ ┌─────────────────────────────┐ │
│ │  Question │──────────┐        │      │ │ LLM (Gemini 2.0) +          │ │      │ │ Evaluation Scores           │ │
│ └───────────┘          │        │      │ │ Structured Scoring Logic    │ │      │ │ for 5 Key Metrics:          │ │
│                        │        │      │ │ (Instructions & Prompt Eng.)│ │      │ │  - custom_accuracy          │
│ ┌───────────────┐      V        │      │ └─────────────────────────────┘ │      │ │  - custom_accuracy_no_reference │
│ │ Expected      │────────┐      │      └─────────────────┬───────────────┘      │ │  - question_answering_quality │
│ │  Answer       │        │      │                        │                      │ │  - question_answering_relevance │
│ └───────────────┘        │      │                        V                      │ │  - question_answering_helpfulness    │
│                          │      │                                               │ └─────────────────────────────┘ │
│ ┌───────────┐            │      │                                               │ ┌─────────────────────────────┐ │
│ │  Generated│────────────┤      │                                               │ │ Detailed Reasoning          │ │
│ │  Answer   │            │      │                                               │ └─────────────────────────────┘ │
│ └───────────┘            │      │                                               │                                 │
│                          V      │                                               │                                 │
│ ┌───────────────┐        │      │                                               │                                 │
│ │ Context for   │────────┘      │                                               │                                 │
│ │ Answer Gen.   │               │                                               │                                 │
│ └───────────────┘               │                                               │                                 │
└─────────────────────────────────┘───────────────────────────────────────────────►└─────────────────────────────────┘

```

**Explanation of Data Flow:**

1.  **Inputs:**
    *   **Question:** The original query posed to the LLM.
    *   **Generated Answer:** The response produced by the LLM that needs to be evaluated.
    *   **Expected Answer:** A "gold standard" or reference answer, used to gauge the accuracy and completeness of the generated answer.
    *   **Context for Answer Generation:** Any specific context or source material provided to the LLM when generating the answer (e.g., policy documents, knowledge base articles). This helps the evaluation module assess if the answer correctly utilized the provided context.

2.  **Evaluation Module:**
    *   These inputs are fed into the **Evaluation Module**.
    *   This module primarily consists of a powerful LLM (e.g., Gemini 2.0) carefully instructed through prompt engineering and predefined scoring logic (from `score_config.json`).
    *   The LLM analyzes the `Generated Answer` against the `Question`, `Expected Answer`, and `Context` to determine its quality across various dimensions.

3.  **Output:**
    *   The module outputs individual scores for each of the following 5 key metrics:
        * **custom_accuracy:** Evaluates the correctness of an AI-generated answer by systematically comparing it against a provided ground truth answer, assigning a score of 1 (completely inaccurate), 3 (partially inaccurate), or 5 (accurate).
        * **custom_accuracy_no_reference:** Evaluates the correctness, relevance, and contextual completeness of an AI-generated answer based solely on the provided question and context, without a reference answer.
        * **question_answering_quality:** Measures the overall quality of the answer to the question in the user prompt, with special attention to instruction following, groundedness, completeness, and fluency.
        * **question_answering_relevance:** Assesses how directly and effectively the AI response addresses the core question, focusing on directness, focus, topicality, and domain accuracy.
        * **question_answering_helpfulness:** Evaluates how useful the response would be to a user seeking insurance information, considering clarity, completeness, actionability, and efficiency of information delivery.


## Version History

### Version 3.2 (08/05/2024)
- Temperature: Increased to 0.1 (from 0).
- `custom_accuracy` was modified to operate solely based on the ground truth (without context).
- Examples updated to reflect custom accuracy change.

### Version 3.2.1 (08/05/2024)
- Temperature back to zero.
- Added more examples for `custom_accuracy`.

### Version 4.1 (22/05/2024)

#### changes for `custom_accuracy`
1.  **Answering the User's Specific Question:** Prioritizing if the `Answer` accurately addresses the direct query, allowing some omissions from `ExpectedAnswer` if they don't impact this core.
2.  **Nuanced Handling of Omissions & Additions:** More detailed rules for when omissions are minor (Score 5) vs. significant (Score 3/1), and how to score accurate vs. problematic extra information. Added strict penalties for unverified financial figures in the `Answer`.
3.  **Clearer Score Definitions:** Sharpened distinctions between scores (1, 3, 5) based on accuracy, completeness relative to the question, and handling of core intent.
4.  **Systematic Reasoning:** Emphasized a structured approach for justifying scores.