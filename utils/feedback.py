class FeedbackHandler:
    def record_feedback(self, user_query, sql_queries, feedback):
        print(f"Recording feedback: {feedback} for query: {user_query}")