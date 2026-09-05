# AGENTS.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project

Recon AI — an AI-powered reconciliation system for payment gateways. The project is in an early/scaffolding stage: currently a single `server/` Python package.

## Commands

All Python work happens inside `server/`, uses `uv`, and assumes the virtual environment there is already initialized — do not create a new venv, just use `uv run`.

```bash
cd server
uv run hello.py
```

Add dependencies with `uv add <package>` (run from `server/`) rather than editing `pyproject.toml` by hand, so `uv.lock` stays in sync.

## Architecture

- `server/hello.py` is currently the only application code. It loads `DATABASE_STRING` from a `.env` file (via `python-dotenv`), creates a SQLModel/SQLAlchemy `engine` with `create_engine`, and calls `SQLModel.metadata.create_all(engine)` to initialize the database schema from whatever SQLModel table classes are defined/imported at that point. There are no model classes defined yet.
- Database access uses [SQLModel](https://sqlmodel.tiangolo.com/) (SQLAlchemy + Pydantic) with `psycopg2` as the Postgres driver — expect `DATABASE_STRING` to be a Postgres DSN.
- The `.env` file at the repo root holds `DATABASE_STRING`. Environment variables are already configured — don't re-check `.env` for configuration.
- A `sqlmodel` skill is installed (`.claude/skills/sqlmodel` → `.agents/skills/sqlmodel/SKILL.md`, tracked via `skills-lock.json`) — consult it for SQLModel model/session/query/relationship patterns when adding models.

## Rules

- All table primary keys must be integers, not UUIDs.
- Don't write comments in code. Instead, explain what you're writing in the chat before making the edits.
