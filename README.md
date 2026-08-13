# BigHammer RAG Backend

This is the backend for the BigHammer RAG (Retrieval-Augmented Generation) Application. It provides a highly scalable, asynchronous API for processing documents, converting them into mathematical embeddings, and generating intelligent answers using a hybrid AI architecture.

## 🏗️ Architecture

- **Framework:** FastAPI (Python)
- **Database:** PostgreSQL 16 with `pgvector` for high-speed similarity search
- **Embeddings AI:** Local `all-MiniLM-L6-v2` (HuggingFace) for private, zero-cost document embedding
- **Content Generation AI:** Google Gemini 1.5 Flash (via asynchronous REST API)
- **Document Processing:** LangChain (PyMuPDF, Docx2txt) with Markdown-aware text chunking

## 🚀 Key Features

1. **Fully Asynchronous:** Uses `asyncpg` and `aiohttp` to ensure the server never blocks during database queries or LLM generation.
2. **Hybrid AI Engine:** Uses a local, open-source model (MiniLM) to guarantee document privacy when generating vector coordinates, while leveraging a world-class cloud LLM (Gemini) strictly for writing the final response.
3. **Optimized Vector Search:** Uses the `<=>` Cosine Distance operator in PostgreSQL for lightning-fast semantic retrieval.

## 🛠️ Setup & Installation

### Option 1: Docker Compose (Recommended)
The entire application (Frontend, Backend, and Database) is orchestrated using Docker Compose. From the root directory, simply run:
```bash
docker-compose up -d --build
```
The backend API will automatically start at `http://localhost:8000`. You can view the interactive Swagger documentation at `http://localhost:8000/docs`.

### Option 2: Local Development
1. Create a virtual environment: `python -m venv .venv`
2. Activate the environment and install dependencies: `pip install -r requirements.txt`
3. Start a local PostgreSQL instance with the `pgvector` extension.
4. Rename `.env.example` to `.env` and fill in your credentials.
5. Run the server: `uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload`

## 📁 Project Structure

- `/app/api`: FastAPI route controllers (Auth, Chat, Documents)
- `/app/core`: Core configuration, database connection, and JWT security
- `/app/models`: SQLAlchemy ORM models
- `/app/services`: Business logic (RAG processing, Document chunking)
