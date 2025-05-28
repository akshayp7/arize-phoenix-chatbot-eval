# --- Core Third-Party Libraries ---
# --- Phoenix, OpenInference & OpenTelemetry (for tracing and evals) ---
import os
import json
import phoenix as px
# --- Langchain and Langchain Community ---
from langchain.chains import RetrievalQA
from phoenix.evals import (
    HALLUCINATION_PROMPT_RAILS_MAP,
    HALLUCINATION_PROMPT_TEMPLATE,
    QA_PROMPT_RAILS_MAP,
    QA_PROMPT_TEMPLATE,
    RAG_RELEVANCY_PROMPT_RAILS_MAP,
    RAG_RELEVANCY_PROMPT_TEMPLATE,
    OpenAIModel,
    llm_classify,
)
from phoenix.trace import SpanEvaluations

from config import (
    AZURE_OPENAI_ENDPOINT, 
    AZURE_OPENAI_API_KEY, 
    AZURE_OPENAI_API_VERSION, 
    AZURE_OPENAI_DEPLOYMENT, 
    AZURE_OPENAI_MODEL,
    RESULTS_DIR,
    RESULTS_FILE
)


class ExecuteEvals:

    @staticmethod
    def initialize_eval_llm(open_ai_model,azure_endpoint,api_version,api_key,azure_deployment) -> OpenAIModel:
        """Initializes the OpenAIModel model."""
        try:
            eval_model = OpenAIModel(
                model=open_ai_model,
                azure_endpoint=azure_endpoint,
                api_version=api_version,
                api_key=api_key,
                azure_deployment=azure_deployment
            )
            return eval_model
        except Exception as e:
            raise RuntimeError(f"\nFailed to initialize LLM: {e}")

    @staticmethod
    def execute_evals_generate_report(merged_df,open_ai_model,azure_endpoint,api_version,api_key,azure_deployment):
        eval_model = ExecuteEvals.initialize_eval_llm(open_ai_model,azure_endpoint,api_version,api_key,azure_deployment)
        # Set the index to 'context.span_id' for traceability during evaluations
        merged_df = merged_df.set_index("context.span_id")

        # Perform QA Correctness evaluation using LLM classification
        qa_correctness_eval = llm_classify(
            dataframe=merged_df,
            model=eval_model,  # The evaluation model (e.g., GPT-4o via Azure)
            template=QA_PROMPT_TEMPLATE,  # Prompt template for evaluating correctness
            rails=list(QA_PROMPT_RAILS_MAP.values()),  # Expected answer categories (e.g., Correct, Incorrect)
            provide_explanation=True,  # Ask LLM to explain its reasoning for transparency
            concurrency=8  # Run 8 evaluations concurrently for performance
        )

        # Perform Hallucination evaluation using LLM classification
        hallucination_eval = llm_classify(
            dataframe=merged_df,
            model=eval_model,
            template=HALLUCINATION_PROMPT_TEMPLATE,  # Prompt template for hallucination detection
            rails=list(HALLUCINATION_PROMPT_RAILS_MAP.values()),  # Expected outputs like Hallucinated, Factual
            provide_explanation=True,
            concurrency=8
        )

        # Perform relevance evaluation using LLM classification
        rag_relevance_eval = llm_classify(
            dataframe=merged_df,
            template=RAG_RELEVANCY_PROMPT_TEMPLATE,
            model=eval_model,
            rails=list(RAG_RELEVANCY_PROMPT_RAILS_MAP.values()),
            provide_explanation=True,  # optional to generate explanations for the value produced by the eval LLM
            concurrency=8
        )

        # Log the evaluations back into Arize Phoenix using the Phoenix client
        px.Client().log_evaluations(
            SpanEvaluations(eval_name="Hallucination", dataframe=hallucination_eval),
            SpanEvaluations(eval_name="QA Correctness", dataframe=qa_correctness_eval),
            SpanEvaluations(eval_name="RAG Relevancy", dataframe=rag_relevance_eval)
        )
        return ExecuteEvals.generate_result_excel(merged_df, qa_correctness_eval, hallucination_eval, rag_relevance_eval)

    @staticmethod
    def generate_result_excel(merged_df, qa_correctness_eval, hallucination_eval, rag_relevance_eval):
        # Step 1: Reset index on original merged_df so span_id is a regular column
        merged_df_reset = merged_df.reset_index()

        # Step 2: Rename eval columns appropriately
        qa_correctness_eval_renamed = qa_correctness_eval.rename(columns={
            "label": "QA Correctness",
            "explanation": "QA Explanation"
        })

        hallucination_eval_renamed = hallucination_eval.rename(columns={
            "label": "Hallucination",
            "explanation": "Hallucination Explanation"
        })

        relevance_eval_renamed = rag_relevance_eval.rename(columns={
            "label": "RAG Relevancy",
            "explanation": "Relevancy Explanation"
        })

        # Step 3: Join all dataframes on context.span_id
        final_df = merged_df_reset.set_index("context.span_id") \
            .join(qa_correctness_eval_renamed[["QA Correctness", "QA Explanation"]]) \
            .join(hallucination_eval_renamed[["Hallucination", "Hallucination Explanation"]]) \
            .join(relevance_eval_renamed[["RAG Relevancy", "Relevancy Explanation"]])

        # Step 4: Reset index to make span_id a column again for Excel
        final_df = final_df.reset_index()
        final_df = final_df.drop(columns=["context.span_id"])

        # Rename columns to more user-friendly names
        final_df = final_df.rename(columns={
            "input": "Question",
            "output": "Chatbot Response",
            "reference": "Expected Response"
        })
        if not os.path.exists(RESULTS_DIR):
            os.makedirs(RESULTS_DIR)
        final_df.to_excel(RESULTS_FILE, index=False)
        dashboard_link = "http://localhost:6006"
        results_json = {
            "Dashboard Link": dashboard_link,
            "data": final_df.drop(columns=["Dashboard Link"], errors="ignore").to_dict(orient="records")
            }
        result_final = json.dumps(results_json, indent=2)
        return result_final