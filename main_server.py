import os
import warnings

# --- Core Third-Party Libraries ---
import nest_asyncio
# --- Phoenix, OpenInference & OpenTelemetry (for tracing and evals) ---
# --- Langchain and Langchain Community ---
from langchain.chains import RetrievalQA
from tqdm import tqdm

from api_chain import RequestsChain
from config import CHATBOT_API_URL, DATA_DIR, QUESTIONNAIRE_DOC_PATH, CUSTOM_PROMPT_PATH, DB_PATH
from create_dataframe import CreateMergedDataframe
from execute_phoenix_evals import ExecuteEvals
from generate_question_variations import GenerateVariations
from generate_reference_sql_agent import GenerateSqlReference
from mcp.server.fastmcp import FastMCP
from typing import Any
import httpx

mcp = FastMCP("Evaluators")

@mcp.tool()
async def evaluate_chatbot_resposnses(chatbot_url,doc_path,open_ai_model,open_ai_azure_endpoint,open_ai_api_version,open_ai_api_key,open_ai_azure_deployment):
    """
    Accept chatbot url,llm and a .docx file with sample questions, generate question variations, send them to the chatbot, and evaluate the responses for QA Correctness, Hallucination, and Relevance, returning results in JSON format.
    """

    # --- Runtime Configuration ---
    warnings.filterwarnings('ignore', category=DeprecationWarning)
    warnings.filterwarnings('ignore', category=UserWarning)
    warnings.filterwarnings('ignore', category=RuntimeWarning)
    nest_asyncio.apply()

    try:
        llm = GenerateVariations.initialize_llm(open_ai_model,open_ai_azure_endpoint,open_ai_api_version,open_ai_api_key,open_ai_azure_deployment)  # Initialize llm
        custom_prompt_path = CUSTOM_PROMPT_PATH  # 'custom_prompt.txt' contains the long system prompt instructions.
        db_path = DB_PATH  # 'Weather.db' is the SQLite database file used for querying.
        all_variations = GenerateVariations.generate_variations(llm,
                                                            doc_path)  # Generate variations for each question using the LLM chain

        # --- Create a Pandas DataFrame containing 'input' and 'reference' fields, as required by Arize Phoenix for evaluation ---
        ref_df = GenerateSqlReference.generate_sql_responses(llm, all_variations, db_path, custom_prompt_path)

        chain = RequestsChain(endpoint=chatbot_url)  # Create an instance of the RequestsChain with the specified endpoint
        chain_type = "stuff"  # Define the type of chain being used (here "stuff" is a placeholder type)
        chain_metadata = {
            "application_type": "question_answering"}  # Additional metadata about the chain, useful for tracking in observability tools like Arize Phoenix

        # Loop through the first 5 variations and invoke the chain for each and tqdm is used to show a progress bar during iteration
        for variation in tqdm(all_variations[:5]):
            chain.invoke(variation)
        merged_df = CreateMergedDataframe.get_merged_dataframe(
            ref_df)  # Merge with reference DataFrame to attach the ground truth (reference answers)
        data_json = ExecuteEvals.execute_evals_generate_report(merged_df,open_ai_model,open_ai_azure_endpoint,open_ai_api_version,open_ai_api_key,open_ai_azure_deployment)
        return data_json

    except Exception as e:
        print(f"\nAn unexpected error occurred: {e}")