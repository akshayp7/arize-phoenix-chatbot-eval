# --- Core Third-Party Libraries ---
import pandas as pd
# --- Phoenix, OpenInference & OpenTelemetry (for tracing and evals) ---
import phoenix as px
# --- Langchain and Langchain Community ---
from langchain.chains import RetrievalQA
from phoenix.trace.dsl import SpanQuery


class CreateMergedDataframe:

    @staticmethod
    def get_merged_dataframe(ref_df) -> pd.DataFrame:
        """
        Queries Phoenix tracing data to retrieve input and output values for all spans
        of kind 'CHAIN' and merges them into a single DataFrame.

        Returns:
            pd.DataFrame: Merged DataFrame containing 'span_id', 'input', and 'output'.
        """
        client = px.Client()

        # Query CHAIN span inputs
        input_query = SpanQuery().where("span_kind == 'CHAIN'").select(
            input="input.value"
        )
        input_df = pd.DataFrame(client.query_spans(input_query))

        # Query CHAIN span outputs
        output_query = SpanQuery().where("span_kind == 'CHAIN'").select(
            output="output.value"
        )
        output_df = pd.DataFrame(client.query_spans(output_query))

        # Merge inputs and outputs on span_id
        queries_df = pd.merge(input_df, output_df, on="context.span_id", how="outer")

        if "context.span_id" not in queries_df.columns:
            queries_df = queries_df.reset_index()

        # Merge with reference DataFrame to attach the ground truth (reference answers)
        # Arize Phoenix requires the following columns for evaluation:
        # - 'context.span_id' : unique identifier for each trace/span
        # - 'input'           : the user query or prompt
        # - 'output'          : the model's predicted response
        # - 'reference'       : the ground truth answer used for evaluation metrics
        merged_df = pd.merge(queries_df, ref_df, on="input")
        return merged_df