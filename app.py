import streamlit as st
import json
from utils.retriever import Retriever
from utils.feedback import FeedbackHandler
from prompts.general_SQL import GENERAL_SQL
from prompts.text_to_sql import TEXT_TO_SQL
from llm_integration.llm_core import LLMCore
from db_utils.query_builder import QueryGenerator
from llm_integration.embeddings import BaseEmbedding
import streamlit.components.v1 as components
import time
from datetime import datetime
from chatbot.SQLChatbot import SQLChatbot

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
    .loading-schema {
        background-color: #FEF3C7;
        border-left: 3px solid #F59E0B;
        padding: 1rem;
        margin: 1rem 0;
    }
</style>
""", unsafe_allow_html=True)

@st.cache_resource
def get_sql_chatbot():
    return SQLChatbot()

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
        st.session_state.selected_model = "openai"
    if "schema_analyzing" not in st.session_state:
        st.session_state.schema_analyzing = False
    if "real_time_schema" not in st.session_state:
        st.session_state.real_time_schema = None
    if "last_analyzed_query" not in st.session_state:
        st.session_state.last_analyzed_query = ""

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
    st.session_state.schema_analyzing = False
    st.session_state.real_time_schema = None
    st.session_state.last_analyzed_query = ""

def clear_history():
    """Clear the conversation history"""
    st.session_state.conversation_history = []
    
def fetch_schema_for_query(query, chatbot):
    """Fetch schema information for a query without generating the SQL yet"""
    if not query.strip():
        return None, "No query provided"
    
    # Get the model from session state
    model_name = st.session_state.selected_model
    chatbot.selected_model = model_name
    
    # Get related tables using the chatbot's retriever
    related_tables, status_message = chatbot.process_query(query.strip())
    
    return related_tables, status_message

def process_query(query, chatbot, schema_already_fetched=False):
    """Process a user query and return results using SQLChatbot"""
    if not query.strip():
        return None, None
    
    # Get the model from session state
    model_name = st.session_state.selected_model
    chatbot.selected_model = model_name
    
    # Get related tables using the chatbot's retriever if not already fetched
    if schema_already_fetched and st.session_state.real_time_schema:
        related_tables = st.session_state.real_time_schema
        status_message = "Schema already analyzed"
    else:
        related_tables, status_message = chatbot.process_query(query.strip())
    
    # Generate the appropriate prompt based on the tables
    prompt = chatbot.generate_prompt(query.strip(), related_tables)
    
    # Get response from the LLM
    response = chatbot.llm.model_call(prompt, model=model_name)
    
    try:
        response_json = json.loads(response)
    except json.JSONDecodeError:
        response_json = {"explanation": response, "query": "FALSE"}
    
    # Add to conversation history with timestamp
    st.session_state.conversation_history.append({
        "query": query,
        "response": response_json,
        "tables": related_tables,
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "model": model_name,
        "status": status_message
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
    
    # Display status message if available
    if 'status' in exchange and exchange['status']:
        st.info(exchange['status'])
    
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
    if isinstance(exchange['response'], dict) and exchange['response'].get('query', '') != "FALSE":
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

def display_schema_explorer(tables, is_loading=False):
    """Display a visual explorer for database schema"""
    if not tables and not is_loading:
        st.info("No schema information available yet. Submit a query to explore related tables.")
        return
    
    if is_loading:
        st.info("🔍 Analyzing query and identifying relevant tables...")
        return
        
    st.markdown("<h3 class='sub-header'>Database Schema Explorer</h3>", unsafe_allow_html=True)
    
    for i, table in enumerate(tables):
        # Check if table is a dictionary or a string
        if isinstance(table, dict):
            table_name = table.get('table_name', f'Table {i+1}')
        else:
            # If it's a string or other type, use it directly or provide a default
            table_name = str(table) if table else f'Table {i+1}'
            
        with st.expander(f"📊 {table_name}", expanded=True):  # Auto-expand for better visibility
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
    # Initialize SQL chatbot
    chatbot = get_sql_chatbot()
    
    # Initialize session state
    initialize_session_state()
    
    # Sidebar setup
    with st.sidebar:
        st.markdown("<h2 style='text-align: center; color: #1E3A8A;'>💬 Text-to-SQL Assistant</h2>", unsafe_allow_html=True)
        st.markdown("<div class='sidebar-content'>", unsafe_allow_html=True)
        
        # Configuration options
        show_raw_json = st.checkbox("Show Raw JSON", value=False)
        compact_view = st.checkbox("Compact View", value=False)
        real_time_schema = st.checkbox("Real-time Schema Analysis", value=True, help="Show schema as you type your query")
        
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
            options=["openai", "mistralai"],
            horizontal=True,
            label_visibility="collapsed",
            key="model_selection"
        )
        st.session_state.selected_model = model_option
        st.markdown("</div>", unsafe_allow_html=True)
        
        # Query text area
        query_input = st.text_area(
            "Type your question in natural language:", 
            key="query_text", 
            height=100,
            placeholder="e.g., Show all customers who made purchases last month"
        )
        
        # Buttons for actions
        col1, col2, col3 = st.columns([1, 1, 1])
        with col1:
            submit_pressed = st.button("Generate SQL", type="primary", use_container_width=True, on_click=update_query)
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
        
        # Real-time schema analysis area
        if real_time_schema:
            schema_area = st.container()
            
            # Only analyze if query has changed and has sufficient content
            current_query = query_input.strip()
            if (current_query and len(current_query) > 10 and 
                current_query != st.session_state.last_analyzed_query):
                
                with schema_area:
                    # Show loading state
                    with st.spinner("Analyzing schema..."):
                        st.session_state.schema_analyzing = True
                        display_schema_explorer(None, is_loading=True)
                        
                        # Fetch schema information
                        try:
                            # Update the last analyzed query
                            st.session_state.last_analyzed_query = current_query
                            tables, _ = fetch_schema_for_query(current_query, chatbot)
                            st.session_state.real_time_schema = tables
                            st.session_state.schema_analyzing = False
                            
                            # Clear the area and show the schema
                            schema_area.empty()
                            if tables:
                                with schema_area:
                                    display_schema_explorer(tables)
                        except Exception as e:
                            schema_area.error(f"Error analyzing schema: {str(e)}")
                            st.session_state.schema_analyzing = False
            elif st.session_state.real_time_schema and not st.session_state.schema_analyzing:
                # Display previously analyzed schema if available
                with schema_area:
                    display_schema_explorer(st.session_state.real_time_schema)
        
        # Show schema explorer for non-compact view and no real-time schema
        elif not compact_view and st.session_state.related_tables:
            display_schema_explorer(st.session_state.related_tables)
            
        st.markdown("</div>", unsafe_allow_html=True)
    
    # Handle submit action
    if submit_pressed and st.session_state.user_query.strip():
        with st.spinner(f"Analyzing your query with {st.session_state.selected_model} and generating SQL..."):
            # If real-time schema is enabled, use the already fetched schema
            schema_already_fetched = real_time_schema and st.session_state.real_time_schema is not None
            
            response_json, related_tables = process_query(
                st.session_state.user_query, chatbot, schema_already_fetched=schema_already_fetched
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
                if query and query != "FALSE":
                    sql_query = st.session_state.response_json.get('query', '')
                    st.code(sql_query, language="sql")
                else:
                    explanation = st.session_state.response_json.get('explanation', 'No explanation provided.')
                    st.markdown(f"{explanation}", unsafe_allow_html=True)
                
            # Show raw JSON if enabled
            if show_raw_json:
                with st.expander("Raw Response Data"):
                    st.json(st.session_state.response_json)
            
            # Schema explorer (in compact mode) - only show if not already shown by real-time analysis
            if compact_view and st.session_state.related_tables and not real_time_schema:
                display_schema_explorer(st.session_state.related_tables)
    
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