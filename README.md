# Granthbodh

Granthbodh is a document question-answering application. Users can create an account, upload PDF, DOCX, and XLSX files, and ask questions about the content of their documents. Uploaded files are parsed into chunks, embedded with Google Gemini, and stored in PostgreSQL with pgvector for retrieval during chat.

The project contains:

- A FastAPI backend for authentication, document processing, retrieval-augmented generation (RAG), and conversation history.
- A React 19 and TypeScript frontend served by Vite.
- A PostgreSQL 15 database with the `pgvector` extension.
- Docker Compose configuration for running the full stack locally.

## Features

- Email and password signup and login.
- Access and refresh token authentication.
- Upload and parse PDF, DOCX, and XLSX documents.
- Generate embeddings for document chunks and store them in pgvector.
- Ask questions about uploaded documents.
- View paginated documents, conversations, and messages.
- Delete uploaded documents.
- Interactive API documentation through FastAPI.

## Architecture

```text
React/Vite frontend (:5173)
						 |
						 v
FastAPI backend (:8000) ---- Google Gemini API
						 |
						 v
PostgreSQL + pgvector (:5433)
```

## Requirements

For the Docker setup, install:

- Docker Engine
- Docker Compose v2
- A Google Gemini API key

For running services directly on the host, also install Python 3.12+, Node.js 22+, and PostgreSQL with pgvector.

## Quick Start with Docker

1. Create a `.env` file in the repository root:

	 ```dotenv
	 POSTGRES_USER=rag_user
	 POSTGRES_PASSWORD=change-this-password
	 POSTGRES_DB=rag_db
	 DATABASE_URL=postgresql://rag_user:change-this-password@localhost:5433/rag_db
	 GEMINI_API_KEY=your-gemini-api-key
	 HASH_SECRET_KEY=replace-with-a-long-random-secret
	 ```

	 `DATABASE_URL` is used when the backend runs outside Compose. Inside the Compose network, the backend receives its database URL automatically and connects to the `db` service.

2. Build and start the application:

	 ```bash
	 docker compose up --build
	 ```

3. Open the application at <http://localhost:5173>.

	 The backend is available at <http://localhost:8000>. Once the backend starts, it creates the `vector` extension and application tables if they do not already exist.

4. Stop the stack when finished:

	 ```bash
	 docker compose down
	 ```

	 Add `-v` only when you intentionally want to remove the persisted PostgreSQL volume and all local database data.

## Local Development

### Backend

Create and activate a virtual environment, then install the Python dependencies:

```bash
python3.12 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Start PostgreSQL with pgvector and configure the variables in `.env`. Then run the API:

```bash
python run.py
```

The API listens on <http://localhost:8000> with auto-reload enabled. Alternatively:

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Frontend

In a second terminal:

```bash
cd frontend
npm install
```

Create `frontend/.env` if the API is not available at the default configured URL:

```dotenv
VITE_API_URL=http://localhost:8000
```

Start the Vite development server:

```bash
npm run dev
```

Useful frontend commands:

```bash
npm run build    # Type-check and create a production build
npm run lint     # Run ESLint
npm run preview  # Preview the production build
```

## API Reference

The API is versioned under `/api/v1`.

| Method | Endpoint | Authentication | Purpose |
| --- | --- | --- | --- |
| `GET` | `/api/v1/health` | No | Check API health |
| `POST` | `/api/v1/users/signup` | No | Create an account and receive tokens |
| `POST` | `/api/v1/users/login` | No | Log in and receive tokens |
| `POST` | `/api/v1/users/refresh` | No | Refresh an access token |
| `POST` | `/api/v1/documents/upload` | Bearer token | Upload and index a document |
| `GET` | `/api/v1/documents?page=1` | Bearer token | List the current user's documents |
| `POST` | `/api/v1/documents/delete/{document_id}` | Bearer token | Delete a document |
| `POST` | `/api/v1/rag/getAnswer` | Bearer token | Ask a question, optionally in a conversation |
| `GET` | `/api/v1/rag/conversations?page=1` | Bearer token | List conversations |
| `GET` | `/api/v1/rag/messages?conversation_id={id}&page=1` | Bearer token | List messages in a conversation |

Interactive documentation is available at:

- Swagger UI: <http://localhost:8000/docs>
- ReDoc: <http://localhost:8000/redoc>
- OpenAPI JSON: <http://localhost:8000/api/v1/openapi.json>

### Example Requests

Create an account:

```bash
curl -X POST http://localhost:8000/api/v1/users/signup \
	-H 'Content-Type: application/json' \
	-d '{"email":"reader@example.com","password":"use-a-strong-password"}'
```

Upload a document using the returned access token:

```bash
curl -X POST http://localhost:8000/api/v1/documents/upload \
	-H "Authorization: Bearer ACCESS_TOKEN" \
	-F "file=@./documents/handbook.pdf"
```

Ask a question:

```bash
curl -X POST http://localhost:8000/api/v1/rag/getAnswer \
	-H "Authorization: Bearer ACCESS_TOKEN" \
	-H 'Content-Type: application/json' \
	-d '{"question":"What are the key points in this document?","conversation_id":null}'
```

## Configuration

The backend reads environment variables from the process environment and from a root `.env` file. The important settings are:

| Variable | Required | Description |
| --- | --- | --- |
| `POSTGRES_USER` | Yes | PostgreSQL username |
| `POSTGRES_PASSWORD` | Yes | PostgreSQL password |
| `POSTGRES_DB` | Yes | PostgreSQL database name |
| `DATABASE_URL` | Yes | SQLAlchemy database connection URL |
| `GEMINI_API_KEY` | For RAG | Google Gemini API key used for embeddings and answers |
| `HASH_SECRET_KEY` | Yes | Secret used for password/token-related security settings |
| `ALGORITHM` | No | JWT algorithm; defaults to `HS256` |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | No | Access-token lifetime; defaults to `30` |
| `REFRESH_TOKEN_EXPIRE_DAYS` | No | Refresh-token lifetime; defaults to `7` |

Do not commit `.env` files or API keys to source control.

## Database and Migrations

The Compose database service exposes PostgreSQL on host port `5433` and mounts the `migrations/` directory at `/migrations` inside the database container. The application also creates the pgvector extension and SQLAlchemy tables during startup.

The SQL migration files can be applied manually when needed. For example:

```bash
docker compose exec db psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" \
	-f /migrations/003_add_created_at.sql
```

Run migrations in order and verify the target database before applying them to an environment containing important data.

## Project Layout

```text
app/
	core/                  Settings, database, security, and dependencies
	modules/users/         Signup, login, and token refresh
	modules/document/      Upload, parsing, chunking, and indexing
	modules/rag/           Retrieval, answers, and conversation history
frontend/
	src/pages/             Authentication and chat screens
migrations/              SQL migration scripts
docker-compose.yml       Local database, API, and frontend services
```

## Troubleshooting

- **The API cannot connect to PostgreSQL:** confirm the database is healthy and that host-based development uses port `5433`; containers use the `db:5432` connection configured by Compose.
- **Document uploads fail:** only `.pdf`, `.docx`, and `.xlsx` files with their expected content types are accepted.
- **Answers or uploads fail during embedding:** confirm `GEMINI_API_KEY` is set and valid.
- **The frontend cannot reach the API:** check `VITE_API_URL`, and make sure the API is running on port `8000`.

## TODO

- [x] Load more in fronend.
- [ ] Better auth than simple email password.
- [ ] Streaming response for large documents.
- [x] Notification to user like uploading feedback, error notification in frontend.
- [x] Loader when uploading documents.

## License

No license has been specified for this repository yet.
