# Customer Support RAG Agent with Memory

An AI-powered customer support assistant using Retrieval-Augmented Generation (RAG) with Google Gemini, ChromaDB, and session-based conversation memory.

## Tech Stack

- **Backend**: Python 3.11 · FastAPI · Uvicorn
- **LLM**: Google Gemini API
- **Vector DB**: ChromaDB
- **Embeddings**: Sentence Transformers (`all-MiniLM-L6-v2`)
- **Validation**: Pydantic

## Quick Start

```bash
# 1. Create & activate virtual environment
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # macOS/Linux

# 2. Install dependencies
pip install -r requirements.txt

# 3. Configure environment
copy .env.example .env
# Edit .env and add your GEMINI_API_KEY

# 4. Run the server
uvicorn app.main:app --reload
```

## API Endpoints

| Method | Endpoint                    | Description              |
|--------|-----------------------------|--------------------------|
| GET    | `/`                         | Root welcome             |
| GET    | `/health`                   | Health check             |
| POST   | `/chat`                     | Send a message           |
| DELETE | `/sessions/{session_id}`    | Clear session memory     |

## Project Structure

```
app/
├── main.py              # FastAPI application factory
├── core/
│   ├── config.py         # Pydantic Settings
│   └── exceptions.py     # Custom exception hierarchy
├── api/
│   ├── routes.py         # Endpoint definitions
│   └── dependencies.py   # Dependency injection
├── services/             # Business logic layer
├── llm/                  # Gemini & Embedding wrappers
├── database/             # ChromaDB & Memory stores
├── models/               # Pydantic schemas
├── knowledge_base/       # Source documents
└── tests/                # Pytest test suite
```
