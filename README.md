# TTS: Text-to-SQL Library

A Python library for generating SQL queries from natural language using a Retrieval Augmented Generation (RAG) approach with table schema integration.

## Features

- **LLM-Powered Query Generation:**  
  Generate formatted SQL queries using a language model. See [`LLMCore`](llm_integration/llm_core.py) and [`QueryGenerator`](db_utils/query_builder.py).

- **Vector-Based Retrieval:**  
  Retrieve context and schema information using embeddings and a Milvus vector store. See [`BaseEmbedding`](llm_integration/embeddings.py) and [`Retriever`](utils/retriever.py).

- **Google Drive File Downloading:**  
  Download and extract files directly from Google Drive. See [`GoogleDriveDownloader`](utils/google_drive_downloader.py).

- **Feedback Handling:**  
  Record and process user feedback for query generation. See [`FeedbackHandler`](utils/feedback.py).

## Requirements

- Python 3.x
- Required libraries (e.g., `openai`, `langchain`, `gdown`, `faiss`, `llama_index`, `dotenv`, etc.)

# Implementation

Still under works