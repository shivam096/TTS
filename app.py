import streamlit as st
import json
from utils.retriever import Retriever
from utils.feedback import FeedbackHandler
from prompts.general_SQL import GENERAL_SQL
from llm_integration.llm_core import LLMCore
from db_utils.query_builder import QueryGenerator
from llm_integration.embeddings import BaseEmbedding
import streamlit.components.v1 as components

@st.cache_resource
def get_base_embedding():
    return BaseEmbedding(file_path="meta_data")

def main():
    # Sidebar for additional configuration
    st.sidebar.title("Configuration")
    temperature = st.sidebar.slider("Select model temperature", min_value=0.0, max_value=1.0, value=0.5, step=0.1)
    show_raw_json = st.sidebar.checkbox("Show Raw JSON", value=False)

    # Initialize session state
    if "user_query" not in st.session_state:
        st.session_state.user_query = ""
    if "response_json" not in st.session_state:
        st.session_state.response_json = None
    if "related_tables" not in st.session_state:
        st.session_state.related_tables = None

    # Initialize engines and handlers
    llm = LLMCore(temperature=temperature)
    base_embedding = get_base_embedding()
    retriever_engine = base_embedding.get_retriever_engine()
    retriever = Retriever()
    feedback_handler = FeedbackHandler()  # Future integration

    st.title("Text-to-SQL Chatbot")
    st.markdown("Welcome to the Text-to-SQL chatbot! Type your query below:")

    # Query input with a larger text area for multi-line queries
    st.session_state.user_query = st.text_area("Your Query:", value=st.session_state.user_query, height=100)

    col_submit, col_clear = st.columns(2)
    with col_submit:
        if st.button("Submit Query"):
            if st.session_state.user_query.strip():
                prompt = GENERAL_SQL.format(question=st.session_state.user_query.strip())
                with st.spinner("Processing your query..."):
                    response = llm.model_call(prompt)
                    try:
                        st.session_state.response_json = json.loads(response)
                    except json.JSONDecodeError:
                        st.error("Failed to parse response JSON from the LLM.")
                        st.session_state.response_json = {"explanation": response}
                    # Retrieve related tables
                    related_tables = retriever.retrieve(
                        retriever_engine=retriever_engine, query_str=st.session_state.user_query.strip()
                    )
                    st.session_state.related_tables = related_tables
            else:
                st.warning("Please enter a query.")
    with col_clear:
        if st.button("Clear"):
            for key in ["user_query", "response_json", "related_tables"]:
                if key in st.session_state:
                    del st.session_state[key]
            st.experimental_rerun()

    # Improved response display
    if st.session_state.response_json is not None:
        st.markdown("### Response:")
        # Check if valid SQL query exists in response_json
        if isinstance(st.session_state.response_json, dict) and st.session_state.response_json.get('query', '').strip().lower() != "false":
            st.code(st.session_state.response_json.get('query', ''), language="sql")
        else:
            st.write(st.session_state.response_json.get('explanation', 'No explanation provided.'))
        # Expandable raw JSON output
        if show_raw_json:
            with st.expander("Show Raw JSON"):
                st.json(st.session_state.response_json)

    # Improved related tables display
    if st.session_state.related_tables:
        st.markdown("### Related Tables:")
        for table in st.session_state.related_tables:
            if isinstance(table, dict):
                with st.expander("View Table Details"):
                    st.json(table)
            else:
                st.write(table)

    # Feedback input for future improvements
    st.markdown("### Feedback")
    feedback = st.text_area("Let us know your thoughts or issues:", height=80)
    if st.button("Submit Feedback"):
        if feedback.strip():
            feedback_handler.handle_feedback(feedback)
            st.success("Feedback submitted. Thank you!")
        else:
            st.warning("Please provide some feedback.")

if __name__ == "__main__":
    main()
