from constants import SIMILARITY_THRESHOLD, DOMAIN_SIMILARITY_THRESHOLD


class Retriever:
    def retrieve(self, retriever_engine, query_str):
        """
        Retrieve relevant documents based on query with similarity filtering.

        Args:
            retriever_engine: The engine to use for retrieval
            query_str: The user's query
            similarity_threshold: Minimum similarity score for relevance

        Returns:
            tuple: (retrieved_text, is_relevant_query)
        """
        # Get retrieval results
        retrieval_results = retriever_engine.retrieve(query_str)

        # Filter by similarity threshold
        relevant_nodes = [
            node
            for node in retrieval_results
            if hasattr(node, "score") and node.score >= SIMILARITY_THRESHOLD
        ]

        # Check if this query is relevant to our domain
        # If the top result has a very low score, the query is likely irrelevant
        is_relevant_query = len(relevant_nodes) > 0 and (
            not hasattr(relevant_nodes[0], "score")
            or relevant_nodes[0].score >= DOMAIN_SIMILARITY_THRESHOLD
        )

        # Extract text from nodes
        retrieved_text = []
        for node in relevant_nodes:
            retrieved_text.append(node.text)

        return retrieved_text, is_relevant_query

    def process_query(self, retriever_engine, user_query):
        """
        Process user query and provide appropriate response based on relevance.

        Args:
            retriever_engine: The retrieval engine to use
            user_query: The user's query

        Returns:
            tuple: (retrieved_text, status_message)
                retrieved_text: List of retrieved texts or empty list
                status_message: Message about query relevance or None if query is valid
        """
        # Get relevant text and check query relevance
        retrieved_text, is_relevant_query = self.retrieve(retriever_engine, user_query)

        # Case 1: Query is irrelevant to the domain
        if not is_relevant_query:
            return (
                [],
                "I don't understand how that relates to the database. Please try a query about customer data, sales, or inventory.",
            )

        # Case 2: Query is relevant but no good matches found
        if not retrieved_text:
            return (
                [],
                "I understand your query, but I couldn't find relevant information in the database. Could you rephrase or try a different query?",
            )

        # Case 3: Relevant information found
        return retrieved_text, None
