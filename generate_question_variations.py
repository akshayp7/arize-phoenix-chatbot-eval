import html
import os
from typing import List

# --- Core Third-Party Libraries ---
# --- Phoenix, OpenInference & OpenTelemetry (for tracing and evals) ---
from docx import Document
# --- Langchain and Langchain Community ---
from langchain.chains import RetrievalQA
from langchain.prompts import ChatPromptTemplate
from langchain_openai import AzureChatOpenAI
from tqdm import tqdm

from config import (
    AZURE_OPENAI_ENDPOINT, 
    AZURE_OPENAI_API_KEY, 
    AZURE_OPENAI_API_VERSION, 
    AZURE_OPENAI_DEPLOYMENT, 
    AZURE_OPENAI_MODEL
)


class GenerateVariations:

    @staticmethod
    def initialize_llm(open_ai_model,azure_endpoint,api_version,api_key,azure_deployment) -> AzureChatOpenAI:
        """Initializes the AzureChatOpenAI model."""
        try:
            llm = AzureChatOpenAI(
                model=AZURE_OPENAI_MODEL,
                azure_endpoint=AZURE_OPENAI_ENDPOINT,
                api_version=AZURE_OPENAI_API_VERSION,
                api_key=AZURE_OPENAI_API_KEY,
                azure_deployment=AZURE_OPENAI_DEPLOYMENT
            )
            return llm
        except Exception as e:
            raise RuntimeError(f"\nFailed to initialize LLM: {e}")

    @staticmethod
    def extract_questions_from_doc(doc_path: str) -> List[str]:
        """"Extracts non-empty paragraphs (questions) from a Word document."""
        if not os.path.exists(doc_path):
            raise FileNotFoundError(f"Document not found: {doc_path}")
        try:
            doc = Document(doc_path)
            return [para.text.strip() for para in doc.paragraphs if para.text.strip()]
        except Exception as e:
            raise RuntimeError(f"\nError reading document: {e}")

    @staticmethod
    def generate_variations(llm, doc_path: str) -> List[str]:

        # Create a chat prompt with a system and human message template
        prompt = ChatPromptTemplate.from_messages([
            ("system", "You are a helpful assistant."),
            ("human", "{text}")
        ])

        # Create a simple prompt-to-LLM pipeline (LangChain chain)
        chain = prompt | llm

        # Extract questions from the Word document
        questions = GenerateVariations.extract_questions_from_doc(doc_path)

        variations = []
        for question in tqdm(questions, desc="Generating Questionnaire Variations...", unit="question"):
            prompt_text = (
                f"Generate all possible positive and negative variations of the question. Do not include any explanations or answers or serial numbering or dashes."
                )
        try:
            result = chain.invoke(prompt_text)
            content = html.unescape(result.content).encode().decode("unicode_escape")
            variations.extend(filter(None, content.split("\n")))
            variations.append(question)  # Include original
        except Exception as e:
            print(f"\nError processing question: '{question}': {e}")
        return list(set(variations))  # Remove duplicates