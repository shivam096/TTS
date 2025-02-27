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

class BaseEmbedding:
    def __init__(self, file_path: str):
        # Initialize embedding model
        self.embed_model = MistralAIEmbedding(
            "mistral-embed", api_key=os.getenv("MISTRAL_API_KEY")
        )
        # Initialize vector store
        self.vector_store = MilvusVectorStore(
            uri="./milvus.db",
            collection_name="text_collection",
            overwrite=True,
            dim=1536,
        )

        self.persist_dir = "./persisting_dir"

        if not os.path.exists(self.persist_dir):
            # Set up storage context and load documents
            self.storage_context = StorageContext.from_defaults(
                vector_store=self.vector_store
            )

            self.documents = SimpleDirectoryReader(file_path).load_data()

            self.index  = VectorStoreIndex.from_documents(
                self.documents, storage_context=self.storage_context
            )

            self.index.storage_context.persist(persist_dir=self.persist_dir)
        
        else:
            self.index  = load_index_from_storage(
                StorageContext.from_defaults(
                    persist_dir=self.persist_dir, vector_store=self.vector_store
                )
                )
        
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
