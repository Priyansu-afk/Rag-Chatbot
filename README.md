# NeuroDocs AI

NeuroDocs AI is a PDF-based Retrieval-Augmented Generation (RAG) chatbot that helps users upload documents and ask questions in natural language. The application retrieves the most relevant document chunks using Sentence Transformers embeddings and FAISS, then generates cited answers through a local Ollama model.

## Overview

The project is designed as a private, document-aware assistant with per-user data isolation. Each user can upload PDFs, query the content conversationally, and review source-backed responses with page-level citations.

## Key Features

- User authentication with signup and login
- PDF ingestion, text chunking, and vector indexing
- Semantic search over uploaded documents
- AI-generated answers grounded in retrieved context
- Source citations with document name and page number
- Conversation history stored in SQLite
- Per-user upload and vector store directories
- Document insight tools for summaries, FAQs, key points, and topics

## Tech Stack

- Streamlit for the web interface
- LangChain for orchestration
- Ollama for local LLM inference
- FAISS for vector search
- Sentence Transformers for embeddings
- SQLite and SQLAlchemy for persistence
- bcrypt for password hashing
- Plotly for dashboard visualizations

## How It Works

1. A user uploads one or more PDF files.
2. The PDFs are parsed and split into smaller chunks.
3. Each chunk is converted into embeddings and stored in FAISS.
4. When the user asks a question, the system retrieves the most relevant chunks.
5. LangChain sends the context and conversation history to the local LLM.
6. The model returns a grounded answer with citations from the uploaded documents.

## Setup

### Prerequisites

- Python 3.10+
- Ollama installed and running locally

### Installation

```bash
pip install -r requirements.txt
```

### Environment Variables

Create a `.env` file in the project root with the following values:

```env
DATABASE_URL=sqlite:///database.db
SESSION_SECRET=your_session_secret_here
OLLAMA_MODEL=phi3
```

### Run the App

```bash
streamlit run app.py
```

## Project Structure

```text
app.py                Main Streamlit entry point
auth/                 Login, signup, and password utilities
database/             SQLAlchemy database setup and models
rag/                  Chunking, embeddings, vector search, and chatbot logic
ui/                   Dashboard components and styling
uploads/              User PDF uploads
vectorstore/          Per-user FAISS indexes
```

## Notes

- Uploaded files and vector indexes are stored per user.
- The repository should not include `.env`, `database.db`, `uploads/`, or `vectorstore/`.
- The local LLM runs through Ollama, so no external API key is required for inference.
