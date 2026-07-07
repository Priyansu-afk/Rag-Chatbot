# NeuroDocs AI

NeuroDocs AI is a PDF-based Retrieval-Augmented Generation (RAG) chatbot that lets users upload documents and ask questions in natural language. It retrieves relevant chunks with LangChain, Sentence Transformers embeddings, and FAISS, then generates cited answers with a local Ollama LLM.

## Tech Stack

- Streamlit
- LangChain
- Ollama
- FAISS
- Sentence Transformers
- SQLite + SQLAlchemy
- bcrypt

## Features

- User signup and login
- PDF upload and chunking
- Vector search over document content
- Cited answers from retrieved context
- Conversation history
- Per-user document and index storage

## Setup

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Create a `.env` file with your local settings.

3. Run the app:
   ```bash
   streamlit run app.py
   ```