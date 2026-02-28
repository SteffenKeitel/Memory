# MCP Memory Server

Persistentes Gedächtnis für Claude Code – stellt semantische Vektorsuche und strukturierte Fakten als MCP-Tools bereit.

## Features

- **Vektorsuche** (ChromaDB) – Texte speichern und per Similarity-Search wiederfinden
- **Fakten-Store** (SQLite) – Key-Value-Paare für strukturierte Informationen
- **Pro-Projekt-Isolation** – Daten werden unter `<Projektverzeichnis>/.claude/memory/` abgelegt
- **stdio-Transport** – Standard-MCP-Protokoll, kompatibel mit Claude Code und Claude Desktop

## Tools

| Tool | Beschreibung |
|---|---|
| `memory_store` | Text ins Vektorarchiv schreiben |
| `memory_search` | Semantische Suche über gespeicherte Erinnerungen |
| `fact_set` | Strukturierten Fakt speichern (Key-Value) |
| `fact_get` | Einzelnen Fakt abrufen |
| `facts_list` | Alle gespeicherten Fakten auflisten |

## Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## In Claude Code registrieren

```bash
claude mcp add memory -- /pfad/zu/Memory/.venv/bin/python /pfad/zu/Memory/server.py
```

Oder manuell in die MCP-Konfiguration eintragen:

```json
{
  "memory": {
    "command": "/pfad/zu/Memory/.venv/bin/python",
    "args": ["/pfad/zu/Memory/server.py"],
    "transport": "stdio"
  }
}
```

## Datenspeicherung

Der Server legt seine Daten relativ zum Arbeitsverzeichnis an:

```
<cwd>/.claude/memory/
├── chroma/      # ChromaDB-Vektordatenbank
└── facts.db     # SQLite-Faktenspeicher
```

Jedes Projekt bekommt so seinen eigenen, isolierten Speicher.

## Deploy

Der produktive Server liegt unter `~/.claude/mcp-memory/server.py`. Nach Änderungen im Repo:

```bash
cp server.py ~/.claude/mcp-memory/server.py
```

Änderungen werden ab der nächsten Claude-Code-Session wirksam.
