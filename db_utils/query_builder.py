class QueryGenerator:
    def generate(self, user_query, relevant_data):
        # Placeholder for LLM call
        print("Generating SQL for:", user_query)
        return [f"SELECT * FROM {table['name']}" for table in relevant_data]