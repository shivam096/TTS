class Retriever:
    def retrieve(self, retriever_engine, query_str):
        
        retrieval_results = retriever_engine.retrieve(query_str)

        retrieved_text = []
        for res_node in retrieval_results:
            retrieved_text.append(res_node.text)

        return retrieved_text
