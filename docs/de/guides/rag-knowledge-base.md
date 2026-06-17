# RAG-Wissensbasis verstehen

Der KI-Assistent in Kamerplanter antwortet nicht aus dem Gedächtnis eines allgemeinen Sprachmodells — er gründet jede Antwort auf deine eigenen Daten und eine kuratierte Wissensbasis. Diese Technik heißt **Retrieval-Augmented Generation (RAG)** (KI-Antwortgenerierung auf Basis abgerufener Kontextdaten). Diese Seite erklärt, wie das System aufgebaut ist und warum es so funktioniert.

---

## Warum RAG?

Ein Sprachmodell, das allein aus seinem Training antwortet, hat zwei Schwächen:

1. **Halluzinationen** — Es erfindet plausibel klingende, aber falsche Fakten
2. **Kein Kontext** — Es kennt nicht deine spezifische Pflanze, deine aktuellen Messwerte oder deine Pflegehistorie

RAG löst beide Probleme: Das System sucht vor jeder Antwort relevante Informationen aus einer geprüften Datenbank und stellt sie dem Modell als Grundlage bereit. Das Modell kombiniert diese Fakten mit deiner konkreten Situation — statt aus dem Gedächtnis zu spekulieren.

!!! tip "Einfach erklärt"
    Stell dir RAG wie einen sehr gut vorbereiteten Assistenten vor: Er hat vor deiner Frage blitzschnell in der Bibliothek nachgeschlagen und kommt mit den passenden Fachbüchern zum Gespräch. Er erfindet nichts — er erklärt, was er gefunden hat.

---

## Das 4-Ebenen-Modell

Die Wissensbasis von Kamerplanter besteht aus vier Ebenen, die bei jeder Anfrage kombiniert werden.

<!-- diagram-source: user-described — 4-level RAG knowledge base feeding the retriever, context builder, and prompt assembler -->
```mermaid
flowchart TB
    subgraph "Level 1: Global Master Data"
        E1[Plant species, cultivars, growth phases,<br/>nutrient profiles, pests, diseases]
    end

    subgraph "Level 2: Thematic Guides"
        E2[31 curated expert knowledge files:<br/>Diagnostics, fertilization, irrigation,<br/>environment, phases, outdoor, general]
    end

    subgraph "Level 3: Tenant Context"
        E3[Active planting run, phase,<br/>measurements EC/pH/VPD,<br/>active IPM events, recent feeding events]
    end

    subgraph "Level 4: Your Plant Data"
        E4[Care history, harvest results,<br/>plant diary entries, confirmations]
    end

    E1 --> RAG[RAG Retriever<br/>pgvector]
    E2 --> RAG
    E3 --> CB[Context Builder<br/>ArangoDB]
    E4 --> CB

    RAG --> PA[Prompt Assembler]
    CB --> PA
    PA --> LLM[Language Model]
    LLM --> Response
```

**Ebenen 1 und 2** werden als Vektoren gespeichert und per Ähnlichkeitssuche abgerufen.
**Ebenen 3 und 4** werden zur Laufzeit als strukturierter Text in jede Anfrage eingefügt.

### Ebene 1: Globale Stammdaten

Die Kamerplanter-Stammdaten sind die Grundlage aller Empfehlungen:

- Pflanzenarten mit Taxonomie, Pflegeanforderungen und Eigenschaften
- Sorten mit spezifischen Besonderheiten
- Wachstumsphasendefinitionen mit VPD-Zielen, Licht- und Temperaturanforderungen
- Nährstoffprofile pro Art und Phase
- Schädlings- und Krankheitsdaten mit Symptomen und Behandlungsmethoden

Diese Daten werden wöchentlich neu indexiert.

### Ebene 2: Thematische Guides

Thematische Guides enthalten Querschnittswissen, das sich nicht aus den Stammdaten ableiten lässt — also Expertenwissen, das für viele Pflanzenarten und Situationen gilt. Aktuell umfasst die Wissensbasis 31 kuratierte Guides in sieben Kategorien:

| Kategorie | Beispiel-Guides |
|-----------|----------------|
| Diagnostik | Nährstoffmangel-Symptome, pH/EC-Abweichungen, Schädlingsfrüherkennung, Wurzelgesundheit |
| Umwelt | VPD-Optimierung, Lichtgrundlagen, Temperatursteuerung, CO₂-Anreicherung |
| Düngung | EC-Management (Hydroponik/Erde), organische Freilanddüngung, CalMag-Korrektur, Mischreihenfolge |
| Bewässerung | Gießstrategien nach Substrat, Überwässerung erkennen, Wasserqualität |
| Phasen | Keimung, vegetative Optimierung, Blütemanagement, Ernte-Timing, Überwintern |
| Outdoor | Saisonplanung, Mischkultur, Fruchtfolge, Wetterreaktionen |
| Allgemein | Anfänger-Einstieg, häufige Fehler vermeiden, Ertragsoptimierung |

!!! note "Agrarbiologisch geprüft"
    Alle Guides werden vor der Aufnahme in die Wissensbasis auf fachliche Korrektheit geprüft. Das System enthält außerdem 100 Benchmark-Fragen, gegen die jede neue Version der Wissensbasis getestet wird.

### Ebene 3: Tenant-Kontext (Echtzeit)

Bei jeder Anfrage holt der Context-Builder den aktuellen Zustand deiner Anlage aus der Datenbank:

- Aktive Pflanzdurchläufe mit aktueller Wachstumsphase und Phasendauer
- Letzte Messwerte: EC, pH, VPD, Temperatur, Luftfeuchtigkeit
- Aktive IPM-Ereignisse (Schädlingsbefall, Krankheiten, laufende Behandlungen)
- Letzte Dünge-Ereignisse mit Mengen und Produkten

### Ebene 4: Deine Pflanzdaten (Echtzeit)

Mit deiner Einwilligung fließen auch persönliche Pflegedaten in den Kontext:

- Pflegebestätigungen (wann wurde gegossen, gedüngt, geschnitten)
- Einträge im Pflanztagebuch
- Ergebnisse vergangener Ernten

---

## Ein Ablauf-Beispiel

So läuft eine typische Anfrage durch das System:

!!! example "Beispiel: Gelbe Blätter"

    **Deine Frage:** "Meine unteren Blätter werden gelb — was kann das sein?"

    **Schritt 1 — Context-Builder liest deine Daten:**
    ```
    Art: Cannabis sativa 'Northern Lights'
    Phase: Flowering, Tag 21
    EC: 1,2 mS/cm, pH: 5,8, VPD: 1,1 kPa
    Letzte Düngung: vor 2 Tagen (Standard-Nährlösung)
    ```

    **Schritt 2 — RAG-Retriever sucht passende Chunks:**
    - Stammdaten-Chunk: "Cannabis sativa, Flowering-Phase, NPK-Ziel 5-15-14"
    - Guide-Chunk: "Stickstoff-Mangel: untere Blätter gelb, EC erhöhen..."
    - Guide-Chunk: "Blütemanagement: N-Bedarf sinkt ab Woche 3, natürlicher N-Abbau..."

    **Schritt 3 — Modell kombiniert alles:**
    > "Deine Northern Lights ist in Woche 3 der Blüte. Gelbe untere Blätter können auf N-Mangel hindeuten, ABER: In der späten Blüte ist ein natürlicher N-Abbau in den unteren Blättern normal. Dein EC liegt bei 1,2 — das ist für Woche 3 Flowering etwas niedrig. Empfehlung: EC auf 1,4–1,6 anheben, NICHT den N-Anteil erhöhen (PK-Phase). Wenn mehr als 30 % der Blätter betroffen sind, leichten N-Boost erwägen."

Ohne die Thematischen Guides würde das Modell nur den Stammdaten-Kontext kennen und allgemeine Tipps geben. Ohne deinen Echtzeit-Kontext (EC 1,2, Woche 3 Blüte) würde das Modell nicht wissen, dass die Situation grenzwertig ist.

---

## Qualitätssicherung der Wissensbasis

### Agrarbiologische Prüfung

Alle Guides und Stammdaten werden vor der Aufnahme von erfahrenen Pflanzenanwendern auf fachliche Korrektheit geprüft. Besonderes Augenmerk gilt:

- Korrekte VPD- und EC-Zielwerte pro Phase und Substrat
- Übereinstimmung von Symptombeschreibungen mit aktueller Fachliteratur
- Sicherheitshinweise (Mischungsreihenfolgen, Karenzzeiten)

### Benchmark-Evaluation

Das System enthält 100 Benchmark-Fragen, deren Antworten bei jeder Wissensbasis-Aktualisierung automatisch evaluiert werden:

- **Topic-Match** — Sind die gefundenen RAG-Chunks relevant für die Frage?
- **LLM-as-Judge** — Bewertet ein zweites Modell die Antwortqualität
- **A/B-Vergleich** — Bei Modelländerungen: Verbesserung gegenüber der Vorversion?

---

## Eigene Guides hinzufügen (Admin)

Tenant-Admins können eigene thematische Guides zur lokalen Wissensbasis hinzufügen. Das ist sinnvoll für:

- Sortenspezifisches Spezialwissen
- Betriebsinterne Protokolle und Erfahrungswerte
- Guides in anderen Sprachen

### YAML-Format

```yaml
---
title: Mein eigener Guide-Titel
category: duengung          # diagnostik | umwelt | duengung | bewaesserung | phasen | outdoor | allgemein
tags: [ec, naehrstoff, hydroponik]
expertise_level: [intermediate, expert]
applicable_phases: [vegetative, flowering]
chunks:
  - id: mein-erster-chunk
    title: Abschnittstitel
    content: |
      Hier steht das Wissen in Freitext. Der Inhalt wird als Vektor
      indexiert und bei passenden Anfragen abgerufen.

      Empfehlung: Konkrete, handlungsorientierte Texte sind
      besser als allgemeine Beschreibungen.
    metadata:
      nutrient: nitrogen
      substrate: coco
```

### Guide hochladen

1. Öffne **Einstellungen > KI-Wissensbasis**
2. Klicke auf **Guide hochladen**
3. Wähle deine YAML-Datei aus
4. Das System validiert das Format und zeigt eine Vorschau
5. Bestätige mit **Importieren**

Der neue Guide wird beim nächsten Reindex-Zyklus (täglich, 06:00 Uhr UTC) in die Vektordatenbank aufgenommen. Du kannst den Reindex auch manuell anstoßen.

!!! warning "Qualitätsverantwortung"
    Eigene Guides werden nicht automatisch geprüft. Du bist für die fachliche Korrektheit deiner Guides verantwortlich. Fehlerhafte Guides können die Qualität der KI-Antworten verschlechtern.

---

## Wissensbasis reindexieren (Operator/Entwickler)

Nach Änderungen an den Knowledge-YAML-Dateien unter `spec/knowledge/rag/` müssen die Vektoren in pgvector neu berechnet werden. Das passiert automatisch wöchentlich (Sonntag 03:00 UTC), kann aber auch manuell angestoßen werden.

### Voraussetzungen

- Die Knowledge-YAML-Dateien sind im Container unter `/app/knowledge` gemountet (passiert automatisch bei Skaffold-Deployment)
- VectorDB (pgvector) und Embedding-Service müssen laufen
- `vectordb_enabled: true` in der Backend-Konfiguration

### Workflow: Chunk ändern → deployen → reindexieren → testen

```bash
# 1. Knowledge-YAML-Dateien bearbeiten
#    z.B. spec/knowledge/rag/diagnostik/naehrstoffmangel-symptome.yaml

# 2. Neu deployen (damit die Dateien im Container ankommen)
skaffold dev   # oder: skaffold run

# 3. Celery-Task manuell triggern
kubectl exec -it deploy/celery-worker -- \
  celery -A app.tasks call app.tasks.vector_indexing_tasks.reindex_vector_chunks

# 4. Benchmark laufen lassen (optional, empfohlen)
cd tools/rag-eval
source ~/.venvs/rag-eval/bin/activate
python eval_rag.py
```

### Alternative: Task direkt im Python-Interpreter auslösen

```bash
kubectl exec -it deploy/celery-worker -- python -c "
from app.tasks.vector_indexing_tasks import reindex_vector_chunks
result = reindex_vector_chunks.delay()
print(f'Task ID: {result.id}')
"
```

### Was passiert beim Reindex?

1. Alle YAML-Dateien unter `/app/knowledge` werden gelesen
2. Jeder Chunk wird mit dem Embedding-Modell vektorisiert (`paraphrase-multilingual-MiniLM-L12-v2`, 384 Dimensionen)
3. Vektoren werden per Upsert in `ai_vector_chunks` geschrieben (bestehende Chunks werden aktualisiert, neue hinzugefügt)
4. Der Task gibt eine Zusammenfassung zurück: Anzahl Dateien, Anzahl Chunks, Dauer

!!! tip "Schneller Feedback-Loop"
    Für die iterative Verbesserung der Wissensbasis empfiehlt sich dieser Zyklus:

    1. Benchmark laufen lassen → Failures identifizieren
    2. Fehlende oder ungenaue Chunks in den YAML-Dateien ergänzen/verbessern
    3. Deployen und reindexieren
    4. Benchmark erneut laufen lassen → Score-Verbesserung prüfen

    Details zum Benchmark-Tool: siehe `tools/rag-eval/README.md`

---

## Häufige Fragen

??? question "Kann die KI außerhalb der Wissensbasis recherchieren (Internet-Suche)?"
    Nein. Das System führt keine Internet-Suche durch. Alle Antworten basieren ausschließlich auf der lokalen Wissensbasis (Stammdaten, Guides) und deinen eigenen Pflanzdaten. Das ist eine bewusste Designentscheidung, um Halluzinationen zu vermeiden und Datenschutz zu gewährleisten.

??? question "Wie aktuell sind die Thematischen Guides?"
    Die Guides werden mit jedem Kamerplanter-Update gepflegt. Der genaue Stand ist in der Versionsdokumentation ([Changelog](../changelog/index.md)) vermerkt. Eigene Guides, die du hochgeladen hast, bleiben immer aktuell bis du sie aktualisierst oder löschst.

??? question "Was passiert, wenn kein passender Guide-Chunk gefunden wird?"
    Das System fällt auf die Stammdaten zurück (Ebene 1) und nutzt den strukturierten Kontext (Ebene 3+4). Die Antwortqualität ist dann geringer, aber das System antwortet trotzdem — ohne zu halluzinieren.

??? question "Werden meine eigenen Guides mit anderen Nutzern geteilt?"
    Nein. Eigene Guides sind tenant-scoped — sie sind nur für deinen Garten/deine Organisation sichtbar und werden nicht mit der globalen Wissensbasis oder anderen Tenants geteilt.

---

## Siehe auch

- [KI-Assistent verwenden](../user-guide/ai-assistant.md)
- [KI-Provider einrichten](../user-guide/ai-providers.md)
- [KI-Architektur (Entwickler)](../architecture/ai-architecture.md)
- [VPD-Optimierung](vpd-optimization.md)
- [Nährlösung mischen](nutrient-mixing.md)
