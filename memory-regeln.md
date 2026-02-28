# Memory (MCP Memory Server) – STRIKTE REGELN

Diese Regeln sind verbindlich und gelten in jeder Session, für jedes Projekt.

## 1. Session-Start: Immer Memory laden
- Bei der ersten inhaltlichen Interaktion einer Session: `memory_search` mit relevanten Begriffen zum aktuellen Projekt/Thema ausführen.
- Bei bekannten Projekten zusätzlich `facts_list` aufrufen, um gespeicherte Fakten zu prüfen.
- Erst danach mit der eigentlichen Arbeit beginnen.

## 2. Vor jedem Plan: Memory konsultieren
- Bevor ein Implementierungsplan erstellt wird: `memory_search` mit den relevanten Begriffen (Dateinamen, Feature-Namen, Architektur-Konzepte).
- Frühere Entscheidungen und Erkenntnisse aus Memory in den Plan einfließen lassen.
- Keine Architektur-Entscheidung treffen, die einer gespeicherten Entscheidung widerspricht, ohne den User darauf hinzuweisen.

## 3. Bei Fragen: Erst Memory, dann Dateien
- Wenn der User eine Frage stellt (zum Projekt, zu Entscheidungen, zu früherem Kontext): zuerst `memory_search` durchführen.
- Nur wenn Memory keine Antwort liefert, in Dateien suchen.

## 4. Memory aktuell halten
- **Sofort speichern** (`fact_set`): User-Präferenzen, Workflow-Entscheidungen, Tool-Vorlieben, wiederkehrende Anweisungen.
- **Nach Abschluss speichern** (`memory_store`): Zusammenfassung abgeschlossener Features, Architektur-Änderungen, gelöste Probleme.
- **Veraltetes korrigieren**: Wenn sich ein Fakt ändert, alten Eintrag aktualisieren oder neuen mit korrektem Stand speichern.
- Keine Duplikate: Vor dem Speichern prüfen, ob die Information bereits vorhanden ist.

## 5. Pläne immer in Memory speichern
- Jeden genehmigten Implementierungsplan per `memory_store` speichern (komprimiert: Ziel, Ansatz, betroffene Dateien, Entscheidungen).
- Nach Umsetzung den Plan-Eintrag mit dem Ergebnis ergänzen oder einen neuen Abschluss-Eintrag erstellen.

## 6. Session-Ende: Summary speichern
- Am Ende jeder produktiven Session `session_save` aufrufen.
- Summary enthält: was wurde gemacht, getroffene Entscheidungen, offene Punkte.
- Optional Projektname mitgeben (`project`-Parameter), um Sessions projektübergreifend filterbar zu machen.
- Frühere Sessions können mit `session_list` (chronologisch) oder `session_search` (semantisch) abgerufen werden.
