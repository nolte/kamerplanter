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
- Aktive [IPM](../user-guide/pest-management.md)-Ereignisse (Integrierter Pflanzenschutz — Schädlingsbefall, Krankheiten, laufende Behandlungen)
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

!!! warning "Noch nicht implementiert"
    Eine Verwaltungsoberfläche zum Hochladen eigener, tenant-spezifischer Guides gibt es aktuell nicht — weder im Frontend noch als eigenständiger Speicherbereich im Backend. Alle thematischen Guides stammen aus den kuratierten YAML-Dateien unter `spec/knowledge/rag/`, die zentral gepflegt und bei jedem Deployment in den Knowledge-Service-Container gemountet werden. Das folgende YAML-Format beschreibt, wie ein Guide-Chunk aufgebaut ist — es dient bereits heute als Vorlage für die zentral gepflegten Guides, eine tenant-eigene Upload-Funktion wird es erst in einer künftigen Version geben.

Sobald diese Funktion verfügbar ist, werden Tenant-Admins eigene thematische Guides zur lokalen Wissensbasis hinzufügen können — sinnvoll für sortenspezifisches Spezialwissen, betriebsinterne Protokolle oder Guides in anderen Sprachen.

### YAML-Format (Referenz)

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

!!! note "Qualitätsverantwortung"
    Auch nach Einführung der Upload-Funktion werden eigene Guides nicht automatisch fachlich geprüft. Fehlerhafte Guides können die Qualität der KI-Antworten verschlechtern.

---

## Wissensbasis reindexieren (Operator/Entwickler)

Nach Änderungen an den Knowledge-YAML-Dateien unter `spec/knowledge/rag/` müssen die Vektoren in der VectorDB (pgvector) neu berechnet werden. Es gibt **keinen automatischen Zeitplan** dafür — der Reindex muss nach jeder inhaltlichen Änderung manuell über den Knowledge-Service angestoßen werden.

### Voraussetzungen

- Die Knowledge-YAML-Dateien sind im Knowledge-Service-Container unter `/app/knowledge` gemountet (passiert automatisch bei Skaffold-Deployment)
- Der Knowledge-Service und sein Embedding-Service müssen laufen
- `INTERNAL_SERVICE_TOKEN` ist gesetzt (der Endpunkt ist service-token-geschützt, siehe [Fehlerbehandlung](../api/error-handling.md))

### Workflow: Chunk ändern → deployen → reindexieren → testen

```bash
# 1. Knowledge-YAML-Dateien bearbeiten
#    z.B. spec/knowledge/rag/diagnostik/naehrstoffmangel-symptome.yaml

# 2. Neu deployen (damit die Dateien im Knowledge-Service-Container ankommen)
skaffold dev   # oder: skaffold run

# 3. Reindex über den Knowledge-Service-Endpunkt auslösen
kubectl exec -it deploy/knowledge-service -- \
  curl -sX POST http://localhost:8000/ingest \
  -H "Authorization: Bearer $INTERNAL_SERVICE_TOKEN"

# 4. Benchmark laufen lassen (optional, empfohlen)
cd tools/rag-eval
source ~/.venvs/rag-eval/bin/activate
python eval_rag.py
```

### Was passiert beim Reindex?

1. Alle YAML-Dateien unter `/app/knowledge` werden gelesen
2. Jeder Chunk wird mit dem Embedding-Modell vektorisiert (`multilingual-e5-large`, 1024 Dimensionen, siehe [ADR-006](../adr/006-embedding-modell-e5-base-hybrid-search.md))
3. Vektoren werden per Upsert in `ai_vector_chunks` geschrieben (bestehende Chunks werden anhand ihres `source_key` aktualisiert, neue hinzugefügt)
4. Der Endpunkt gibt eine Zusammenfassung zurück: Anzahl Dateien, Anzahl Chunks

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
    Die Guides werden mit jedem Kamerplanter-Update gepflegt. Der genaue Stand ist in der Versionsdokumentation ([Changelog](../changelog/index.md)) vermerkt.

??? question "Was passiert, wenn kein passender Guide-Chunk gefunden wird?"
    Das System fällt auf die Stammdaten zurück (Ebene 1) und nutzt den strukturierten Kontext (Ebene 3+4). Die Antwortqualität ist dann geringer, aber das System antwortet trotzdem — ohne zu halluzinieren.

??? question "Kann ich eigene Guides für meinen Tenant hinzufügen?"
    Noch nicht — das ist als künftige Funktion geplant (siehe oben). Aktuell stammen alle thematischen Guides aus der zentral gepflegten Wissensbasis unter `spec/knowledge/rag/` und gelten für alle Tenants gleichermaßen.

---

## Siehe auch

- [KI-Assistent verwenden](../user-guide/ai-assistant.md)
- [KI-Provider einrichten](../user-guide/ai-providers.md)
- [KI-Architektur (Entwickler)](../architecture/ai-architecture.md)
- [VPD-Optimierung](vpd-optimization.md)
- [Nährlösung mischen](nutrient-mixing.md)
