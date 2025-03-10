import asyncio
import os
from dotenv import load_dotenv
from constants import DEFAULT_TOP_K
from llama_index.core import Settings
from llama_index.embeddings.mistralai import MistralAIEmbedding
from llama_index.core import SimpleDirectoryReader, StorageContext, VectorStoreIndex
from llama_index.vector_stores.milvus import MilvusVectorStore
from llama_index.core import load_index_from_storage


# Load the environment variables
load_dotenv()


try:
    asyncio.get_event_loop()
except RuntimeError:
    asyncio.set_event_loop(asyncio.new_event_loop())


class BaseEmbedding:
    def __init__(self, file_path: str):
        # Initialize embedding model
        self.embed_model = MistralAIEmbedding(
            "mistral-embed", api_key=os.getenv("MISTRAL_API_KEY")
        )

        embed_dim = 1024

        Settings.embed_model = self.embed_model
        self.persist_dir = "./vector_store/persisting_dir"

        # Clear lock file if it exists
        lock_file = "vector_store/.milvus.db.lock"
        if os.path.exists(lock_file):
            os.remove(lock_file)

        # Initialize vector store with correct dimensions
        vector_store = MilvusVectorStore(
            uri="./vector_store/milvus.db",
            collection_name="text_collection",
            dim=embed_dim,
            overwrite=False,
        )

        if not os.path.exists(self.persist_dir):
            print("Creating new index...")

            # For first-time setup, we'll overwrite the collection
            vector_store = MilvusVectorStore(
                uri="./vector_store/milvus.db",
                collection_name="text_collection",
                dim=embed_dim,
                overwrite=True,
            )

            # Set up storage context
            storage_context = StorageContext.from_defaults(vector_store=vector_store)

            # Load documents and create index
            documents = SimpleDirectoryReader(file_path).load_data()
            self.index = VectorStoreIndex.from_documents(
                documents, storage_context=storage_context
            )

            # Persist the storage context
            self.index.storage_context.persist(persist_dir=self.persist_dir)

        else:
            print("Loading existing index...")

            # Create storage context with the vector store
            storage_context = StorageContext.from_defaults(
                persist_dir=self.persist_dir, vector_store=vector_store
            )

            # Load the index with the storage context
            self.index = load_index_from_storage(storage_context)

        # Create a retriever engine once during initialization
        self.retriever_engine = self.index.as_retriever(similarity_top_k=DEFAULT_TOP_K)

    def embed_text(self, text: str) -> list:
        """
        Embed a given text string.
        """
        return self.embed_model.get_text_embedding(text)

    def get_retriever_engine(self):
        """
        Get the retriever engine.
        """
        return self.retriever_engine

    def get_relevant_nodes(self, query: str, similarity_threshold: float = 0.3):
        """
        Get nodes relevant to a query with relevance filtering.

        Args:
            query: The user query
            similarity_threshold: Minimum similarity score to include a result

        Returns:
            tuple: (relevant_nodes, is_relevant_query)
        """
        # Get retrieval results
        retrieval_results = self.retriever_engine.retrieve(query)

        # Filter by similarity threshold
        relevant_nodes = [
            node
            for node in retrieval_results
            if hasattr(node, "score") and node.score >= similarity_threshold
        ]

        # Check if this query is relevant to our domain
        # If the top result has a very low score, the query is likely irrelevant
        is_relevant_query = len(relevant_nodes) > 0 and relevant_nodes[0].score >= 0.5

        return relevant_nodes, is_relevant_query
