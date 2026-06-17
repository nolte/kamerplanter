# Pflanzdurchläufe

Ein Pflanzdurchlauf (Planting Run) gruppiert zusammengehörige Pflanzen für ein gemeinsames Lifecycle-Tracking. Statt 20 Tomaten einzeln zu verwalten, legst du einen Durchlauf an — und kannst dann Phasenübergänge, Gießereignisse und Ernte-Batches auf die ganze Gruppe anwenden.

---

## Voraussetzungen

- Mindestens eine Site mit einer Location
- Stammdaten: Pflanzenart (Spezies) muss angelegt sein
- Optional: Nährstoffplan für die Gruppe

---

## Was ist ein Pflanzdurchlauf?

Ein Pflanzdurchlauf ist ein leichtgewichtiger Gruppencontainer. Er selbst hat keinen eigenen Lebenszyklus — er gruppiert nur Pflanzen. Jede Pflanze im Durchlauf behält ihre volle Eigenständigkeit:

- Einzelne Pflanzen können individuell bearbeitet werden
- Eine Pflanze kann jederzeit aus dem Durchlauf herausgelöst werden
- Phasen-Übergänge können für alle Pflanzen gleichzeitig oder für einzelne separat ausgelöst werden

**Drei Typen von Pflanzdurchläufen:**

| Typ | Beschreibung | Beispiel |
|-----|-------------|---------|
| **Monokultur** | Alle Pflanzen sind eine Art und eine Sorte | 20 Tomaten "San Marzano" |
| **Klon** | Stecklinge einer Mutterpflanze | 10 Cannabis-Klone von Mutter "WW-01" |
| **Mischkultur** | Mehrere Arten in einer Gruppe | Tomaten + Basilikum + Tagetes |

---

## Einen neuen Pflanzdurchlauf anlegen

### Schritt 1: Zu Durchläufen navigieren

Klicke in der Navigation auf **Durchläufe**. Die Übersicht zeigt alle aktiven und vergangenen Pflanzdurchläufe.

### Schritt 2: Neuen Durchlauf erstellen

Klicke auf **Neuer Durchlauf**. Ein Dialog öffnet sich.

### Schritt 3: Grunddaten eingeben

| Feld | Beschreibung | Beispiel |
|------|-------------|---------|
| Name | Eindeutiger Name für den Durchlauf | "Tomaten Hochbeet A 2026" |
| Typ | Monokultur, Klon oder Mischkultur | Monokultur |
| Site | Welche Anlage? | "Mein Garten" |
| Standort (Location) | Konkreter Bereich | "Hochbeet A" |
| Geplanter Start | Wann soll gepflanzt werden? | 15.04.2026 |
| Notizen | Besondere Ziele oder Beobachtungen | "Versuch ohne Folienabdeckung" |

### Schritt 4: Pflanzen zum Durchlauf hinzufügen

Klicke auf **Eintrag hinzufügen**:

1. Wähle **Pflanzenart** (Spezies) aus den Stammdaten.
2. Wähle optional eine **Sorte** (Cultivar).
3. Gib die **Anzahl** der Pflanzen ein.
4. Wähle die **Rolle** (Primärpflanze, Begleitpflanze, Fangpflanze).
5. Wähle das **Substrat**.

Bei Mischkultur-Durchläufen kannst du mehrere Einträge mit unterschiedlichen Arten hinzufügen.

!!! example "Beispiel: Mischkultur-Beet"
    - Tomaten "Roma", 8 Stück, Rolle: Primärpflanze
    - Basilikum "Genovese", 12 Stück, Rolle: Begleitpflanze
    - Tagetes, 6 Stück, Rolle: Fangpflanze

### Schritt 5: Pflanzen erstellen lassen

Klicke auf **Pflanzen erstellen**. Kamerplanter legt automatisch alle Einzelpflanzen mit fortlaufenden IDs an (z.B. HOCHBEETA_TOM_01 bis HOCHBEETA_TOM_08).

---

## Status eines Pflanzdurchlaufs

Ein Pflanzdurchlauf durchläuft folgende Zustände:

<!-- diagram-source: user-described — planting run status lifecycle from planned through harvesting to completed or cancelled -->
```mermaid
stateDiagram-v2
    [*] --> Planned
    Planned --> Active : Plants moved in
    Active --> Harvesting : First harvest initiated
    Harvesting --> Completed : All plants harvested
    Active --> Cancelled : Cancel run
    Planned --> Cancelled : Cancel run
```

| Status | Beschreibung |
|--------|-------------|
| **Geplant** | Angelegt, noch nicht gestartet |
| **Aktiv** | Pflanzen eingezogen, Wachstum läuft |
| **Ernte** | Erste Ernte wurde durchgeführt, weitere folgen |
| **Abgeschlossen** | Alle Pflanzen geerntet oder entfernt |
| **Abgebrochen** | Durchlauf wurde vorzeitig beendet |

---

## Batch-Operationen

Die Stärke von Pflanzdurchläufen liegt in den Batch-Operationen — Aktionen, die du auf alle Pflanzen gleichzeitig anwenden kannst.

### Batch-Phasenübergang

Alle Pflanzen eines Durchlaufs gleichzeitig in die nächste Phase überführen:

1. Öffne den Pflanzdurchlauf.
2. Klicke auf **Batch-Phasenwechsel**.
3. Wähle die Zielphase (z.B. "Vegetativ" → "Blüte").
4. Überprüfe die Liste der berechtigten Pflanzen (Pflanzen, die bereits in einer späteren Phase sind, werden ausgeschlossen).
5. Bestätige.

### Gießen bestätigen (Batch)

Nach dem Gießen dokumentierst du das Ereignis für alle Pflanzen gleichzeitig:

1. Klicke auf **Gießen bestätigen**.
2. Das System schlägt die Menge und EC aus dem zugewiesenen Nährstoffplan vor.
3. Passe die Werte an, falls du anders gemischt hast.
4. Bestätige — für alle Pflanzen wird ein Gießereignis erfasst.

### Batch-Ernte erstellen

Eine Ernte für alle Pflanzen des Durchlaufs gleichzeitig dokumentieren:

1. Klicke auf **Ernte-Batch erstellen**.
2. Das System prüft alle Karenzzeiten.
3. Trage Frischmasse und Qualitätsbewertung ein.
4. Bestätige — ein Ernte-Batch wird mit allen Pflanzen des Durchlaufs verknüpft.

### Alle Pflanzen entfernen

Am Ende des Zyklus alle Pflanzen auf einmal als entfernt markieren:

1. Klicke auf **Alle Pflanzen entfernen**.
2. Bestätige. Der Durchlauf wechselt auf Status "Abgeschlossen".

---

## Nährstoffplan zuweisen

Einem Pflanzdurchlauf kannst du einen Nährstoffplan zuweisen. Das vereinfacht die Gießplanung erheblich:

1. Öffne den Durchlauf.
2. Klicke auf **Nährstoffplan zuweisen**.
3. Wähle einen Plan aus der Liste.

Der Plan bestimmt, welche Dünger in welcher Phase in welcher Dosierung verwendet werden. Beim Gießen schlägt Kamerplanter automatisch die phasengerechten Dosierungen vor.

---

## Einzelne Pflanzen aus dem Durchlauf lösen

Wenn eine Pflanze einen anderen Verlauf nehmen soll als die Gruppe (z.B. eine Pflanze zeigt Mangelerscheinungen und braucht individuelle Behandlung):

1. Öffne die Pflanze in der Durchlauf-Liste.
2. Klicke auf **Aus Durchlauf lösen**.
3. Die Pflanze bleibt aktiv, ist aber jetzt unabhängig.

Das Entfernen einer Pflanze aus dem Durchlauf löscht die Pflanze nicht.

---

## Sukzessions-Aussaat (gestaffelte Durchläufe)

Für kontinuierliche Ernte (z.B. alle 3 Wochen frischer Salat) unterstützt Kamerplanter gestaffelte Pflanzdurchläufe:

1. Erstelle den ersten Durchlauf wie gewohnt.
2. Klicke auf **Folgepflanzung anlegen**.
3. Wähle das Intervall (z.B. 21 Tage nach dem ersten Durchlauf).
4. Kamerplanter kopiert die Durchlauf-Konfiguration und versetzt das Startdatum entsprechend.

---

## Häufige Fragen

??? question "Muss ich zwingend Pflanzdurchläufe nutzen?"
    Nein. Du kannst Pflanzen auch einzeln anlegen und verwalten. Pflanzdurchläufe sind besonders nützlich, wenn du mehrere Pflanzen derselben Art gleichzeitig anbaust und gemeinsam verwalten möchtest.

??? question "Kann eine Pflanze in mehreren Durchläufen sein?"
    Nein. Eine Pflanze kann zu maximal einem Pflanzdurchlauf gehören. Wenn du eine Pflanze einem anderen Durchlauf zuordnen möchtest, musst du sie zuerst aus dem aktuellen Durchlauf lösen.

??? question "Was passiert mit den Pflanzen, wenn ich einen Durchlauf abbreche?"
    Die Pflanzen bleiben im System erhalten und werden als "aktiv" markiert. Diese sind dann nur nicht mehr dem Durchlauf zugeordnet. Du kannst sie anschließend einzeln weiterführen oder manuell entfernen.

??? question "Kann ich nachträglich Pflanzen zu einem laufenden Durchlauf hinzufügen?"
    Ja, solange der Durchlauf nicht abgeschlossen ist. Öffne den Durchlauf und klicke auf **Pflanzen hinzufügen**.

---

## Siehe auch

- [Stammdaten: Pflanzenarten](plant-management.md)
- [Wachstumsphasen](growth-phases.md)
- [Ernte](harvest.md)
- [Dünge-Logik](fertilization.md)
