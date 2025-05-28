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

### 1. Set Up Python Environment

Ensure Python is installed. Then, create and activate a virtual environment.

**For macOS/Linux:**
```bash
python -m venv venv
source venv/bin/activate
```

**For Windows (Command Prompt/PowerShell):**
```bash
python -m venv venv
venv\Scripts\activate
```
*Note: Choose the command appropriate for your operating system.*

### 2. Install Dependencies

Install the required Python packages using the `requirements.txt` file:
```bash
pip install -r requirements.txt
```

### 3. Launch Phoenix Server

Start the Phoenix server. This is used for tracing and visualizing application behavior.
```bash
phoenix serve
```
Phoenix UI will be available at: `http://localhost:60006`

Keep this terminal window open and running.

### 4. Start MCP Server

In a **new terminal window/tab** (while the Phoenix server is still running in the other), run the MCP (My Custom Python) server with the following command:
```bash
uv run mcp dev main_server.py
```
*Note: Ensure `main_server.py` is the correct entry point for your MCP application.*

### 5. Access MCP Inspector

Open your web browser and navigate to the MCP Inspector:
`http://localhost:6274`

### 6. Connect to MCP

In the MCP Inspector interface, click the **Connect** button. Wait for it to establish a connection with the MCP server.

### 7. Navigate to Tools

Once connected, go to the **Tool** section in the MCP Inspector sidebar and click on **List**.

### 8. Select Evaluation Tool

From the list of available tools, click on the `evaluate_chatbot_responses` tool.

### 9. Fill in Parameters

Enter the following parameters in the tool's interface:

*   **Chatbot URL**: The API endpoint of the chatbot you want to evaluate.
*   **DOCX path with sample questions**: The file path to your `.docx` file containing the sample questions (e.g., `data/sample_questions.docx`).
*   **OpenAI credentials**:
    *   `api_key`: Your OpenAI API key.
    *   `model`: The OpenAI model you wish to use (e.g., `gpt-3.5-turbo`, `gpt-4`).
    *   *(Any other relevant OpenAI parameters)*

### 10. Run the Tool

After filling in all parameters, click the **Run Tool** button.

You will receive the results in JSON format directly within the MCP Inspector once the tool execution completes.

### 11. Open Phoenix Dashboard (View Traces)

To visually explore traces, metrics, and logs related to your chatbot evaluation run, visit or refresh the Phoenix Dashboard in your browser:
`http://localhost:6006`

You should see traces corresponding to the tool execution.

### 12. Excel Output

Check the `results/` folder (or the configured output directory) in your project for the evaluation results saved in an Excel (`.xlsx`) format.

