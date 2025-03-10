import json
import logging


from functools import lru_cache
from contextlib import contextmanager
from utils.retriever import Retriever
from utils.handler import load_metadata
from db_utils.validator import Validator
from utils.feedback import FeedbackHandler
from prompts.general_SQL import GENERAL_SQL
from prompts.text_to_sql import TEXT_TO_SQL
from llm_integration.llm_core import LLMCore
from db_utils.query_builder import QueryGenerator
from typing import Dict, Tuple, Optional, List, Any
from llm_integration.embeddings import BaseEmbedding

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Command dispatch table
COMMANDS = {
    'exit': lambda _: ('exit', None),
    'help': lambda _: ('help', None),
    'change model': lambda _: ('change_model', None),
}

class SQLChatbot:
    """Enhanced Text-to-SQL chatbot with optimized resource management."""
    
    def __init__(self):
        """Initialize required components lazily."""
        self._llm = None
        self._embedding = None
        self._retriever = None
        self._validator = None
        self._feedback_handler = None
        self._retriever_engine = None
        self.selected_model = None
        
    @property
    def llm(self) -> LLMCore:
        """Lazy initialization of LLM component."""
        if self._llm is None:
            self._llm = LLMCore()
        return self._llm
    
    @property
    def embedding(self) -> BaseEmbedding:
        """Lazy initialization of embedding component."""
        if self._embedding is None:
            self._embedding = BaseEmbedding(file_path="meta_data")
        return self._embedding
    
    @property
    def retriever_engine(self):
        """Lazy initialization of retriever engine."""
        if self._retriever_engine is None:
            self._retriever_engine = self.embedding.get_retriever_engine()
        return self._retriever_engine
    
    @property
    def retriever(self) -> Retriever:
        """Lazy initialization of retriever component."""
        if self._retriever is None:
            self._retriever = Retriever()
        return self._retriever
    
    @property
    def validator(self) -> Validator:
        """Lazy initialization of validator component."""
        if self._validator is None:
            self._validator = Validator()
        return self._validator
    
    @property
    def feedback_handler(self) -> FeedbackHandler:
        """Lazy initialization of feedback handler component."""
        if self._feedback_handler is None:
            self._feedback_handler = FeedbackHandler()
        return self._feedback_handler

    def select_model(self) -> str:
        """Select a model provider from available options."""
        valid_models = ["openai", "mistralai"]
        
        while True:
            model_selection = input(f"Select a model ({', '.join(valid_models)}): ").strip().lower()
            
            if model_selection in valid_models:
                self.selected_model = model_selection
                logger.info(f"Selected model: {self.selected_model}")
                return self.selected_model
            else:
                logger.warning(f"Invalid model selection: {model_selection}")
                print(f"Invalid model selection. Please choose from: {', '.join(valid_models)}")
    
    @contextmanager
    def handle_exceptions(self, user_query: str):
        """Context manager for exception handling."""
        try:
            yield
        except json.JSONDecodeError as e:
            logger.error(f"JSON parsing error: {str(e)}")
            print("\nThe model response couldn't be parsed as JSON. Here's the raw response:")
        except ConnectionError as e:
            logger.error(f"Connection error: {str(e)}")
            print("\nConnection error. Please check your network and try again.")
        except Exception as e:
            logger.error(f"Error processing query '{user_query}': {str(e)}")
            print(f"\nI encountered an error: {str(e)}")
            print("Please try rephrasing your question or type 'help' for examples.")
    
    def display_help(self):
        """Display help information."""
        print("\nAvailable commands:")
        print("- 'exit': Exit the chatbot")
        print("- 'change model': Switch to a different model")
        print("- 'help': Display this help message")
        
        print("\nExample queries:")
        print("- List all employees in the marketing department.")
        print("- Show total sales grouped by region for the last quarter.")
        print("- Retrieve customer orders placed in the past month.")
    
    @lru_cache(maxsize=100)
    def process_query(self, user_query: str) -> Tuple[Any, Optional[str]]:
        """Process user query with caching for repeated queries."""
        return self.retriever.process_query(
            retriever_engine=self.retriever_engine, 
            user_query=user_query
        )
    
    def generate_prompt(self, user_query: str, related_tables: List[str]) -> str:
        """Generate appropriate prompt based on retrieved tables."""
        if not related_tables:
            return GENERAL_SQL.format(question=user_query)
        else:
            return TEXT_TO_SQL.format(
                question=user_query, 
                table_schemas=related_tables
            )
    
    def validate_sql(self, sql_query: str) -> Tuple[bool, Optional[str]]:
        """Validate the generated SQL query."""
        try:
            return self.validator.validate_query(sql_query)
        except Exception as e:
            logger.warning(f"SQL validation error: {str(e)}")
            return False, f"Validation error: {str(e)}"
    
    def collect_feedback(self, user_query: str, response: str):
        """Collect and record user feedback."""
        print("\nWas this response helpful? (yes/no)")
        feedback = input().lower()
        if feedback in ["yes", "y", "no", "n"]:
            self.feedback_handler.record_feedback(
                user_query, 
                response, 
                feedback in ["yes", "y"]
            )
    
    def handle_command(self, user_input: str) -> Tuple[str, Any]:
        """Handle special commands using command pattern."""
        user_input_lower = user_input.lower()
        
        # Check command dispatch table
        for cmd, handler in COMMANDS.items():
            if user_input_lower == cmd:
                return handler(user_input)
        
        # If no command matches, treat as regular query
        return ('query', user_input)
    
    def process_sql_response(self, response: str, user_query: str):
        """Process and display the SQL response."""
        parsed_response = json.loads(response)
        
        # Extract SQL query if it exists in the response
        sql_query = parsed_response.get("query", "")
        if sql_query and sql_query != "FALSE":
            print("\nGenerated SQL Query:")
            print(f"{sql_query}")
            
            # # Validate the SQL query
            # is_valid, validation_message = self.validate_sql(sql_query)
            # if not is_valid:
            #     print(f"\nWarning: {validation_message}")
        else:
            print("\nExplanation:")
            print(parsed_response.get("explanation", "No explanation provided."))
        
        # Display the full response in a formatted way
        # print("\nFull Response:")
        # print(json.dumps(parsed_response, indent=2))
        
        # Collect feedback
        # self.collect_feedback(user_query, response)
    
    def run(self):
        """Main chatbot execution loop."""
        print("Welcome to the Text-to-SQL chatbot!")
        print("Type 'exit' to quit, 'help' for more information.\n")
        
        # Initial model selection
        self.select_model()
        
        while True:
            user_input = input("\nEnter your query (or type 'help' to get more information): ").strip()
            
            if not user_input:
                print("Please enter a user query.")
                continue
            
            # Process command or query
            cmd_type, cmd_data = self.handle_command(user_input)
            
            # Handle commands
            if cmd_type == 'exit':
                print("Goodbye!")
                break
            elif cmd_type == 'help':
                self.display_help()
                continue
            elif cmd_type == 'change_model':
                self.select_model()
                continue
            
            # Handle regular query
            user_query = cmd_data
            with self.handle_exceptions(user_query):
                # Get related tables with improved retrieval
                related_tables, status_message = self.process_query(user_query)
                
                # Check if there was an issue with the query
                if status_message:
                    print(f"\n{status_message}")
                    print("Do you still want to proceed with this query? (yes/no)")
                    proceed = input().lower()
                    if proceed not in ["yes", "y"]:
                        continue
                
                # Generate prompt and get response
                prompt = self.generate_prompt(user_query, related_tables)
                print("\nGenerating SQL query...")
                response = self.llm.model_call(prompt, model=self.selected_model)
                
                # Process response
                try:
                    self.process_sql_response(response, user_query)
                except json.JSONDecodeError:
                    # If response is not valid JSON, display it as is
                    print(f"\nBot: {response}")
    
    def cleanup(self):
        """Clean up resources when chatbot is done."""
        # Close any open connections or resources
        logger.info("Cleaning up resources...")
        # Implementation depends on what resources need cleanup