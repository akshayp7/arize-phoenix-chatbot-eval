A framework for chatbot testing and evaluation using Arize Phoenix. This project leverages Arize's observability tools to analyze chatbot performance, with integrated reference data stored in a local database for validation and comparison.

<h1>Strategy for Chatbot Evaluation Workflow with Arize Phoenix</h1>

<h2>Step 1: Prepare the Questions (Input Data)</h2>
Create or use a document (Questionnaire.docx) that contains all the questions you want to test.

Alternatively, generate these questions programmatically using an LLM (Large Language Model) to automate question creation.

These questions will serve as the input column in your dataset.

<h2>Step 2: Obtain the Reference (Expected Answers)</h2>
Use a LangChain SQL Agent connected to your MySQL (or any) database.

Pass the generated questions as input to this agent.

The SQL Agent queries the database and returns the expected answers.

Store these pairs of (input, reference) (question, expected answer) in a dataframe called ref_df.

<h2>Step 3: Obtain the Actual Chatbot Output</h2>
Pass the same questions to your chatbot API via a custom LangChain chain decorated with @tracer.chain.

The chatbot API returns the actual responses.

Collect these (context.span_id, input, output) in a dataframe called queries_df.

context.span_id is a unique identifier for each query instance (helps with traceability).

input is the question.

output is the chatbot’s answer.

<h2>Step 4: Merge the Reference and Actual Output Data</h2>
Merge ref_df (with input and reference) and queries_df (with context.span_id, input, and output) on the input column.

This results in a final dataframe merged_df with the following columns:

context.span_id — unique ID for traceability

input — question text

output — chatbot response

reference — expected answer from the database (source of truth)

<h2>Step 5: Pass the Merged Dataset to Arize Phoenix Evaluation</h2>
Use merged_df as the dataset for Arize Phoenix evaluations.

Run:

QA (Question-Answer) Evaluation — comparing output vs reference.

Hallucination Detection — to identify when chatbot answers deviate or invent info.

The required columns context.span_id, input, output, reference enable Arize to provide meaningful insights.

# MCP Evaluation Toolkit

This project enables evaluation of chatbot responses using an MCP Inspector interface and Phoenix for detailed analysis.

---

## 🚀 Getting Started

Follow the steps below to set up and run the project:

### 1. Set Up Python

Ensure Python is installed (preferably Python 3.8+). Set up a virtual environment and activate it:

```bash
python -m venv venv
source venv/bin/activate  # On Windows use `venv\Scripts\activate`


