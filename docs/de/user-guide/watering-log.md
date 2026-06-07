# Gießprotokoll

Das Gießprotokoll (WateringLog) ist das zentrale, vereinheitlichte Protokoll aller Bewässerungsvorgänge in Kamerplanter. Es fasst sowohl manuelle als auch automatisch erfasste Gießereignisse zusammen und bietet dir eine lückenlose Übersicht über die Bewässerungshistorie deiner Pflanzen — als Grundlage für fundierte Entscheidungen bei Nährstoffplanung und Substratmanagement.

---

## Voraussetzungen

- Mindestens ein angelegter Pflanzdurchlauf oder eine Pflanze
- Zugeordnetes Substrat (empfohlen, für Substrat-Feuchte-Tracking)

---

## Abgrenzung: WateringLog, WateringEvents und FeedingEvents

Kamerplanter unterscheidet drei verwandte Konzepte:

| Begriff | Beschreibung | Typischer Auslöser |
|---------|-------------|-------------------|
| **WateringEvent** | Ein einzelnes Bewässerungsereignis — Zeitpunkt, Menge, Quelle | Manuelle Erfassung oder Gießplan-Bestätigung |
| **FeedingEvent** | Ein Dünge-/Bewässerungsereignis mit Nährstoffdaten (EC, pH, Dosierungen) | Düngung nach Nährstoffplan (REQ-004) |
| **WateringLog** | Vereinheitlichtes Protokoll — fasst WateringEvents und FeedingEvents in einer Ansicht zusammen | Automatisch aggregiert |

!!! note "Unterschied zu FeedingEvents"
    FeedingEvents dokumentieren Bewässerungen, bei denen Dünger hinzugefügt wurde — mit vollständigem Nährstoffprofil (EC-Ziel, pH-Ziel, Produktdosierungen). Das WateringLog zeigt beide Typen nebeneinander, damit du die Bewässerungshistorie ohne Kontextwechsel nachverfolgen kannst.

---

## Das Gießprotokoll aufrufen

1. Navigiere zu einem **Pflanzdurchlauf** oder einer **Pflanze**.
2. Klicke auf den Tab **Gießprotokoll** (oder **Bewässerung**).
3. Die Protokollansicht zeigt alle Bewässerungsereignisse in chronologischer Reihenfolge.

!!! info "Screenshot folgt"
    Dieser Screenshot wird in einer zukünftigen Version ergänzt.

---

## Was das Gießprotokoll anzeigt

Pro Eintrag werden folgende Informationen angezeigt:

| Feld | Beschreibung |
|------|-------------|
| **Datum & Uhrzeit** | Zeitpunkt des Gießvorgangs |
| **Menge (Liter)** | Bewässerungsmenge in Liter |
| **EC** | Elektrische Leitfähigkeit der Nährlösung (falls Dünger eingesetzt) |
| **pH** | pH-Wert der Gießlösung (falls erfasst) |
| **Typ** | `Bewässerung` oder `Düngung` |
| **Quelle** | Manuell, Gießplan, automatisch |
| **Notiz** | Optionale Freitext-Anmerkung |

---

## Gießereignis manuell eintragen

1. Klicke auf **Neues Gießereignis**.
2. Trage Menge und Zeitpunkt ein.
3. Optional: EC, pH und eine Notiz ergänzen.
4. Klicke auf **Speichern**.

!!! tip "Gießplan nutzen"
    Wenn du einen Gießplan (WateringSchedule) für deinen Pflanzdurchlauf konfiguriert hast, erzeugt Kamerplanter automatisch Aufgaben. Durch Bestätigung dieser Aufgaben werden Gießereignisse automatisch im Protokoll eingetragen — du musst nichts manuell erfassen.

---

## Gießprotokoll und Nährstoffplanung

Das WateringLog ist eng mit der Dünge-Logik (REQ-004) verzahnt:

- **EC-Verlauf** über mehrere Gießvorgänge ist in der Protokollansicht als Minigraph sichtbar (bei vorhandenen Daten).
- **Spülungserkennung**: Wenn EC und pH erfasst werden, kann Kamerplanter Spülvorgänge (Flushing) automatisch kennzeichnen.
- **Runoff-Analyse**: Bei erfasstem Runoff-EC können Nährstoff-Akkumulationen im Substrat erkannt werden.

---

## Häufige Fragen

??? question "Werden automatische Bewässerungen (Home Assistant) auch protokolliert?"
    Ja. Wenn Kamerplanter über die Home-Assistant-Integration Bewässerungsdaten empfängt, werden diese automatisch als WateringEvents im Protokoll eingetragen — mit der Quelle `automatisch`.

??? question "Wie lange werden Gießprotokolle aufbewahrt?"
    Gießprotokolle werden entsprechend der Datenaufbewahrungsrichtlinie (NFR-011) gespeichert. Standardmäßig bleiben Roheinträge 90 Tage vollständig erhalten, danach werden sie zu täglichen Aggregaten verdichtet.

??? question "Kann ich Einträge im Protokoll nachträglich korrigieren?"
    Ja. Klicke auf einen Eintrag und wähle **Bearbeiten**. Änderungen werden mit Zeitstempel protokolliert.

---

## Siehe auch

- [Dünge-Logik](fertilization.md) — Nährstoffpläne und FeedingEvents (REQ-004)
- [Pflanzdurchläufe](planting-runs.md) — Gießplan konfigurieren
- [Tankmanagement](tanks.md) — Bewässerungstanks und Befüllungen
