---
name: memory-check
description: Prüfe den MCP-Memory-Server auf veraltete, redundante oder fehlerhafte Einträge und gleiche sie mit dem aktuellen Projektstand ab.
allowed-tools: mcp__memory__memory_search, mcp__memory__facts_list, mcp__memory__session_list, mcp__memory__memory_delete, mcp__memory__fact_set
---

# Memory-Check

Prüfe den MCP-Memory-Server auf veraltete, redundante oder fehlerhafte Einträge
und gleiche sie mit dem aktuellen Projektstand ab.

## Anleitung

### Schritt 1: Alle Memory-Daten abrufen

Rufe parallel ab:
- `facts_list` – alle gespeicherten Fakten
- `memory_search` mit breitem Query (z.B. "Rachel Projekt") und `n_results=50`
- `session_list` mit `n=20`

### Schritt 2: Aktuelle Quellen lesen

Lies parallel:
- `CLAUDE.md` (Projekt-Root) – aktuelle Architektur, Roadmap, Standards
- `~/.claude/CLAUDE.md` – globale Anweisungen, Memory-Regeln
- Git-Log der letzten 20 Commits (`git log --oneline -20`)
- Existierende Dateien im Projekt (`ls *.py`)

### Schritt 3: Analyse

Prüfe jeden Memory-Eintrag gegen diese Kriterien:

**Veraltete Einträge:**
- Beschreiben Features als "geplant" oder "nächster Schritt", die laut CLAUDE.md/Git bereits implementiert sind
- Enthalten alte Architektur-Beschreibungen (z.B. Regex-Tags statt tool_use)
- Fakten die sich selbst als "VERALTET" markieren
- Roadmap-Punkte die bereits erledigt sind

**Redundante Einträge:**
- Zwei oder mehr Einträge beschreiben denselben Plan/dasselbe Feature
- Einträge die nur CLAUDE.md-Inhalte wiedergeben (Architektur, Standards, Persönlichkeit)
- Plan-Einträge UND Abschluss-Einträge zum selben Feature (Plan ist nach Abschluss überflüssig)

**Inkorrekte Einträge:**
- Dateien/Klassen/Funktionen die nicht (mehr) existieren
- Falsche Beschreibungen der aktuellen Architektur

### Schritt 4: Bericht

Erstelle einen strukturierten Bericht:

```
## Memory-Check Ergebnis

### Fakten ({n} gesamt)
- OK: {liste}
- Löschen: {liste mit Begründung}

### Memory-Einträge ({n} gesamt)
- OK: {liste mit Kurzbeschreibung}
- Löschen: {liste mit ID und Begründung}

### Sessions ({n} gesamt)
- OK / Löschen analog

### Zusammenfassung
- {n} Einträge OK
- {n} zum Löschen vorgeschlagen
- Geschätzter Noise-Anteil: {%}
```

### Schritt 5: Aufräumen

Frage den User: "Soll ich die {n} vorgeschlagenen Einträge löschen?"

Bei Zustimmung:
- Fakten löschen mit `fact_set` (key auf leeren Wert) oder passender Delete-Methode
- Memory-Einträge löschen mit `memory_delete` (doc_id aus der Suche)
- Nach dem Löschen: Kurze Bestätigung was entfernt wurde

Bei Ablehnung oder Teilzustimmung:
- User nach einzelnen Einträgen fragen oder Auswahl akzeptieren

## Wichtig

- Lösche NIE ohne Rückfrage
- Im Zweifel als "unklar" markieren statt zum Löschen vorschlagen
- Abschluss-Einträge zu abgeschlossenen Features können gelöscht werden wenn die Info in CLAUDE.md steht
- Genehmigte Pläne die umgesetzt wurden können gelöscht werden
- Session-Summaries sind historisch – nur löschen wenn komplett redundant
