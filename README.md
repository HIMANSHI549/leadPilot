# LeadPilot AI

A beginner-friendly mini CRM that demonstrates LLM APIs, RAG with pgvector, SQL-backed tool calling, and simple preference memory.

The app is a Streamlit project. There is no separate React frontend in this first version.

## What it does

- **Lead Dashboard** — create, edit, delete, and filter sales leads in PostgreSQL.
- **Chat with Documents** — upload a PDF, chunk it, store embeddings, and answer questions with sources.
- **AI Sales Assistant** — the model may request Python tools such as `find_stale_leads`, `get_lead_details`, and `draft_followup_email`. Your code validates arguments and runs the functions.
- **Memory and History** — conversations and an email-tone preference persist in PostgreSQL.

## Architecture

```
PDF → text chunks → embeddings → PostgreSQL + pgvector
Question → question embedding → nearest chunks → LLM answer with sources

User question → LLM selects a tool → Python validates and executes it → LLM explains the result
```

`app.py` is navigation only. Database access lives in `src/database.py` and `src/lead_service.py`. LLM calls live in `src/llm_service.py`. Retrieval lives in `src/rag_service.py`. Tool handlers live in `src/tools.py`.

## Setup

### 1. Python

```powershell
cd leadpilot-ai
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

On macOS or Linux, activate with `source .venv/bin/activate`.

### 2. PostgreSQL with pgvector

The easiest local option is:

```powershell
docker compose up -d
```

You can also use a local PostgreSQL install or a hosted database, as long as the `vector` extension is available. After the database is running, the app creates tables automatically from `sql/schema.sql`.

### 3. Environment variables

```powershell
copy .env.example .env
```

Then edit `.env`. Set your API key and local PostgreSQL variables there; replace the placeholders in `.env.example` with values you choose:

```
OPENAI_API_KEY=your_api_key_here
POSTGRES_USER=replace_with_local_username
POSTGRES_PASSWORD=replace_with_local_password
POSTGRES_DB=leadpilot
```

Set `DATABASE_URL` to the connection string for that local database. Keep all real values in `.env` and never commit that file.

Do not commit `.env` or paste a real API key into GitHub. `.env.example` contains placeholders only. LLM usage can incur charges, so set a provider budget and start with small questions.

### 4. Sample PDF

```powershell
python scripts/generate_sample_pdf.py
```

### 5. Run the app

```powershell
streamlit run app.py
```

Open the URL Streamlit prints, usually http://localhost:8501.

### 6. Tests

```powershell
pytest
```

## How to demo

1. Lead Dashboard: edit a lead, restart the app, confirm it is still there. Filter **Overdue only**.
2. Document Chat: load `data/sample_company_profile.pdf`. Ask: `What is included in the 14-day pilot?` Check that a cited chunk supports the answer.
3. Sales Assistant: ask `Which leads are more than 3 days overdue?` then `Draft a follow-up email for lead 1`.
4. Memory: set email tone to **friendly**, then draft another email and confirm the tone changed.

The assistant never sends real email. It drafts text and asks for confirmation before any real-world action.

## Resume bullets (only after you have tested the feature)

LeadPilot AI — LLM-Powered Sales Assistant | Python, Streamlit, PostgreSQL, pgvector, LLM APIs

- Built an AI-powered CRM to manage sales leads and generate personalized follow-up emails using database-backed tool calling.
- Implemented a RAG pipeline using document chunking, embeddings, and vector similarity search to answer questions from company documents with source references.
- Developed persistent conversation history and preference-based memory using PostgreSQL, with validation and error handling for AI tool execution.

## Out of scope for v1

LangChain, OAuth, Gmail sending, MCP, multi-agent workflows, and a separate React/FastAPI split. Those can be added later if a role expects them.
