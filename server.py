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
    results = collection.query(query_texts=[query], n_results=n)
    docs = results.get("documents", [[]])[0]
    distances = results.get("distances", [[]])[0]
    if not docs:
        return "Keine passenden Erinnerungen gefunden."
    lines = []
    for i, (doc, dist) in enumerate(zip(docs, distances), 1):
        similarity = 1 - dist
        lines.append(f"{i}. [{similarity:.0%}] {doc}")
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


if __name__ == "__main__":
    mcp.run(transport="stdio")
