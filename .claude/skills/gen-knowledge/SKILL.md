---
name: gen-knowledge
description: "Generiert qualitativ hochwertige YAML-Knowledge-Dokumente fuer die RAG-Vektordatenbank (spec/knowledge/rag/). Recherchiert Themen gruendlich und erzeugt fachlich korrekte, chunked, retrieval-optimierte Dokumente. Nutze diesen Skill wenn neue Wissensdokumente zu Pflanzenpflege, Duengung, Diagnostik, Umweltsteuerung, Outdoor-Anbau oder Bewaesserung erstellt werden sollen."
argument-hint: "<Thema> [--category <kategorie>] [--level <beginner|intermediate|expert>]"
disable-model-invocation: true
---

# Knowledge-Dokument generieren: $ARGUMENTS

## Ueberblick

Erzeuge ein qualitativ hochwertiges YAML-Knowledge-Dokument fuer die Kamerplanter RAG-Vektordatenbank.
Diese Dokumente werden vom `KnowledgeIngestor` (`src/backend/app/domain/engines/knowledge_ingestor.py`)
eingelesen, in Chunks zerlegt, embedded und in TimescaleDB/pgvector indexiert. Sie bilden die
Wissensgrundlage fuer den KI-Assistenten (REQ-031).

## Schritt 1: Argument parsen

Parse `$ARGUMENTS` nach:
- **Thema** (Pflichtfeld): Das Hauptthema des Dokuments (z.B. "Hydroponik Grundlagen", "Tomaten Bluetezeit", "LED vs HPS")
- **--category** (optional): Zielkategorie — eine von: `allgemein`, `bewaesserung`, `diagnostik`, `duengung`, `outdoor`, `phasen`, `umwelt`. Falls nicht angegeben, aus dem Thema ableiten.
- **--level** (optional): Expertise-Level — `beginner`, `intermediate`, `expert` oder Kombination. Falls nicht angegeben, alle Level abdecken.

Falls das Thema unklar oder zu breit ist, frage den Nutzer nach Praezisierung.

## Schritt 2: Bestehendes Wissen pruefen

1. Lies das Verzeichnis `spec/knowledge/rag/` (Glob `spec/knowledge/rag/**/*.yaml`)
2. Pruefe ob ein Dokument zum gleichen oder stark ueberlappenden Thema bereits existiert
3. Falls ja: Melde dem Nutzer welches Dokument existiert und frage ob:
   - Das bestehende Dokument **erweitert** werden soll
   - Ein **neues Dokument** mit anderem Fokus erstellt werden soll
   - Abbruch

## Schritt 3: Recherche

Fuehre eine gruendliche Recherche zum Thema durch:

1. **Interne Quellen pruefen:**
   - Relevante REQ-Dokumente in `spec/req/` (Grep nach Themen-Keywords)
   - Bestehende Knowledge-Dokumente die das Thema tangieren (fuer Querverweise)
   - Seed-Daten in `src/backend/seeds/` (botanische Referenzdaten)
   - Backend-Code fuer Kamerplanter-spezifische Berechnungen/Features

2. **Externe Quellen recherchieren:**
   - Nutze WebSearch fuer aktuelle, wissenschaftlich fundierte Informationen
   - Mindestens 3-5 unabhaengige Quellen konsultieren
   - Bevorzuge: Universitaets-Publikationen, Agrar-Forschungsinstitute, etablierte Gartenbau-Fachliteratur
   - Vermeide: Einzelne Blog-Posts, Foren-Meinungen, Herstellerwerbung

3. **Fakten verifizieren:**
   - Zahlenwerte (pH-Bereiche, EC-Werte, Temperaturen, Dosierungen) muessen aus mindestens 2 Quellen uebereinstimmen
   - Bei widerspruchlichen Quellen: den konservativen/sicheren Wert waehlen und im Text darauf hinweisen
   - Einheiten immer angeben (mg/L, mS/cm, kPa, °C, g/m², ml/L)

## Schritt 4: Dokument strukturieren

Plane die Chunk-Struktur. Jeder Chunk wird separat embedded — daher gelten folgende Regeln:

### Chunk-Design-Prinzipien (KRITISCH fuer RAG-Qualitaet):

1. **Selbsterklaerend**: Jeder Chunk muss OHNE Kontext der anderen Chunks verstaendlich sein.
   Ein Chunk darf nicht mit "Wie oben erwaehnt..." beginnen oder auf andere Chunks verweisen.

2. **Ein Thema pro Chunk**: Jeder Chunk beantwortet genau EINE Frage oder erklaert genau EIN Konzept.
   Nicht: "VPD-Berechnung und Zielwerte und Messung" — sondern 3 separate Chunks.

3. **Retrieval-optimiert**: Der Titel und die ersten 2-3 Saetze muessen die wichtigsten Keywords enthalten,
   da diese fuer die Embedding-Qualitaet entscheidend sind. Fachbegriffe sowohl deutsch als auch
   englisch benennen (z.B. "Dampfdruckdefizit (VPD, Vapor Pressure Deficit)").

4. **Chunk-Laenge**: 150-400 Woerter pro Chunk. Zu kurz = zu wenig Kontext fuer sinnvolle Antwort.
   Zu lang = Embedding wird verwaschen, Praezision leidet.

5. **Praxis zuerst**: Jeder Chunk soll praktisch anwendbares Wissen enthalten, nicht nur Theorie.
   Konkrete Zahlen, Dosierungen, Handlungsanweisungen.

6. **Abgrenzung/Differenzialdiagnose**: Bei diagnostischen Themen IMMER abgrenzen
   ("NICHT verwechseln mit...", "Abgrenzung zu..."). Verwechslungen sind die haeufigste
   Fehlerquelle in der RAG-Antwort.

7. **Kamerplanter-Referenz**: Wo sinnvoll, einen Bezug zum Kamerplanter-System herstellen
   (welches Feature/REQ relevant ist). Das erhoeht die Antwortqualitaet wenn Nutzer
   systemspezifische Fragen stellen.

### Chunk-Aufbau (pro Chunk):

```yaml
- id: kebab-case-eindeutig        # Einzigartig innerhalb der Datei
  title: Praegnanter Titel         # 5-10 Woerter, keyword-reich
  content: |                       # Multiline YAML Block-Scalar
    Erklaerungstext...
    Konkrete Werte/Dosierungen...
    Praxis-Tipps...
    Kamerplanter-Referenz (optional)...
  metadata:                        # Strukturierte Daten fuer Retrieval-Enrichment
    topic: snake_case_topic        # Hauptthema (wird in Embedding angereichert)
    # Weitere Key-Value-Paare je nach Thema (Zahlen, Ranges, Enums)
```

### Metadata-Felder die vom Ingestor fuer Embedding-Enrichment genutzt werden:

Diese Keys werden automatisch als `"key: value"` ans Embedding angehaengt:
- `nutrient`, `symbol`, `deficiency_type`, `affected_leaves`, `severity_indicator`, `type`, `trigger`, `approach`

Weitere Metadata-Felder sind frei waehlbar und werden als JSON gespeichert (nicht embedded),
aber sind fuer zukuenftige Filter-Queries nuetzlich. Verwende numerische Ranges als Strings
(z.B. `"5.8-6.2"`) und Listen fuer Multi-Value-Felder.

## Schritt 5: Dokument schreiben

Schreibe die YAML-Datei nach `spec/knowledge/rag/{category}/{kebab-case-dateiname}.yaml`.

### Datei-Header (Pflicht):

```yaml
---
title: Beschreibender Titel des Gesamtdokuments
category: {kategorie}
tags: [tag1, tag2, tag3, ...]  # 5-15 Tags, deutsch, lowercase, keine Umlaute
expertise_level: [beginner, intermediate, expert]  # Welche Level profitieren
applicable_phases: [seedling, vegetative, flowering, harvest]  # Relevante Phasen
chunks:
  - id: ...
    ...
```

### Schreibregeln:

1. **Sprache**: Deutsch (Fachwissen-Dokument), aber Fachbegriffe auch auf Englisch nennen
2. **Umlaute**: KEINE Umlaute in YAML-Strings verwenden (ae, oe, ue, ss statt ae, oe, ue, ss).
   Das ist Konvention im gesamten `spec/knowledge/rag/` Verzeichnis.
3. **Formatierung im Content**: Einfache Markdown-artige Listen (- Item), Nummerierungen (1. 2. 3.).
   KEIN Markdown-Heading (#), keine Links, keine Bilder.
4. **Zahlen**: Immer mit Einheit, Ranges mit Bindestrich (z.B. "5.8-6.2 pH", "0.3-0.5 ml/L")
5. **Dateiname**: `{thema-in-kebab-case}.yaml` — kurz, beschreibend, deutsch, keine Umlaute
6. **Mindestens 3 Chunks**, idealerweise 4-8 pro Dokument

## Schritt 6: Qualitaetspruefung

Pruefe das erstellte Dokument gegen diese Checkliste:

- [ ] YAML ist syntaktisch korrekt (kein Parsing-Fehler)
- [ ] Jeder Chunk hat `id`, `title`, `content`, `metadata`
- [ ] Chunk-IDs sind eindeutig und kebab-case
- [ ] Kein Chunk verweist auf andere Chunks ("wie oben", "siehe unten")
- [ ] Jeder Chunk ist selbsterklaerend (allein lesbar)
- [ ] Content-Laenge pro Chunk: 150-400 Woerter
- [ ] Keine Umlaute (ae/oe/ue/ss statt ae/oe/ue/ss)
- [ ] Tags sind lowercase, ohne Umlaute, 5-15 Stueck
- [ ] Metadata enthaelt mindestens `topic` Feld
- [ ] Zahlen haben Einheiten
- [ ] Mindestens ein Kamerplanter-Bezug im Dokument
- [ ] Abgrenzungen/Differenzialdiagnosen wo angebracht
- [ ] Keine widerspruchlichen Aussagen zu bestehenden Knowledge-Docs

Validiere die YAML-Syntax:
```bash
python3 -c "import yaml; yaml.safe_load(open('spec/knowledge/rag/{category}/{dateiname}.yaml'))"
```

## Schritt 7: Benchmark-Integration (optional)

Falls das Thema diagnostisch ist (Kategorie `diagnostik` oder `duengung`):

1. Pruefe ob `spec/rag-eval/benchmark_questions.yaml` Fragen enthaelt die das neue Dokument beantworten sollte
2. Falls ja: Notiere dem Nutzer welche Benchmark-Fragen nun besser beantwortet werden koennten
3. Falls nein: Schlage 2-3 neue Benchmark-Fragen vor die zum neuen Dokument passen

Falls das Thema neue Keywords einfuehrt:
- Schlage Ergaenzungen fuer `spec/rag-eval/topic_synonyms.yaml` vor

## Qualitaetskriterien (die ein GUTES von einem MITTELMASSIGEN Dokument unterscheiden):

1. **Spezifitaet**: "Giesse alle 2-3 Tage" ist schlecht. "Finger-Test: Erde 2-3cm tief pruefen,
   bei trockenem Gefuehl giessen" ist gut.
2. **Abgrenzung**: "Vergilbung kann viele Ursachen haben" ist schlecht. "Gleichmaessige Vergilbung
   UNTERER Blaetter = N-Mangel. Intervenale Chlorose UNTERER Blaetter = Mg-Mangel. Intervenale
   Chlorose OBERER Blaetter = Fe-Mangel" ist gut.
3. **Zahlen**: Jede quantifizierbare Aussage muss eine konkrete Zahl haben. "Nicht zu viel duengen"
   ist schlecht. "Max. EC 1.2 mS/cm in der Saemlings-Phase, 1.5-2.0 mS/cm vegetativ" ist gut.
4. **Kontext**: Immer angeben WANN und FUER WEN ein Tipp gilt. "Substrat feucht halten" gilt nicht
   fuer Kakteen. "In der Bluete weniger N" gilt nicht fuer Blattpflanzen.
5. **Fehlertoleranz**: Angeben was passiert wenn der Wert ueber-/unterschritten wird.
   Nicht nur den Optimalwert, auch die Konsequenzen bei Abweichung.
