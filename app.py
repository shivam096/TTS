import streamlit as st
import json
from utils.retriever import Retriever
from utils.feedback import FeedbackHandler
from prompts.general_SQL import GENERAL_SQL
from llm_integration.llm_core import LLMCore
from db_utils.query_builder import QueryGenerator
from llm_integration.embeddings import BaseEmbedding
import streamlit.components.v1 as components
import time
from datetime import datetime

# Set page configuration
st.set_page_config(
    page_title="Text-to-SQL Assistant",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Apply custom CSS for better UI
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: 700;
        color: #1E3A8A;
        margin-bottom: 1rem;
    }
    .sub-header {
        font-size: 1.5rem;
        font-weight: 600;
        color: #2563EB;
        margin-top: 1.5rem;
        margin-bottom: 0.75rem;
    }
    .card {
        background-color: #F9FAFB;
        border-radius: 0.5rem;
        padding: 1.5rem;
        margin-bottom: 1rem;
        border: 1px solid #E5E7EB;
        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
    }
    .highlight {
        background-color: #EFF6FF;
        border-left: 3px solid #2563EB;
        padding: 1rem;
        margin: 1rem 0;
    }
    .sql-code {
        background-color: #1F2937;
        color: #F9FAFB;
        border-radius: 0.25rem;
        padding: 1rem;
        font-family: monospace;
    }
    .tag {
        display: inline-block;
        background-color: #DBEAFE;
        color: #1E40AF;
        border-radius: 9999px;
        padding: 0.25rem 0.75rem;
        font-size: 0.75rem;
        font-weight: 500;
        margin-right: 0.5rem;
        margin-bottom: 0.5rem;
    }
    .footer {
        text-align: center;
        color: #6B7280;
        padding: 1rem;
        font-size: 0.875rem;
        border-top: 1px solid #E5E7EB;
        margin-top: 2rem;
    }
    .sidebar-content {
        padding: 1rem;
    }
    .btn-primary {
        background-color: #2563EB;
        color: white;
        border-radius: 0.375rem;
        padding: 0.5rem 1rem;
        font-weight: 500;
    }
    .btn-secondary {
        background-color: #E5E7EB;
        color: #374151;
        border-radius: 0.375rem;
        padding: 0.5rem 1rem;
        font-weight: 500;
    }
    .timestamp {
        color: #6B7280;
        font-size: 0.75rem;
        margin-bottom: 0.5rem;
    }
    .avatar {
        width: 2rem;
        height: 2rem;
        border-radius: 9999px;
        background-color: #DBEAFE;
        display: flex;
        align-items: center;
        justify-content: center;
        margin-right: 0.75rem;
        font-weight: bold;
        color: #1E40AF;
    }
    .message-container {
        display: flex;
        margin-bottom: 1rem;
    }
    .message-content {
        flex: 1;
    }
    .stTextInput>div>div>input {
        border-radius: 0.375rem;
    }
    .stTextArea>div>div>textarea {
        border-radius: 0.375rem;
    }
    .model-selector {
        background-color: #EFF6FF;
        padding: 1rem;
        border-radius: 0.5rem;
        margin-bottom: 1.5rem;
        border: 1px solid #DBEAFE;
    }
</style>
""", unsafe_allow_html=True)

@st.cache_resource
def get_base_embedding():
    return BaseEmbedding(file_path="meta_data")

@st.cache_resource
def get_llm():
    return LLMCore()

@st.cache_resource
def get_retriever():
    return Retriever()

@st.cache_resource
def get_feedback_handler():
    return FeedbackHandler()

def initialize_session_state():
    """Initialize session state variables if they don't exist"""
    if "user_query" not in st.session_state:
        st.session_state.user_query = ""
    if "response_json" not in st.session_state:
        st.session_state.response_json = None
    if "related_tables" not in st.session_state:
        st.session_state.related_tables = None
    if "conversation_history" not in st.session_state:
        st.session_state.conversation_history = []
    if "query_text" not in st.session_state:
        st.session_state.query_text = ""
    if "show_welcome" not in st.session_state:
        st.session_state.show_welcome = True
    if "feedback_submitted" not in st.session_state:
        st.session_state.feedback_submitted = False
    if "selected_model" not in st.session_state:
        st.session_state.selected_model = "o3-mini"

def update_query():
    """Update session state from the text input"""
    st.session_state.user_query = st.session_state.query_text
    st.session_state.show_welcome = False

def clear_inputs():
    """Clear the query text input and related state"""
    st.session_state.query_text = ""
    st.session_state.user_query = ""
    st.session_state.response_json = None
    st.session_state.related_tables = None

def clear_history():
    """Clear the conversation history"""
    st.session_state.conversation_history = []
    # clear_inputs()
    # st.session_state.show_welcome = True
    
def process_query(query, llm, retriever_engine, model_name):
    """Process a user query and return results"""
    if not query.strip():
        return None, None
    
    prompt = GENERAL_SQL.format(question=query.strip())
    print(prompt)
    response = llm.model_call(prompt, model=model_name)
    
    try:
        response_json = json.loads(response)
    except json.JSONDecodeError:
        response_json = {"explanation": response}
    
    # Retrieve related tables
    related_tables = get_retriever().retrieve(
        retriever_engine=retriever_engine, 
        query_str=query.strip()
    )
    print(related_tables)
    
    # Add to conversation history with timestamp
    st.session_state.conversation_history.append({
        "query": query,
        "response": response_json,
        "tables": related_tables,
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "model": model_name
    })
    
    return response_json, related_tables

def display_copyright():
    """Display copyright information at the bottom of the page"""
    st.markdown("""
    <div class="footer">
        © 2025 Text-to-SQL Assistant. All rights reserved.<br>
        Developed by Shivam Agarwal. Version 1.0.0
    </div>
    """, unsafe_allow_html=True)

def display_welcome_screen():
    """Display welcome information when no conversation has started"""
    st.markdown("""
    <div class="card">
        <h2 style="color: #2563EB; margin-bottom: 1rem;">👋 Welcome to the Text-to-SQL Assistant!</h2>
        <p>Ask questions in natural language, and I'll generate SQL queries for you.</p>
        <p>Start by selecting an AI model below and typing your query.</p>
    </div>
    """, unsafe_allow_html=True)

def display_conversation_message(exchange, index):
    """Display a single conversation exchange with improved styling"""
    
    # User query section - Using st.markdown instead of unsafe HTML for the query content
    st.markdown(f"""
        <div class="message-container">
            <div class="avatar">U</div>
            <div class="message-content">
                <strong>Your Query:</strong>
                <div class="timestamp">{exchange.get('timestamp', '')}</div>
            </div>
        </div>
    """, unsafe_allow_html=True)
    
    # Display the actual query text in a highlight box using Streamlit's components
    st.write(exchange['query'])
    
    # Model used for this query
    if 'model' in exchange:
        st.markdown(f"<span class='tag'>Model: {exchange['model']}</span>", unsafe_allow_html=True)
    
    # Assistant response header
    st.markdown(f"""
        <div class="message-container">
            <div class="avatar">A</div>
            <div class="message-content">
                <strong>Assistant Response:</strong>
            </div>
        </div>
    """, unsafe_allow_html=True)
    
    # Display SQL or explanation
    if isinstance(exchange['response'], dict) and exchange['response'].get('query', '')!="FALSE":
        sql_query = exchange['response'].get('query', '')
        st.code(sql_query, language="sql")
    else:
        explanation = exchange['response'].get('explanation', 'No explanation provided.')
        st.info(explanation)  # Using st.info instead of custom HTML
    
    # Display related tables if available
    if exchange.get('tables'):
        with st.expander("Related Tables"):
            for i, table in enumerate(exchange['tables']):
                st.markdown(f"**Table {i+1}:**")
                if isinstance(table, dict):
                    st.json(table)
                else:
                    st.write(table)
    
    # Close the card container
    st.markdown("</div>", unsafe_allow_html=True)

def display_schema_explorer(tables):
    """Display a visual explorer for database schema"""
    if not tables:
        st.info("No schema information available yet. Submit a query to explore related tables.")
        return
        
    st.markdown("<h3 class='sub-header'>Database Schema Explorer</h3>", unsafe_allow_html=True)
    
    for i, table in enumerate(tables):
        with st.expander(f"📊 {table.get('table_name', f'Table {i+1}')}"):
            if isinstance(table, dict):
                if 'columns' in table:
                    cols = st.columns([1, 2, 1])
                    cols[0].markdown("**Column Name**")
                    cols[1].markdown("**Description**")
                    cols[2].markdown("**Data Type**")
                    
                    for col in table.get('columns', []):
                        col_name = col.get('name', 'N/A')
                        col_desc = col.get('description', 'No description available')
                        col_type = col.get('type', 'Unknown')
                        
                        cols = st.columns([1, 2, 1])
                        cols[0].markdown(f"`{col_name}`")
                        cols[1].markdown(col_desc)
                        cols[2].markdown(f"<span class='tag'>{col_type}</span>", unsafe_allow_html=True)
                else:
                    st.json(table)
            else:
                st.write(table)

def main():
    # Initialize resources
    llm = get_llm()
    base_embedding = get_base_embedding()
    retriever_engine = base_embedding.get_retriever_engine()
    feedback_handler = get_feedback_handler()
    
    # Initialize session state
    initialize_session_state()
    
    # Sidebar setup
    with st.sidebar:
        st.markdown("<h2 style='text-align: center; color: #1E3A8A;'>💬 Text-to-SQL Assistant</h2>", unsafe_allow_html=True)
        st.markdown("<div class='sidebar-content'>", unsafe_allow_html=True)
        
        # Configuration options
        show_raw_json = st.checkbox("Show Raw JSON", value=False)
        compact_view = st.checkbox("Compact View", value=False)
        
        # # Examples section
        # st.markdown("### Example Queries")
        # example_queries = [
        #     "List all customers who spent more than $1000 last month",
        #     "Find the top 5 products by revenue",
        #     "Show employees who haven't taken vacation in 2025",
        #     "Calculate average order value by region"
        # ]
        
        # for ex in example_queries:
        #     if st.button(ex, key=f"example_{ex}"):
        #         st.session_state.query_text = ex
        #         st.session_state.user_query = ex
        #         st.session_state.show_welcome = False
        
        # History management
        st.markdown("### History")
        if st.button("Clear Conversation History"):
            clear_history()
            
        st.markdown("</div>", unsafe_allow_html=True)
    
    # Main content area
    st.markdown("<h1 class='main-header'>Text-to-SQL Assistant</h1>", unsafe_allow_html=True)
    
    # Display welcome screen if no conversation yet
    if st.session_state.show_welcome and not st.session_state.conversation_history:
        display_welcome_screen()
    
    # Two-column layout for main content
    if not compact_view:
        query_col, results_col = st.columns([2, 3])
    else:
        query_col = st
        results_col = st
    
    # Query input section
    with query_col:
        st.markdown("<h3 class='sub-header'>Enter your Query</h3>", unsafe_allow_html=True)
        
        # Model selection using radio buttons
        st.markdown("<div class='model-selector'>", unsafe_allow_html=True)
        st.markdown("**Select AI Model:**", unsafe_allow_html=True)
        model_option = st.radio(
            "Choose a model for SQL generation:",
            options=["o3-mini", "codestral-latest"],
            horizontal=True,
            label_visibility="collapsed",
            key="model_selection"
        )
        st.session_state.selected_model = model_option
        st.markdown("</div>", unsafe_allow_html=True)
        
        st.text_area(
            "Type your question in natural language:", 
            key="query_text", 
            height=100,
            placeholder="e.g., Show all customers who made purchases last month",
            on_change=update_query
        )
        
        col1, col2, col3 = st.columns([1, 1, 1])
        with col1:
            submit_pressed = st.button("Generate SQL", type="primary", use_container_width=True)
        with col2:
            clear_pressed = st.button("Clear", on_click=clear_inputs, use_container_width=True)
        with col3:
            if st.session_state.related_tables:
                st.download_button(
                    label="Export SQL",
                    data=st.session_state.response_json.get('query', '') if st.session_state.response_json else '',
                    file_name="generated_query.sql",
                    mime="text/plain",
                    use_container_width=True
                )
        
        # Schema explorer (visible in non-compact mode)
        if not compact_view and st.session_state.related_tables:
            display_schema_explorer(st.session_state.related_tables)
            
        st.markdown("</div>", unsafe_allow_html=True)
    
    # Handle submit action
    if submit_pressed and st.session_state.user_query.strip():
        with st.spinner(f"Analyzing your query with {st.session_state.selected_model} and generating SQL..."):
            response_json, related_tables = process_query(
                st.session_state.user_query, llm, retriever_engine, st.session_state.selected_model
            )
            
            # Update session state with results
            st.session_state.response_json = response_json
            st.session_state.related_tables = related_tables
            st.session_state.feedback_submitted = False
    
    # Results section
    with results_col:
        # Display most recent response if available
        if st.session_state.response_json:
            st.markdown("<h3 class='sub-header'>Results</h3>", unsafe_allow_html=True)
            
            # Show which model was used
            st.markdown(f"<span class='tag'>Generated with: {st.session_state.selected_model}</span>", unsafe_allow_html=True)
            
            if isinstance(st.session_state.response_json, dict):
                query = st.session_state.response_json.get('query')
                # Handle explicit False from LLM or empty queries
                if query and query !="FALSE":
                    sql_query = st.session_state.response_json.get('query', '')
                    st.code(sql_query, language="sql")
                else:
                    explanation = st.session_state.response_json.get('explanation', 'No explanation provided.')
                    st.markdown(f"{explanation}", unsafe_allow_html=True)
                
            # Show raw JSON if enabled
            if show_raw_json:
                with st.expander("Raw Response Data"):
                    st.json(st.session_state.response_json)
            
            # Schema explorer (in compact mode)
            if compact_view and st.session_state.related_tables:
                display_schema_explorer(st.session_state.related_tables)
                    
        
        # # Feedback section when there's a result
        # if st.session_state.response_json and not st.session_state.feedback_submitted:
        #     st.markdown("<h3 class='sub-header'> Feedback</h3>", unsafe_allow_html=True)
            
        #     # Quick feedback buttons
        #     st.markdown("Was this SQL query helpful?")
        #     col1, col2, col3 = st.columns([1, 1, 3])
        #     with col1:
        #         if st.button("👍 Yes", use_container_width=True):
        #             feedback_handler.record_feedback(
        #                 user_query=st.session_state.user_query,
        #                 sql_queries=st.session_state.response_json.get('query', '') if st.session_state.response_json else '',
        #                 feedback=f"Positive: The SQL query was helpful. Model used: {st.session_state.selected_model}"
        #             )
        #             st.session_state.feedback_submitted = True
        #             st.success("Thanks for your feedback!")
            
        #     with col2:
        #         if st.button("👎 No", use_container_width=True):
        #             st.session_state.feedback_negative = True
            
        #     # Detailed feedback form appears if negative feedback given
        #     if "feedback_negative" in st.session_state and st.session_state.feedback_negative:
        #         feedback_key = f"feedback_text_{int(time.time())}"  # Use a unique key with timestamp
        #         feedback = st.text_area("Please tell us what could be improved:", height=80, key=feedback_key)
                
        #         if st.button("Submit Detailed Feedback"):
        #             if feedback.strip():
        #                 feedback_handler.record_feedback(
        #                     user_query=st.session_state.user_query,
        #                     sql_queries=st.session_state.response_json.get('query', '') if st.session_state.response_json else '',
        #                     feedback=f"Negative: {feedback}. Model used: {st.session_state.selected_model}"
        #                 )
        #                 st.session_state.feedback_submitted = True
        #                 st.session_state.feedback_negative = False
        #                 st.success("Thanks for your detailed feedback! We'll use it to improve.")
        #                 # Don't try to clear the text area directly
        #             else:
        #                 st.warning("Please provide some feedback details.")
        #                 st.markdown("</div>", unsafe_allow_html=True)
    
    # Conversation history display
    if st.session_state.conversation_history and not st.session_state.show_welcome:
        st.markdown("<h3 class='sub-header'>Conversation History</h3>", unsafe_allow_html=True)
        
        # Display in reverse order with most recent at top, with the option to toggle
        display_order = st.radio("Display order:", ["Most recent first", "Oldest first"], horizontal=True)
        
        history_to_display = st.session_state.conversation_history.copy()
        if display_order == "Most recent first":
            history_to_display.reverse()
        
        for i, exchange in enumerate(history_to_display):
            display_conversation_message(exchange, i)
    
    # Display copyright at the bottom
    display_copyright()

if __name__ == "__main__":
    main()