import os


from dotenv import load_dotenv
# from constants import DEFAULT_TOP_K
from llama_index.core import Settings
from llama_index.embeddings.mistralai import MistralAIEmbedding
from llama_index.core import SimpleDirectoryReader, StorageContext, VectorStoreIndex
from llama_index.vector_stores.milvus import MilvusVectorStore

# Load the environment variables
load_dotenv()

class BaseEmbedding:
    def __init__(self):
        self.embed_model = MistralAIEmbedding(
            "mistral-embed", api_key=os.getenv("MISTRAL_API_KEY")
        )
        self.vector_store = MilvusVectorStore(
            uri="./milvus.db",
            collection_name="text_collection",
            overwrite=False,
            dim=1536,
        )

    def embed_text(self, text: str) -> list:
        """
        Embed a given text string.
        """
        return self.embed_model.get_text_embedding(text)


    def embed_directory(self, file_path: str) -> list:
        self.storage_context = StorageContext.from_defaults(
            vector_store=self.vector_store
            )
        self.documents = SimpleDirectoryReader(file_path).load_data()
        self.index = VectorStoreIndex.from_documents(
            self.documents, storage_context=self.storage_context
        )

        self.retriever_engine = self.index.as_retriever(similarity_top_k=5)

        return self.retriever_engine
    

#Example code for testing
# base_embedding = BaseEmbedding()
# print(base_embedding.embed_text("Hello, how are you?"))
# print(base_embedding.embed_directory("data"))
