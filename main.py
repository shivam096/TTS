import json
from pprint import pprint
from utils.retriever import Retriever
from utils.handler import load_metadata
from db_utils.validator import Validator
from utils.feedback import FeedbackHandler
from prompts.general_SQL import GENERAL_SQL
from llm_integration.llm_core import LLMCore
from db_utils.query_builder import QueryGenerator
from llm_integration.embeddings import BaseEmbedding


def main():
    """Enhanced chatbot with better user interaction."""

    # Initialize BaseEmbedding once with the directory path
    llm = LLMCore()
    base_embedding = BaseEmbedding(file_path="meta_data")
    retriever_engine = base_embedding.get_retriever_engine()
    retriever = Retriever()
    feedback_handler = FeedbackHandler()

    print("Welcome to the Text-to-SQL chatbot!")
    print("Type 'exit' to quit, 'help' for example questions.\n")

    while True:
        try:
            user_query = input("Enter your query : ").strip()

            if user_query.lower() == "exit":
                print("Goodbye!")
                break

            if user_query.lower() == "help":
                print("\nExample queries:")
                print("- List all employees in the marketing department.")
                print("- Show total sales grouped by region for the last quarter.")
                print("- Retrieve customer orders placed in the past month.")
                continue

            if not user_query:
                print("Please enter a user query.")
                continue

            prompt = GENERAL_SQL.format(question=user_query)

            response = llm.model_call(prompt)

            txt = retriever.retrieve(
                retriever_engine=retriever_engine, query_str=user_query
            )

            related_tables = ", ".join(txt)

            pprint(json.dumps(json.loads(response)))

        except Exception as e:
            print(f"\nBot: I encountered an error: {str(e)}")
            print("Please try rephrasing your question or type 'help' for examples.")


# if __name__ == "__main__":
#     chatbot()

#     txt = retriever(retriever_engine=retriever_engine, query_str=user_query)


#     # feedback_handler.record_feedback(user_query, None, None)

if __name__ == "__main__":
    main()
