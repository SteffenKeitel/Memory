# Memory (MCP Memory Server) – Regeln

Der Memory-Server dient als **Entscheidungs- und Planhistorie** — nicht als
Duplikat von CLAUDE.md oder Code. Alles, was im Projekt dokumentiert ist
(Architektur, Standards, Roadmap), gehört NICHT ins Memory.

## Was ins Memory gehört

| Tool | Inhalt | Wann |
|------|--------|------|
| `memory_store` | Genehmigte Pläne (Ziel, Ansatz, betroffene Dateien, Entscheidungen, verworfene Alternativen) | Nach Genehmigung |
| `memory_store` | Abschluss-Einträge (was wurde umgesetzt, was wich vom Plan ab, offene Punkte) | Nach Umsetzung |
| `session_save` | Manuelle Session-Summaries (nur bei Bedarf — automatische Summaries werden vom SessionEnd-Hook erstellt) | Optional |
| `fact_set` | User-Präferenzen, Workflow-Entscheidungen, wiederkehrende Anweisungen — nur wenn nicht in CLAUDE.md dokumentiert | Sofort |

## Was NICHT ins Memory gehört

- Projekt-Architektur, Coding-Standards, Dateistruktur (steht in CLAUDE.md)
- Informationen, die aus dem Code oder Git-Log ersichtlich sind
- Duplikate bereits gespeicherter Einträge

## Wann Memory konsultieren

- **Vor jedem Plan**: `memory_search` nach früheren Entscheidungen zum Thema. Keine Architektur-Entscheidung treffen, die einer gespeicherten widerspricht, ohne den User darauf hinzuweisen
- **Bei Fragen zu früherem Kontext**: `memory_search` vor Dateisuche

## Session-Summaries (AUTOMATISCH)

Session-Summaries werden **automatisch** vom SessionEnd-Hook erstellt (`session_hook.py`). Der Hook liest das Transkript, ruft Claude Haiku auf und schreibt die Summary in die Memory-DB.

- **Kein manueller `session_save`-Aufruf nötig** — der Hook übernimmt das
- `session_save` kann weiterhin manuell genutzt werden, z.B. für Zwischen-Summaries bei sehr langen Sessions
- Voraussetzung: `{cwd}/.claude/memory/` muss existieren (Projekte ohne Memory-Server werden übersprungen)

## Aufräumen

- **Veraltete Einträge löschen**: `memory_search` zum Finden, dann `memory_delete` mit der angezeigten ID
- **Fakten korrigieren**: `fact_set` überschreibt bestehende Werte automatisch
- Vor dem Speichern prüfen, ob die Information bereits vorhanden ist
