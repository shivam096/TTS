from db_utils.query_builder import QueryGenerator
from db_utils.validator import Validator
from utils.feedback import FeedbackHandler
from utils.handler import load_metadata
from utils.retriever import Retriever


def main():

    retriever = Retriever()
    query_generator = QueryGenerator()
    validator = Validator()
    feedback_handler = FeedbackHandler()

    user_query = input("Enter your natural language query: ")

    query_str = "Using examples from video, explain the architecture of this building"

    img, txt = retriever(retriever_engine=retriever_engine, query_str=query_str)

    # relevant_data = retriever.retrieve(retriever_engine,user_query)
    # sql_queries = query_generator.generate(user_query, relevant_data)

    # for query in sql_queries:
    #     if validator.validate(query):
    #         print("Generated Query:", query)

    # feedback = input("Was this helpful? (yes/no): ")
    feedback_handler.record_feedback(user_query, sql_queries, feedback)

if __name__ == "__main__":
    main()