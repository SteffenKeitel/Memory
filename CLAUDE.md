# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

MCP Memory Server – a persistent memory backend for Claude Code. Provides semantic vector search (ChromaDB) and structured key-value facts (SQLite) as MCP tools over stdio transport.

Main components:
- `server.py` — MCP server (all tools)
- `session_hook.py` — SessionEnd-Hook for automatic session summaries

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

## SessionEnd-Hook (Automatic Session Summaries)

`session_hook.py` runs automatically at the end of every Claude Code session via `~/.claude/settings.json`. It reads the session transcript, calls Claude Haiku for a summary, and writes directly into the project's Memory DB.

**Flow:** SessionEnd → `run-session-summary.sh` → `session_hook.py`

- **Guard**: Only runs if `{cwd}/.claude/memory/` exists (projects without Memory are skipped)
- **Transcript parsing**: Extracts user/assistant text from JSONL, truncates to last 150k chars
- **Storage**: Writes to ChromaDB `"sessions"` + SQLite `sessions` table (same format as `session_save`)
- **Error handling**: Errors go to stderr, always exits 0 (never blocks session end)

**Productive path**: `~/.claude/hooks/session_hook.py` + `run-session-summary.sh`
**Hook venv**: `~/.claude/hooks/.venv/` (separate from MCP server venv)
**Config**: `~/.claude/hooks/.env` (ANTHROPIC_API_KEY, not in repo)

## Repository & Deploy

- Remote: https://github.com/SteffenKeitel/Memory
- Branch: `main`
- `.gitignore` excludes: `.claude/memory/`, `.claude/settings.local.json`, `.venv/`, `__pycache__/`

**MCP Server:**
- **Productive path**: `~/.claude/mcp-memory/server.py`
- **Deploy**: `cp server.py ~/.claude/mcp-memory/server.py`

**SessionEnd-Hook:**
- **Productive path**: `~/.claude/hooks/session_hook.py` + `run-session-summary.sh`
- **Deploy**: `cp session_hook.py run-session-summary.sh ~/.claude/hooks/`
- **Hook venv**: `~/.claude/hooks/.venv/bin/pip install -r requirements-hook.txt`

## Key Details

- Language: German (docstrings, tool descriptions, user-facing messages)
- Dependencies MCP server: `mcp[cli]>=1.0.0`, `chromadb>=0.5.0` (see `requirements.txt`)
- Dependencies Hook: `anthropic>=0.40.0`, `chromadb>=0.5.0` (see `requirements-hook.txt`)
- No test suite exists
- `memory-regeln.md` contains the usage protocol for Claude Code sessions (when to search/store memory) — these rules are also in the global `~/.claude/CLAUDE.md`
