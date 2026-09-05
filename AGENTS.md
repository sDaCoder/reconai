# AGENTS.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project

Recon AI — an AI-powered reconciliation system for payment gateways. The repo has two independent apps: `server/` (Python/FastAPI backend + LangChain agent) and `client/` (Next.js frontend), talking over plain HTTP on `localhost:8000`.

## Commands

### Server (`server/`)

Uses `uv`, and assumes the virtual environment there is already initialized — do not create a new venv, just use `uv run`.

```bash
cd server
uv run hello.py                     # FastAPI/uvicorn app on :8000
uv run agent/recon_agent.py "Reconcile settlement 1."   # run the recon agent from the CLI
uv run crud_check.py                # exercise SQLModel CRUD against the DB
uv run seed_data.py                 # seed the DB with dummy reconciliation data
```

Add dependencies with `uv add <package>` (run from `server/`) rather than editing `pyproject.toml` by hand, so `uv.lock` stays in sync.

Both `DATABASE_STRING` (Postgres/Supabase DSN) and `GROQ_API_KEY` are already loaded via `.env` at the repo root — don't re-check `.env` for configuration or search for these keys.

### Client (`client/`)

Plain JavaScript (no TypeScript) Next.js App Router project. Uses `bun` — always install/remove dependencies with `bun add <package>` / `bun remove <package>` (run from `client/`) rather than editing `package.json` by hand, so `bun.lock` stays in sync.

```bash
cd client
bun run dev                         # Next.js dev server on :3000 (Turbopack)
bun run build                       # production build
bun run start                       # serve the production build
bun run lint                        # eslint
```

The client fetches directly from the FastAPI server at `http://localhost:8000` (hardcoded in `src/lib/api.js`), so `server/hello.py` must be running for pages to load data. There is no CORS setup because all fetches happen server-side in Next.js Server Components, not from the browser.

Both dev servers are also declared in `.claude/launch.json` (`client-dev`, `server-dev`) for use with the preview tooling.

## Architecture

### Server

- **Data layer** (`server/models.py`, `server/db_connection.py`): SQLModel table classes — `Order`, `BankTransaction`, `Payment`, `Settlement`, `Adjustment`, `ReconciliationCase` — plus a shared `engine` built from `DATABASE_STRING` via `psycopg2`. `ReconciliationCase` is the join table linking a payment to its settlement/bank transaction with a `status`, `confidence`, and computed amount differences. `hello.py` calls `SQLModel.metadata.create_all(engine)` to initialize the schema.
- **Deterministic tools** (`server/tools/`): plain-Python, DB-backed helper functions with no LLM involvement, each focused on one concern:
  - `amounts.py` — expected settlement math and amount comparison with tolerance.
  - `dates.py` — timezone-aware date-difference calculation.
  - `duplicates.py` — detects duplicate bank transactions by (reference, amount, currency, date).
  - `matching.py` — exact reference matching and candidate bank-transaction search (joins `BankTransaction` → `ReconciliationCase` → `Payment` → `Order`).
  - `validation.py` — currency allow-list validation.
  - `lookups.py` — get/list CRUD-style reads for every table, returning `dict`/`None` via `model_dump()`.
- **Agent layer** (`server/agent/recon_agent.py`, `server/ai_models.py`): a LangChain `create_agent` agent (`recon_agent`) backed by Groq (`get_groq_model`, default `openai/gpt-oss-120b`) that wraps every function in `tools/` as a `@tool` and follows the reconciliation procedure defined in `server/agent/prompt.txt` (validate currency → check duplicates → calculate expected settlement → match bank reference/candidates → compare amounts/dates → decide with confidence → explain). `run(user_input)` invokes the agent and returns the final message content; running the module directly (`uv run agent/recon_agent.py "<query>"`) prints the result as Markdown via `rich`.
- `server/crud_check.py` and `server/seed_data.py` are standalone scripts (own `load_dotenv`/`engine`, not importing `db_connection`) for exercising and seeding the schema directly.
- `server/hello.py` is the FastAPI app: `GET /` (health check), `GET /reconciliation-cases` (all rows of `ReconciliationCase`, JSON), `POST /reconcile` (runs `recon_agent` on a free-text query and returns its answer).
- A `sqlmodel` skill is installed (`.claude/skills/sqlmodel` → `.agents/skills/sqlmodel/SKILL.md`, tracked via `skills-lock.json`) — consult it for SQLModel model/session/query/relationship patterns. A `langchain-fundamentals` skill is installed the same way for `create_agent`/tool/middleware patterns. A `fastapi` skill is installed for FastAPI route/dependency conventions.

### Client

Next.js App Router app in `client/src/app/`, styled entirely with Tailwind v4 utilities and a hand-rolled "liquid glass" design system (`glass`/`glass-soft`/`glass-nav` utilities defined in `src/app/globals.css`, grayscale-only color tokens, `Fraunces`/`Source Serif 4` fonts via `next/font/google`).

- **Routes**: `/` (dashboard — aggregate stats + a donut breakdown chart), `/cases` (table of all reconciliation cases), `/investigation/[id]` (single-case detail, `case_id` as the route param). All three are async Server Components that fetch live data server-side — there is no client-side data fetching or state management.
- **`src/lib/api.js`**: the only place that talks to the backend. `getReconciliationCases()` fetches `GET /reconciliation-cases` with `cache: "no-store"`; `classifyStatus()` buckets the DB's varied status strings (`matched`, `RECONCILED`, `adjusted`, `mismatch`, etc.) into `reconciled` / `explained` / `exception` for consistent badge styling across pages; `formatCaseCode()`/`formatStatusLabel()` handle display formatting. Reuse these helpers rather than re-deriving status logic per page.
- **`src/lib/format.js`**: `inr()` currency formatter (INR, no decimals).
- **`src/lib/utils.js`**: `cn()` — `clsx` + `tailwind-merge`, standard shadcn-style className merging.
- **`src/app/top-nav.js`** and **`src/app/chat-bubble.js`** are client components (`usePathname`/`useState`) rendered from the root layout; everything else is a server component by default.
- The `@/*` path alias maps to `client/src/*` (`jsconfig.json`).
- `client/AGENTS.md` is regenerated by `next dev` itself — don't hand-edit its content, just keep it committed as-is.

## Rules

- All table primary keys must be integers, not UUIDs.
- Don't write comments in code. Instead, explain what you're writing in the chat before making the edits.
- Server: use `uv` for all dependency/venv management.
- Client: use `bun` for all dependency management (`bun add`/`bun remove`); the client is plain JavaScript, not TypeScript — don't introduce `.ts`/`.tsx` files or type annotations.
