"""SessionEnd-Hook: Liest Claude-Code-Transkript, erstellt Summary via API, speichert in Memory-DB.

Wird von run-session-summary.sh aufgerufen. Erwartet JSON auf stdin mit:
  - session_id: str
  - transcript_path: str
  - cwd: str

Schreibt die Summary in {cwd}/.claude/memory/ (ChromaDB + SQLite),
identisches Format wie session_save in server.py.
"""

import json
import os
import sqlite3
import sys
from datetime import datetime, timezone

import anthropic
import chromadb


# ---------------------------------------------------------------------------
# Konfiguration
# ---------------------------------------------------------------------------

MAX_TRANSCRIPT_CHARS = 150_000
HAIKU_MODEL = "claude-haiku-4-5-20251001"
SUMMARY_PROMPT = """\
Du erhältst das Transkript einer Claude-Code-Session. Erstelle eine strukturierte \
Session-Zusammenfassung auf Deutsch mit folgenden Abschnitten:

**Was wurde gemacht**: Kurze Aufzählung der erledigten Aufgaben/Änderungen.
**Entscheidungen**: Wichtige technische oder architektonische Entscheidungen.
**Offene Punkte**: Was noch nicht fertig ist oder als Nächstes ansteht.

Halte die Zusammenfassung kompakt (max 300 Wörter). Keine Einleitung, direkt mit den Abschnitten beginnen."""


def main():
    # --- Input lesen ---
    try:
        hook_input = json.load(sys.stdin)
    except (json.JSONDecodeError, ValueError) as exc:
        print(f"Hook-Input ungültig: {exc}", file=sys.stderr)
        return

    transcript_path = hook_input.get("transcript_path", "")
    cwd = hook_input.get("cwd", "")

    if not transcript_path or not cwd:
        print("transcript_path oder cwd fehlt im Hook-Input.", file=sys.stderr)
        return

    # --- Guard: Nur Projekte mit Memory-Server ---
    memory_dir = os.path.join(cwd, ".claude", "memory")
    if not os.path.isdir(memory_dir):
        return  # Kein Memory-Verzeichnis → nichts tun

    # --- Transkript lesen und parsen ---
    if not os.path.isfile(transcript_path):
        print(f"Transkript nicht gefunden: {transcript_path}", file=sys.stderr)
        return

    messages = []
    with open(transcript_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                entry = json.loads(line)
            except json.JSONDecodeError:
                continue

            msg_type = entry.get("type", "")
            if msg_type not in ("user", "assistant"):
                continue

            # Text-Inhalte extrahieren
            message = entry.get("message", {})
            content = message.get("content", "")

            if isinstance(content, str):
                if content.strip():
                    role = "User" if msg_type == "user" else "Assistant"
                    messages.append(f"[{role}]: {content.strip()}")
            elif isinstance(content, list):
                texts = []
                for block in content:
                    if isinstance(block, dict) and block.get("type") == "text":
                        text = block.get("text", "").strip()
                        if text:
                            texts.append(text)
                if texts:
                    role = "User" if msg_type == "user" else "Assistant"
                    messages.append(f"[{role}]: {' '.join(texts)}")

    if not messages:
        print("Keine relevanten Nachrichten im Transkript gefunden.", file=sys.stderr)
        return

    transcript_text = "\n\n".join(messages)

    # --- Truncation: Ende der Session ist wichtiger ---
    if len(transcript_text) > MAX_TRANSCRIPT_CHARS:
        transcript_text = transcript_text[-MAX_TRANSCRIPT_CHARS:]
        # Ersten unvollständigen Eintrag abschneiden
        first_bracket = transcript_text.find("\n\n[")
        if first_bracket != -1:
            transcript_text = transcript_text[first_bracket + 2:]

    # --- Claude Haiku API-Call ---
    api_key = os.environ.get("ANTHROPIC_API_KEY", "")
    if not api_key:
        print("ANTHROPIC_API_KEY nicht gesetzt.", file=sys.stderr)
        return

    client = anthropic.Anthropic(api_key=api_key)

    try:
        response = client.messages.create(
            model=HAIKU_MODEL,
            max_tokens=1024,
            messages=[
                {
                    "role": "user",
                    "content": f"{SUMMARY_PROMPT}\n\n---\n\n{transcript_text}",
                }
            ],
        )
    except Exception as exc:
        print(f"API-Fehler: {exc}", file=sys.stderr)
        return

    summary = ""
    for block in response.content:
        if block.type == "text":
            summary += block.text

    if not summary.strip():
        print("Leere Summary von API erhalten.", file=sys.stderr)
        return

    summary = summary.strip()

    # --- Projekt-Name aus cwd ---
    project = os.path.basename(cwd.rstrip("/"))

    # --- In Memory-DB speichern (identisch zu session_save in server.py) ---
    doc_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%f")
    chroma_dir = os.path.join(memory_dir, "chroma")
    facts_db = os.path.join(memory_dir, "facts.db")

    # SQLite
    conn = sqlite3.connect(facts_db)
    conn.execute(
        "CREATE TABLE IF NOT EXISTS sessions "
        "(id TEXT PRIMARY KEY, summary TEXT, project TEXT, created_at TEXT)"
    )
    conn.execute(
        "INSERT INTO sessions (id, summary, project, created_at) VALUES (?, ?, ?, ?)",
        (doc_id, summary, project, doc_id),
    )
    conn.commit()
    conn.close()

    # ChromaDB
    chroma_client = chromadb.PersistentClient(path=chroma_dir)
    sessions_collection = chroma_client.get_or_create_collection(
        name="sessions",
        metadata={"hnsw:space": "cosine"},
    )
    sessions_collection.add(
        documents=[summary],
        ids=[doc_id],
        metadatas=[{"project": project, "created_at": doc_id}],
    )

    print(f"Session-Summary gespeichert: [{project}] id={doc_id}", file=sys.stderr)


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"Unerwarteter Fehler im Session-Hook: {exc}", file=sys.stderr)
        sys.exit(0)
