from llama_index.core.response.notebook_utils import display_source_node

class Retriever:
    def retrieve(self, retriever_engine, query_str):
        retrieval_results = retriever_engine.retrieve(query_str)

        retrieved_text = []
        for res_node in retrieval_results:
            display_source_node(res_node, source_length=200)
            retrieved_text.append(res_node.text)

        return retrieved_text

    