# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

MCP Memory Server – a persistent memory backend for Claude Code. Provides semantic vector search (ChromaDB) and structured key-value facts (SQLite) as MCP tools over stdio transport.

Single-file server: all logic lives in `server.py`.

## Setup & Run

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Register in Claude Code:
```bash
claude mcp add memory -- /path/to/Memory/.venv/bin/python /path/to/Memory/server.py
```

Run directly (stdio transport):
```bash
python server.py
```

## Architecture

`server.py` uses `FastMCP` from `mcp.server.fastmcp` to expose eight tools:

- **Vector memory** (`memory_store`, `memory_search`): ChromaDB collection `"memories"` with cosine similarity. Documents are timestamped IDs. Search returns similarity scores as `1 - distance`.
- **Facts store** (`fact_set`, `fact_get`, `facts_list`): SQLite `facts` table (key, value, updated_at). Uses upsert via `ON CONFLICT`.
- **Session summaries** (`session_save`, `session_list`, `session_search`): ChromaDB collection `"sessions"` + SQLite `sessions` table (id, summary, project, created_at). Stores structured session summaries, listable chronologically and searchable semantically.

Data is stored relative to `cwd` at `.claude/memory/` (chroma/ + facts.db), giving per-project isolation.

## Repository & Deploy

- Remote: https://github.com/SteffenKeitel/Memory
- Branch: `main`
- `.gitignore` excludes: `.claude/memory/`, `.claude/settings.local.json`, `.venv/`, `__pycache__/`
- **Productive path**: `~/.claude/mcp-memory/server.py` (this is what Claude Code actually runs)
- **Deploy**: `cp server.py ~/.claude/mcp-memory/server.py` — changes take effect on next Claude Code session

## Key Details

- Language: German (docstrings, tool descriptions, user-facing messages)
- Dependencies: `mcp[cli]>=1.0.0`, `chromadb>=0.5.0`
- No test suite exists
- `memory-regeln.md` contains the usage protocol for Claude Code sessions (when to search/store memory) — these rules are also in the global `~/.claude/CLAUDE.md`
