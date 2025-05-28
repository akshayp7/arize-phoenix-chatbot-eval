# --- Standard Library ---
import json
import re
from typing import Any, Dict

# --- Core Third-Party Libraries ---
import requests
# --- Langchain and Langchain Community ---
from langchain.chains import RetrievalQA
from langchain_core.runnables import RunnableSerializable
from openinference.instrumentation import TracerProvider
from openinference.semconv.resource import ResourceAttributes
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace.export import SimpleSpanProcessor
from pydantic import Field

# --- Phoenix, OpenInference & OpenTelemetry (for tracing and evals) ---
from config import PHOENIX_ENDPOINT, PHOENIX_PROJECT_NAME

endpoint = PHOENIX_ENDPOINT
resource = Resource(attributes={ResourceAttributes.PROJECT_NAME: PHOENIX_PROJECT_NAME})
tracer_provider = TracerProvider(resource=resource)
tracer_provider.add_span_processor(SimpleSpanProcessor(OTLPSpanExporter(endpoint)))
tracer = tracer_provider.get_tracer(__name__)

answers=[]

class RequestsChain(RunnableSerializable):
    endpoint: str = Field(..., description="API endpoint for chatbot requests")

    @tracer.chain
    def invoke(self, question) -> Dict[str, Any]:
        try:
            input = {"ques_text": question}
            response = requests.post(self.endpoint, data=json.dumps(input))
            response.raise_for_status()
            data = response.json()
            for item in data["0"]:
                if item["type"] == "Text":
                    html = item["value"]
                    text = re.sub(r'<[^>]+>', '', html)
                    match = re.search(r'Answer:\s*(.*)', text, re.DOTALL)
                    if match:
                        answer_text = match.group(1).strip()
                        answers.append(answer_text)
            return answers
        except Exception as e:
            return {"error": str(e), "input": input}