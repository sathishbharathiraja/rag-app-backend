# RAG Backend

This is the backend for the RAG App, built with FastAPI, PostgreSQL, MongoDB, and Gemini 3.6 Flash.

## Setup

1. Copy the `.env.example` file to a new file named `.env`:
   ```bash
   cp .env.example .env
   ```
2. Fill in the required API keys in the `.env` file (especially `GEMINI_API_KEY` and `MONGO_URI`).
3. Run the application using Docker Compose:
   ```bash
   docker-compose up -d --build
   ```

## Stack
- Python / FastAPI
- Google Gemini 3.6 Flash (Text Generation)
- all-MiniLM-L6-v2 (Local Embeddings for RAG)
- PostgreSQL & pgvector (Vector Database)
- MongoDB (Historical data)
