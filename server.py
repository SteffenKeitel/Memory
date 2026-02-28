"""MCP Memory Server – Persistentes Gedächtnis für Claude Code.

Stellt ChromaDB-Vektorsuche und SQLite-Fakten als MCP-Tools bereit.
Daten werden pro Projekt in <cwd>/.claude/memory/ gespeichert.
"""

import os
import sqlite3
from datetime import datetime, timezone

import chromadb
from mcp.server.fastmcp import FastMCP

# ---------------------------------------------------------------------------
# Pfade
# ---------------------------------------------------------------------------

DATA_DIR = os.path.join(os.getcwd(), ".claude", "memory")
CHROMA_DIR = os.path.join(DATA_DIR, "chroma")
FACTS_DB = os.path.join(DATA_DIR, "facts.db")

os.makedirs(CHROMA_DIR, exist_ok=True)

# ---------------------------------------------------------------------------
# ChromaDB
# ---------------------------------------------------------------------------

chroma_client = chromadb.PersistentClient(path=CHROMA_DIR)
collection = chroma_client.get_or_create_collection(
    name="memories",
    metadata={"hnsw:space": "cosine"},
)
sessions_collection = chroma_client.get_or_create_collection(
    name="sessions",
    metadata={"hnsw:space": "cosine"},
)

# ---------------------------------------------------------------------------
# SQLite
# ---------------------------------------------------------------------------


def _get_db() -> sqlite3.Connection:
    """SQLite-Verbindung mit auto-create der Tabelle."""
    conn = sqlite3.connect(FACTS_DB)
    conn.execute(
        "CREATE TABLE IF NOT EXISTS facts "
        "(key TEXT PRIMARY KEY, value TEXT, updated_at TEXT)"
    )
    conn.execute(
        "CREATE TABLE IF NOT EXISTS sessions "
        "(id TEXT PRIMARY KEY, summary TEXT, project TEXT, created_at TEXT)"
    )
    conn.commit()
    return conn


# ---------------------------------------------------------------------------
# MCP Server
# ---------------------------------------------------------------------------

mcp = FastMCP("memory")


@mcp.tool()
def memory_store(content: str) -> str:
    """Text oder Notiz ins Vektorarchiv schreiben.

    Args:
        content: Der zu speichernde Text.
    """
    doc_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%f")
    collection.add(
        documents=[content],
        ids=[doc_id],
        metadatas=[{"stored_at": doc_id}],
    )
    return f"Gespeichert (id={doc_id})."


@mcp.tool()
def memory_search(query: str, n_results: int = 5) -> str:
    """Semantische Suche über gespeicherte Erinnerungen.

    Args:
        query: Suchbegriff oder Frage.
        n_results: Maximale Anzahl Ergebnisse (Standard: 5).
    """
    total = collection.count()
    if total == 0:
        return "Keine Erinnerungen vorhanden."
    n = min(n_results, total)
    results = collection.query(query_texts=[query], n_results=n, include=["documents", "distances", "metadatas"])
    docs = results.get("documents", [[]])[0]
    distances = results.get("distances", [[]])[0]
    metadatas = results.get("metadatas", [[]])[0]
    if not docs:
        return "Keine passenden Erinnerungen gefunden."
    lines = []
    for i, (doc, dist, meta) in enumerate(zip(docs, distances, metadatas), 1):
        similarity = 1 - dist
        stored_at = meta.get("stored_at", "")
        timestamp = ""
        if stored_at:
            try:
                dt = datetime.strptime(stored_at, "%Y%m%dT%H%M%S%f")
                timestamp = f" [{dt.strftime('%Y-%m-%d %H:%M')}]"
            except ValueError:
                pass
        lines.append(f"{i}. [{similarity:.0%}]{timestamp} {doc}")
    return "\n".join(lines)


@mcp.tool()
def fact_set(key: str, value: str) -> str:
    """Strukturierten Fakt speichern (überschreibt bestehenden Wert).

    Args:
        key: Schlüssel des Fakts.
        value: Wert des Fakts.
    """
    now = datetime.now(timezone.utc).isoformat()
    db = _get_db()
    db.execute(
        "INSERT INTO facts (key, value, updated_at) VALUES (?, ?, ?) "
        "ON CONFLICT(key) DO UPDATE SET value=excluded.value, updated_at=excluded.updated_at",
        (key, value, now),
    )
    db.commit()
    db.close()
    return f"Fakt gespeichert: {key} = {value}"


@mcp.tool()
def fact_get(key: str) -> str:
    """Einzelnen Fakt abrufen.

    Args:
        key: Schlüssel des Fakts.
    """
    db = _get_db()
    row = db.execute("SELECT value, updated_at FROM facts WHERE key = ?", (key,)).fetchone()
    db.close()
    if row is None:
        return f"Kein Fakt mit Schlüssel '{key}' gefunden."
    return f"{key} = {row[0]} (aktualisiert: {row[1]})"


@mcp.tool()
def facts_list() -> str:
    """Alle gespeicherten Fakten auflisten."""
    db = _get_db()
    rows = db.execute("SELECT key, value, updated_at FROM facts ORDER BY key").fetchall()
    db.close()
    if not rows:
        return "Keine Fakten gespeichert."
    lines = [f"- {key} = {value} ({updated_at})" for key, value, updated_at in rows]
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Session-Summary Tools
# ---------------------------------------------------------------------------


@mcp.tool()
def session_save(summary: str, project: str = "") -> str:
    """Session-Zusammenfassung speichern (SQLite + Vektorsuche).

    Args:
        summary: Zusammenfassung der Session (was wurde gemacht, Entscheidungen, offene Punkte).
        project: Optionaler Projektname.
    """
    doc_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%f")
    db = _get_db()
    db.execute(
        "INSERT INTO sessions (id, summary, project, created_at) VALUES (?, ?, ?, ?)",
        (doc_id, summary, project, doc_id),
    )
    db.commit()
    db.close()
    sessions_collection.add(
        documents=[summary],
        ids=[doc_id],
        metadatas=[{"project": project, "created_at": doc_id}],
    )
    return f"Session-Summary gespeichert (id={doc_id})."


@mcp.tool()
def session_list(n: int = 10) -> str:
    """Letzte Session-Summaries chronologisch auflisten.

    Args:
        n: Anzahl der letzten Sessions (Standard: 10).
    """
    db = _get_db()
    rows = db.execute(
        "SELECT id, summary, project, created_at FROM sessions ORDER BY created_at DESC LIMIT ?",
        (n,),
    ).fetchall()
    db.close()
    if not rows:
        return "Keine Session-Summaries vorhanden."
    lines = []
    for sid, summary, project, created_at in rows:
        timestamp = ""
        try:
            dt = datetime.strptime(created_at, "%Y%m%dT%H%M%S%f")
            timestamp = dt.strftime("%Y-%m-%d %H:%M")
        except ValueError:
            timestamp = created_at
        prefix = f"[{timestamp}]"
        if project:
            prefix += f" [{project}]"
        lines.append(f"{prefix} {summary}")
    return "\n".join(lines)


@mcp.tool()
def session_search(query: str, n_results: int = 5) -> str:
    """Semantische Suche über Session-Summaries.

    Args:
        query: Suchbegriff oder Frage.
        n_results: Maximale Anzahl Ergebnisse (Standard: 5).
    """
    total = sessions_collection.count()
    if total == 0:
        return "Keine Session-Summaries vorhanden."
    n = min(n_results, total)
    results = sessions_collection.query(
        query_texts=[query], n_results=n, include=["documents", "distances", "metadatas"]
    )
    docs = results.get("documents", [[]])[0]
    distances = results.get("distances", [[]])[0]
    metadatas = results.get("metadatas", [[]])[0]
    if not docs:
        return "Keine passenden Session-Summaries gefunden."
    lines = []
    for i, (doc, dist, meta) in enumerate(zip(docs, distances, metadatas), 1):
        similarity = 1 - dist
        created_at = meta.get("created_at", "")
        project = meta.get("project", "")
        timestamp = ""
        if created_at:
            try:
                dt = datetime.strptime(created_at, "%Y%m%dT%H%M%S%f")
                timestamp = f" [{dt.strftime('%Y-%m-%d %H:%M')}]"
            except ValueError:
                pass
        proj_tag = f" [{project}]" if project else ""
        lines.append(f"{i}. [{similarity:.0%}]{timestamp}{proj_tag} {doc}")
    return "\n".join(lines)


if __name__ == "__main__":
    mcp.run(transport="stdio")
