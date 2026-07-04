# Gießprotokoll

Das Gießprotokoll (WateringLog) ist der zentrale Ort, an dem du jeden Gieß- und Düngevorgang dokumentierst — egal ob reine Bewässerung oder Düngung mit Nährstoffen. Es ersetzt die früheren, getrennten Modelle für Bewässerungs- und Düngeereignisse durch einen einzigen Eintragstyp und gibt dir eine lückenlose Historie pro Pflanze, Stellplatz oder Standort.

---

## Voraussetzungen

- Mindestens eine Pflanze **oder** ein Stellplatz, dem du den Eintrag zuordnen kannst (mindestens eines von beidem ist Pflicht)

---

## Ein Wort zum Datenmodell

Frühere Versionen von Kamerplanter unterschieden zwei getrennte Modelle: `WateringEvent` (reine Bewässerung) und `FeedingEvent` (Düngung mit Nährstoffdaten). Beide sind als **veraltet** markiert und werden schrittweise abgelöst.

Das `WateringLog` ersetzt beide Modelle durch einen einzigen Eintragstyp, der sowohl reine Bewässerung als auch Düngung abbildet — je nachdem, ob du Dünger und Messwerte einträgst oder nicht. Es **aggregiert nicht** mehrere Einzelereignisse zu einer Zusammenfassung; jeder Eintrag im Protokoll ist eine eigenständige, unveränderliche Aufzeichnung eines einzelnen Gieß- oder Düngevorgangs.

!!! note "Legacy-Ansicht Düngeereignisse"
    Die alte Übersicht „Düngeereignisse" (`FeedingEvent`) ist aus Kompatibilitätsgründen weiterhin erreichbar, aber nicht mehr in der Navigation verlinkt — sie zeigt nur historische Alteinträge. Neue Einträge legst du ausschließlich im Gießprotokoll an.

---

## Das Gießprotokoll öffnen

Das Gießprotokoll ist ein **eigener Menüpunkt auf oberster Navigationsebene** — es liegt nicht unter „Düngung", da es sowohl reine Bewässerung als auch Düngung abdeckt.

1. Klicke in der Navigation auf **Gießprotokoll**.
2. Die Listenansicht zeigt alle Einträge, standardmäßig nach Zeitpunkt absteigend sortiert.

Alternativ erreichst du gefilterte Ansichten über die Detailseite einer Pflanze, eines Stellplatzes oder eines Standorts.

---

## Was die Liste anzeigt

Pro Eintrag werden folgende Spalten angezeigt (einige nur, wenn mindestens ein Eintrag einen Wert dafür hat):

| Spalte | Beschreibung |
|--------|-------------|
| Zeitpunkt | Wann der Vorgang protokolliert wurde |
| Pflanzen | Verknüpfte Pflanzen (bis zu 3 als Chips, Rest als Zähler) |
| Anwendungsart | Fertigation (automatisierte Nährlösungsausbringung über die Bewässerung, siehe [Nährlösung mischen](../guides/nutrient-mixing.md)), Gießen (Drench), Blattdüngung oder Aufstreuen |
| Volumen (L) | Eingesetzte Wassermenge |
| Verwendete Dünger | Namen der eingesetzten Düngemittel (nur sichtbar, wenn Dünger verwendet wurden) |
| EC vorher / EC nachher | Gemessene Leitfähigkeit (nur sichtbar, wenn erfasst) |
| pH vorher / pH nachher | Gemessener pH-Wert (nur sichtbar, wenn erfasst) |
| Wasserquelle | Tank, Leitungswasser, Osmosewasser, Regenwasser, Destilliert oder Brunnenwasser (nur sichtbar, wenn erfasst) |

---

## Gießvorgang manuell erfassen

1. Klicke auf **Gießvorgang erfassen**.
2. **Grunddaten**:
    - Pflanze(n) wählen (Mehrfachauswahl) und/oder Stellplatz-Keys eintragen (kommagetrennt)
    - **Anwendungsart** wählen (Fertigation, Gießen, Blattdüngung, Aufstreuen)
    - **Wasserquelle** angeben (optional)
    - **Volumen (L)** eintragen
    - Vorgang bei Bedarf als **ergänzend** markieren (zusätzliche Gießrunde außerhalb des regulären Plans)
3. **Messwerte**: Trage optional EC und pH vor und nach dem Gießen ein.
4. **Ablaufwerte**: Trage optional Abfluss-EC, Abfluss-pH und Abflussvolumen ein (für die Runoff-Analyse).
5. **Verwendete Dünger**: Füge über **Dünger hinzufügen** beliebig viele Dünger mit ihrer Dosierung in ml/L hinzu.
6. Trage optional ein, wer den Vorgang durchgeführt hat, und eine Notiz.
7. Klicke auf **Speichern**.

!!! warning "Pflanzen oder Stellplätze sind Pflicht"
    Ein Eintrag muss mindestens eine Pflanze oder einen Stellplatz referenzieren — sonst lässt er sich nicht speichern. Ergänzende Gießrunden (**ergänzend** aktiviert) können außerdem nicht gleichzeitig die Anwendungsart **Fertigation** verwenden.

### Aus einem Ausbringungskanal protokollieren

Ist ein Nährstoffplan-Phaseneintrag mit einem [Ausbringungskanal](fertilization.md#ausbringungskanaele-multi-channel-delivery) verknüpft, kannst du den Gießvorgang direkt aus dem Kanal heraus protokollieren — das Formular ist dann bereits mit Anwendungsmethode, Ziel-EC/-pH und den Dünger-Dosierungen des Kanals vorausgefüllt.

---

## Eintrag ansehen und bearbeiten

Klicke einen Eintrag in der Liste an, um zur Detailseite zu gelangen. Sie zeigt zwei Tabs:

- **Details**: Verknüpfte Pflanzen/Stellplätze, Mess- und Ablaufwerte, verwendete Dünger, sowie — falls vorhanden — wer den Vorgang durchgeführt hat, der zugehörige Ausbringungskanal und der verknüpfte Nährstoffplan.
- **Bearbeiten**: Alle Felder außer den verknüpften Pflanzen/Stellplätzen lassen sich nachträglich korrigieren.

Auf der Detailseite kannst du außerdem über den Button **„Ablauf analysieren"** eine Runoff-Analyse für diesen Eintrag anstoßen (benötigt EC/pH/Volumen sowohl für die Zufuhr als auch für den Ablauf). Sie bewertet EC-Drift, pH-Drift und Ablaufmenge und gibt eine Gesamteinschätzung sowie Hinweise pro Kennwert aus — siehe [Ablaufanalyse](../guides/nutrient-mixing.md#ablaufanalyse-runoff) für die zugrunde liegenden Schwellenwerte.

---

## Häufige Fragen

??? question "Werden automatische Bewässerungen über Home Assistant protokolliert?"
    Nein, aktuell nicht automatisch. Es gibt derzeit keine automatische Übernahme von Home-Assistant-Bewässerungsereignissen in das Gießprotokoll — Einträge entstehen durch manuelle Erfassung, durch Bestätigen eines Gießplan-Termins oder durch Bestätigen einer Pflegeerinnerung (Gießen/Düngen).

??? question "Wie lange werden Gießprotokoll-Einträge aufbewahrt?"
    Für das Gießprotokoll gibt es derzeit keine eigene automatische Verdichtung oder Löschfrist — Einträge bleiben erhalten, bis du sie manuell löschst oder deine Daten im Rahmen der DSGVO-Betroffenenrechte löschen lässt.

??? question "Kann ich Einträge im Protokoll nachträglich korrigieren?"
    Ja. Öffne den Eintrag und wechsle zum Tab **Bearbeiten**.

??? question "Muss ich jeden Gießvorgang erfassen?"
    Nein, das ist optional. Kamerplanter funktioniert auch ohne vollständige Dokumentation. Willst du aber die Runoff-EC verfolgen oder deine Nährstoffgabe optimieren, lohnt sich eine konsequente Erfassung.

---

## Siehe auch

- [Dünge-Logik](fertilization.md) — Nährstoffpläne und Ausbringungskanäle (REQ-004)
- [Pflanzdurchläufe](planting-runs.md) — Gießplan konfigurieren
- [Tankmanagement](tanks.md) — Bewässerungstanks und Befüllungen
- [Guides: Nährlösung mischen](../guides/nutrient-mixing.md) — Ablaufanalyse-Schwellenwerte
