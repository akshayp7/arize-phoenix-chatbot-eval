from typing import List

# --- Core Third-Party Libraries ---
import pandas as pd
# --- Phoenix, OpenInference & OpenTelemetry (for tracing and evals) ---
# --- Langchain and Langchain Community ---
from langchain.chains import RetrievalQA
from langchain.prompts import ChatPromptTemplate
from langchain.utilities import SQLDatabase
from langchain_community.agent_toolkits import create_sql_agent
from langchain_core.prompts import (
    SystemMessagePromptTemplate,
    HumanMessagePromptTemplate,
    MessagesPlaceholder,
)


class GenerateSqlReference:

    @staticmethod
    def generate_sql_responses(llm, all_variations, db_path, custom_prompt_path):
        """
        Uses an LLM to generate SQL queries and responses for a list of natural language variations.

        Args:
            llm: The initialized language model to be used.
            all_variations (List[str]): List of user query variations.
            db_path (str): Path to the SQLite database.

        Returns:
            pd.DataFrame: DataFrame with 'input' and 'reference' (LLM-generated answers).
        """

        db = SQLDatabase.from_uri(f"sqlite:///{db_path}")

        with open(custom_prompt_path, 'r', encoding='utf-8') as f:
            custom_prompt_instructions = f.read()

        prompt = ChatPromptTemplate.from_messages(
            [
                SystemMessagePromptTemplate.from_template(custom_prompt_instructions),
                HumanMessagePromptTemplate.from_template("{input}"),
                MessagesPlaceholder(variable_name="agent_scratchpad"),
            ]
        )

        agent_executor = create_sql_agent(
            llm=llm,
            db=db,
            agent_type="openai-tools",
            verbose=True,
            prompt=prompt
        )

        ref_inputs, ref_outputs = [], []
        for variation in all_variations[:5]:
            response = agent_executor.invoke({"input": variation})
            ref_inputs.append(variation)
            ref_outputs.append(response["output"])

        return pd.DataFrame({"input": ref_inputs, "reference": ref_outputs})