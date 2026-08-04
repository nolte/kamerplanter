# Spezifikation: REQ-050 - KI-Analyse von Tagebuch-Einträgen

```yaml
ID: REQ-050
Titel: KI-Analyse von Tagebuch-Einträgen (Nutzer markiert, externer Agent analysiert asynchron über MCP)
Kategorie: KI & Beratung
Fokus: Beides (Zierpflanze & Nutzpflanze)
Technologie: Python 3.14+, FastAPI, ArangoDB, React 19, TypeScript 6, MCP (JSON-RPC über Streamable HTTP)
Status: Entwurf
Priorität: Mittel
Version: 1.0
Datum: 2026-08-04
Tags: [diary, ai-analysis, mcp, image-content, goose, async, opt-in]
Abhängigkeit: REQ-013 v2.4 (Pflanzdurchlauf — PlantDiaryEntry), REQ-033 v1.4 (MCP-Server — Werkzeuge, Bild-Content), NFR-013 v1.2 (Object-Storage — Attachments, Thumbnail-Renditions), REQ-024 v1.6 (Mandant, Permission-Matrix), REQ-049 v1.3 (Rollenvokabular), REQ-025 v1.5 (DSGVO — Einwilligungszweck), REQ-023 v1.10 (API-Keys)
Wird benötigt von: —
```

## Versionshistorie

| Version | Datum | Änderung |
|---------|-------|----------|
| 1.0 | 2026-08-04 | Erstentwurf — Markierung, Zustandsmaschine, Ergebnis-Ablage am Eintrag, MCP-Vertrag für externe Agenten. |

---

## 0. Verhältnis zu bestehenden Spezifikationen

REQ-050 erfindet **kein** neues Tagebuch, **kein** neues Speicherkonzept, **keinen** neuen
Server-KI-Pfad. Es fügt einem bestehenden Datensatz einen Zustand und ein Ergebnisfeld hinzu und
macht beides zusammen mit den Bildern über eine bereits vorhandene Schnittstelle zugänglich.

| Dokument | Was es liefert | Was REQ-050 daraus nutzt |
|----------|----------------|--------------------------|
| **REQ-013** | `PlantDiaryEntry` mit Freitext, Tags, Messwerten und `photo_refs` (≤ 5 Attachment-IDs), Tagebuch-Endpunkte | Der zu analysierende Datensatz. REQ-050 ergänzt nur Analyse-Zustand und Analyse-Ergebnis. |
| **NFR-013** | `attachments`-Collection, Storage-Adapter, Thumbnail-Renditions 128/512/1280 px WebP (§8.2), EXIF-Strip (§6.4) | Bildquelle. REQ-050 liefert **Renditions**, nie Originale, und führt **keine** neue Storage-Kategorie ein — Tagebuchfotos sind `category = diary`. |
| **REQ-033** | MCP-Server, `kp_`-API-Key-Auth, Mandantenbindung pro Aufruf, `ToolDispatcher` als einziger Kontrollpunkt, Audit, Idempotenz | Transportweg. REQ-050 ergänzt fünf Werkzeuge und den Bild-Content-Typ. |
| **REQ-024 / REQ-049** | Rollen je Mandant, Rechte-Vokabular | Markieren und Zurückschreiben sind Schreibrechte (Gärtner aufwärts), Lesen ist ein Leserecht. |
| **REQ-025** | Einwilligungszwecke, Löschklassen | Die Analyse ist ein eigener, opt-in-pflichtiger Verarbeitungszweck (§7). |

### 0.1 Abgrenzung zu den bestehenden KI-Diagnosewegen

Es gibt bereits zwei Diagnosepfade. REQ-050 ist ein dritter und überschneidet sich mit keinem
von beiden — der Unterschied liegt im **Anker**, im **Auslöser** und in der **ausführenden Seite**.

| | Anker | Auslöser | Wer rechnet | Eingabe |
|---|---|---|---|---|
| **REQ-036** KI-Diagnose-Assistent | Pflanze | interaktiver Dialog | Kamerplanter-Backend (Knowledge-Service) | kuratierter Symptom-Katalog + Pflanzenkontext |
| **REQ-038** CV-Pflanzendiagnose | einzelnes Foto | Upload / Inspektion | Kamerplanter (ONNX-Klassifikator, PlantCV) | ein Blattfoto |
| **REQ-050** Tagebuch-Analyse | **Tagebuch-Eintrag** | **Nutzer markiert den Eintrag** | **externer, vom Nutzer betriebener Agent** | Freitext + Tags + Messwerte + **alle** Fotos des Eintrags |

Der entscheidende Unterschied: REQ-036 und REQ-038 sind **Server-Funktionen**, die Rechenzeit,
Modellkosten und Betriebsverantwortung bei der Kamerplanter-Instanz lassen. REQ-050 verlagert
beides zum Nutzer — die Instanz stellt nur Daten bereit und nimmt ein Ergebnis entgegen. Sie ruft
**selbst kein Sprachmodell auf** und braucht dafür weder Schlüssel noch Budget noch Netzausgang.

Damit ist REQ-050 auch der einzige der drei Wege, der einen **erzählenden** Eintrag auswerten
kann („seit dem Umtopfen hängen die unteren Blätter, Substrat riecht sauer") statt eines
Katalogsymptoms oder eines isolierten Blattfotos.

---

## 1. Business Case

### 1.1 User Stories

**Als** Hobbygärtner
**möchte ich** einen Tagebuch-Eintrag mit Foto ankreuzen können und später die Einschätzung
einer KI direkt an diesem Eintrag wiederfinden,
**um** nicht bei jedem Problem einen separaten Diagnose-Dialog von vorn führen zu müssen.

**Als** Nutzer mit vielen Pflanzen
**möchte ich** über den Tag mehrere Einträge markieren und sie gesammelt analysieren lassen,
**um** die Auswertung dann laufen zu lassen, wenn es mir passt — nicht synchron beim Erfassen.

**Als** Nutzer mit vielen Pflanzen
**möchte ich** eine Übersicht über die Einträge **aller** meiner Pflanzen, in der ich auf einen
Blick sehe, wo schon ein Analyse-Ergebnis vorliegt,
**um** nicht Pflanze für Pflanze durchklicken zu müssen, um zu erfahren, was inzwischen fertig ist.

**Als** Nutzer, der gerade an einer Pflanze steht
**möchte ich** den Eintrag genau dort erfassen, wo ich die Pflanze offen habe,
**um** nicht in einer Gesamtliste erst wieder auswählen zu müssen, um welche Pflanze es geht.

**Als** datenschutzbewusster Nutzer
**möchte ich**, dass **nichts** automatisch an eine KI geht und ich pro Eintrag entscheide,
**um** die Kontrolle über meine Fotos und meine Notizen zu behalten.

**Als** technisch versierter Nutzer
**möchte ich** die Analyse mit meinem eigenen Agenten und meinem eigenen Modellzugang fahren,
**um** nicht an die Modellauswahl und die Kosten der Kamerplanter-Instanz gebunden zu sein.

**Als** Betreiber einer Self-Hosted-Instanz
**möchte ich**, dass diese Funktion meine Instanz **nicht** von einem externen KI-Dienst abhängig
macht,
**um** Kamerplanter weiterhin ohne Netzausgang und ohne Modellschlüssel betreiben zu können.

**Als** Nutzer eines Gemeinschaftsgartens
**möchte ich** wissen, wessen Beobachtungen eine Analyse überhaupt erfassen darf,
**um** nicht ungefragt die Notizen und Fotos anderer Mitglieder an ein Sprachmodell zu geben.

### 1.2 Geschäftliche Motivation

Das Tagebuch ist heute ein Datenfriedhof: Der Nutzer schreibt „braune Flecken an den unteren
Blättern" und lädt zwei Fotos hoch — und dann passiert nichts. Die Information ist erfasst, aber
sie führt zu keiner Aussage. Gleichzeitig ist genau dieser Eintrag der reichhaltigste Datenpunkt
im System: Freitext, Bilder, Messwerte und Pflanzenkontext an einer Stelle, vom Nutzer selbst als
bemerkenswert markiert.

REQ-050 schließt diese Lücke mit dem billigsten denkbaren Mittel — es verlagert die eigentliche
Analyse aus dem Produkt heraus. Das ist keine Notlösung, sondern die passende Arbeitsteilung:
Sprachmodelle mit Bildverständnis entwickeln sich schneller, als eine Anbauverwaltung ihnen
folgen kann, und der Nutzer hat den Zugang dazu ohnehin schon.

### 1.3 Scope-Abgrenzung

| In Scope (v1.0) | Out of Scope (v1.0) |
|-----------------|---------------------|
| Markieren/Entmarkieren eines Eintrags zur Analyse | Automatische Markierung durch Regeln oder Schwellwerte |
| Zustandsmaschine mit Lease gegen Doppelbearbeitung | Warteschlangen-Priorisierung, Fairness zwischen Mandanten |
| Ein Analyse-Ergebnis je Eintrag (das jüngste) | Versionierte Analyse-Historie (§9, O-01) |
| Fünf MCP-Werkzeuge als Vertrag für externe Agenten | Das Agenten-Rezept selbst (Repository `kamerplanter-goose`) |
| Bilder als MCP-Bild-Content aus vorhandenen Renditions | Ausliefern von Originalbildern über MCP |
| **Tagebuch-Erfassung an der Pflanzeninstanz** (§2.5.1) | Serverseitiger Modellaufruf jeglicher Art |
| **Mandantenweite Tagebuch-Übersicht mit Analyse-Status** (§2.5.2) | Analyse-Übersicht über Mandantengrenzen hinweg |
| Einwilligungszweck + Löschklassifizierung | Automatische Übernahme in IPM-Behandlungen (§9, O-03) |

### 1.4 Die Tagebuch-Oberfläche gibt es heute nicht — sie ist Teil dieser Anforderung

Im Frontend existiert **keine** Tagebuch-Oberfläche: weder Seite noch Route noch API-Modul;
lediglich der TypeScript-Typ `PlantDiaryEntry` ist vorhanden und wird nirgends verwendet. Das
Backend hat seit REQ-013 v2.0 sechs Tagebuch-Endpunkte, die nie eine Oberfläche bekommen haben.

Damit gibt es heute keinen Ort, an dem ein Nutzer einen Eintrag anlegen, markieren oder ein
Ergebnis lesen könnte. Eine Anforderung, die nur einen Zustand am Datensatz einführt und die
Oberfläche einer anderen Anforderung überlässt, wäre nicht benutzbar — deshalb sind
**Erfassung (§2.5.1) und Übersicht (§2.5.2) ausdrücklich Bestandteil von REQ-050**, nicht bloß
Vorbedingung.

Fachlich gehört die Tagebuch-Oberfläche zu REQ-013. Sie hier mitzuspezifizieren ist eine bewusste
Zuschnitt-Entscheidung: REQ-050 ist der Anlass, aus dem sie überhaupt entsteht, und die
Analyse-Anzeige ist von der Liste nicht sinnvoll zu trennen. REQ-013 bleibt die Quelle für den
Eintrag selbst (Felder, Endpunkte, Rechte); REQ-050 spezifiziert seine Darstellung.

---

## 2. Fachliche Anforderungen

### 2.1 Markieren ist eine Nutzerhandlung, immer

Ein Tagebuch-Eintrag wird **ausschließlich durch eine ausdrückliche Handlung** zur Analyse
freigegeben. Es gibt keinen Automatismus, keine Voreinstellung „alles analysieren", keinen
Regelsatz, der Einträge nach Typ oder Stichwort markiert. Diese Beschränkung ist die tragende
Datenschutzmaßnahme dieser Anforderung (§7) und darf nicht durch eine Komfortfunktion aufgeweicht
werden.

Die Markierung ist zurücknehmbar, solange die Analyse noch nicht begonnen hat.

### 2.2 Zustandsmaschine

Der Analysezustand hängt am Eintrag und kennt fünf Werte:

```
                    ┌──────────────────────────────────────┐
                    │                                      │
  none ──markieren──▶ requested ──beanspruchen──▶ in_progress ──erfolg──▶ completed
    ▲                    │                             │                      │
    │                    │                             └──fehler──▶ failed ────┤
    └──entmarkieren──────┘                                            │        │
                         ▲                                            │        │
                         └──────Lease abgelaufen ──────────────────────┘        │
                         └──────erneut markieren ────────────────────────────────┘
```

| Übergang | Wer | Bedingung |
|----------|-----|-----------|
| `none → requested` | Nutzer (Weboberfläche oder MCP) | Schreibrecht im Mandanten |
| `requested → none` | Nutzer | nur solange nicht beansprucht |
| `requested → in_progress` | Agent | Vergleiche-und-Setze auf `_rev`; setzt Lease |
| `in_progress → requested` | System | Lease abgelaufen (Vorgabe 15 Minuten) |
| `in_progress → completed` | Agent | Ergebnis übermittelt, Lease gültig |
| `in_progress → failed` | Agent | Fehler übermittelt, Lease gültig |
| `completed → requested` | Nutzer | erneute Analyse angefordert |
| `failed → requested` | Nutzer | Wiederholung nach Fehler |

**Warum ein Lease und nicht nur ein Statusfeld:** Zwei parallel laufende Agenten (oder ein
Rezept, das versehentlich zweimal gestartet wird) würden denselben Eintrag doppelt analysieren
und zweimal Modellkosten verursachen. Das Beanspruchen erfolgt daher als optimistisches
Vergleiche-und-Setze über die Dokumentrevision `_rev` — dasselbe Fencing-Muster, das das
Migrations-Framework für seinen Sperrmechanismus verwendet. Der zweite Beanspruchungsversuch
schlägt fehl, statt still zu überschreiben.

**Warum ein Lease mit Ablauf und nicht nur ein Sperrflag:** Ein abgestürzter oder abgebrochener
Agent würde einen Eintrag sonst dauerhaft in `in_progress` festhalten. Nach Ablauf des Lease
erscheint der Eintrag wieder im Arbeitsvorrat. Vorbild ist der Wiederanstoß hängengebliebener
Datenexporte nach 15 Minuten (REQ-025).

### 2.3 Was analysiert wird

Gegenstand der Analyse ist der **gesamte Eintrag**, nicht ein einzelnes Foto:

- Freitext (`text`) und Titel
- Eintragstyp (`entry_type`) und Tags
- strukturierte Messwerte (`measurements`)
- alle referenzierten Fotos (`photo_refs`, bis zu 5)
- der Pflanzenkontext: Art, Sorte, aktuelle Phase, Standort, Pflanzdatum

Der Pflanzenkontext ist Teil der Eingabe, weil dieselbe Verfärbung an einem Sämling und an einer
Pflanze in der Blüte unterschiedlich zu bewerten ist.

### 2.4 Ergebnis am Eintrag

Das Ergebnis wird **am Eintrag** persistiert, nicht in einer eigenen Sitzungs-Collection. Es
besteht aus einer Zusammenfassung, einer Liste von Befunden mit Konfidenz und Begründung, einer
Liste empfohlener Maßnahmen sowie der Herkunftsangabe (Modell, Rezeptversion, Zeitpunkt, welche
Fotos tatsächlich ausgewertet wurden).

Ein **Vorbehalt** (`disclaimer`) ist Pflichtbestandteil und wird in der Oberfläche immer
angezeigt: Die Aussage stammt von einem Sprachmodell, ist eine Hypothese und ersetzt keine
fachliche Prüfung. Dieselbe Vorsichtsregel gilt bereits für REQ-038.

Es wird genau **ein** Ergebnis je Eintrag geführt — eine erneute Analyse überschreibt das
vorherige. Eine Historie ist bewusst zurückgestellt (§9, O-01).

### 2.5 Weboberfläche

Die Oberfläche hat **zwei getrennte Orte** mit unterschiedlichen Aufgaben. Diese Trennung ist
verbindlich, nicht nur eine Layout-Empfehlung: Erfasst wird dort, wo man die Pflanze vor sich
hat; gesichtet wird dort, wo man alle Pflanzen zusammen sieht.

| | Ort | Aufgabe |
|---|-----|---------|
| **Erfassung** | Pflanzeninstanz-Detailseite, neuer Tab „Tagebuch" | Einträge anlegen, bearbeiten, löschen, Fotos anhängen, zur Analyse markieren |
| **Sichtung** | Eigene Tagebuch-Übersicht, mandantenweit | Alle Einträge **aller** Pflanzen zusammen, mit Analyse-Status auf einen Blick |

#### 2.5.1 Erfassung an der Pflanzeninstanz

Das Tagebuch einer Pflanze ist ein **Tab auf der Pflanzeninstanz-Detailseite** — neben dem
Foto-Galerie-Tab aus REQ-034, nach demselben Muster. Der Nutzer sieht dort ausschließlich die
Einträge dieser einen Pflanze, chronologisch absteigend.

- Anlegen eines Eintrags: Typ, Titel, Freitext, Tags, optionale Messwerte, bis zu 5 Fotos
  (Erfassungswege wie in REQ-034 §2.2 — Webcam, Smartphone-Kamera, Datei-Upload).
- Je Eintrag: Bearbeiten, Löschen, Fotos als Vorschau (512-px-Rendition), Lightbox bei Klick.
- Je Eintrag: Schalter **„Analysieren"** (nur mit Schreibrecht und nur für Einträge, die der
  Nutzer selbst verfasst hat bzw. bei Rolle Leitung, §7.2). Ist der Eintrag bereits markiert,
  wird der Schalter zu „Markierung zurücknehmen" — solange der Zustand `requested` ist.

**Warum die Erfassung nicht in der Übersicht liegt:** Ein Eintrag gehört immer zu genau einer
Pflanze. Ein Anlegen-Dialog in einer mandantenweiten Liste müsste die Pflanze erst erfragen —
ein zusätzlicher Schritt genau dort, wo der Nutzer ihn schon beantwortet hat, wenn er von der
Pflanze kommt.

#### 2.5.2 Tagebuch-Übersicht (mandantenweit)

Eine eigene Seite listet die Einträge **aller** Pflanzen des Mandanten in einer gemeinsamen,
chronologisch absteigenden Ansicht. Sie ist der Ort, an dem ein Nutzer den Analyse-Stand
überblickt, ohne Pflanze für Pflanze durchzuklicken.

Je Zeile werden dargestellt:

| Spalte | Inhalt |
|--------|--------|
| Datum | `created_at` des Eintrags |
| Pflanze | Name und Kennung der Pflanzeninstanz, verlinkt auf deren Detailseite |
| Art | Wissenschaftlicher bzw. gebräuchlicher Name |
| Typ | Eintragstyp (Beobachtung, Problem, Meilenstein, Messung, Foto, Notiz) |
| Titel / Auszug | Titel, sonst die ersten Zeichen des Freitexts |
| Fotos | Anzahl angehängter Fotos, mit Miniaturvorschau des ersten |
| **Analyse** | Zustandsanzeige, siehe unten |

**Die Analyse-Spalte ist der Kern dieser Ansicht** und unterscheidet fünf Zustände sichtbar
voneinander — nicht nur „Ergebnis ja/nein":

| Zustand | Darstellung |
|---------|-------------|
| `none` | neutral, „nicht markiert"; bei Schreibrecht als Schalter „Analysieren" bedienbar |
| `requested` | „wartet auf Analyse" — ausdrücklich **kein** Fortschrittsbalken, es gibt keine Zusage über die Dauer (§3) |
| `in_progress` | „wird analysiert", mit dem Zeitpunkt des Beanspruchens |
| `completed` | **Ergebnis vorhanden** — deutlich hervorgehoben, mit der Zusammenfassung als einzeilige Vorschau |
| `failed` | Fehlerhinweis mit der gemeldeten Ursache und der Möglichkeit, erneut zu markieren |

Filter und Sortierung, mindestens:

- **nach Analyse-Zustand** — insbesondere „nur mit Ergebnis" und „nur wartend". Das ist der
  häufigste Zugriff überhaupt: „Was ist inzwischen fertig?"
- nach Pflanze, Art, Eintragstyp, Tag und Zeitraum
- Freitextsuche über Titel und Text
- Sortierung nach Erfassungsdatum (Vorgabe) oder Analyse-Zeitpunkt

Ein Klick auf eine Zeile öffnet den vollständigen Eintrag samt Fotos und — falls vorhanden — dem
Analyse-Ergebnis.

Die Übersicht ist **mandantenweit**, zeigt also im Gemeinschaftsgarten auch Einträge anderer
Mitglieder. Markieren darf der Nutzer dort trotzdem nur die eigenen (§7.2); fremde Zeilen zeigen
den Analyse-Zustand, aber keinen Schalter.

**Der tragende Endpunkt existiert heute nicht.** REQ-013 kennt nur eine Aggregation **je
Pflanzdurchlauf** (`GET /planting-runs/{key}/diary`). Eine mandantenweite Liste über alle
Pflanzen — mit oder ohne Run — gibt es nicht. REQ-050 fordert sie:

```
GET /api/v1/t/{tenant_slug}/diary
```

| Parameter | Typ | Bedeutung |
|-----------|-----|-----------|
| `analysis_state` | `list[DiaryAnalysisState] \| None` | Filter, mehrfach angebbar |
| `plant_key`, `species_key` | `str \| None` | Filter |
| `entry_type`, `tag` | `str \| None` | Filter |
| `from`, `to` | `date \| None` | Zeitraum über `created_at` |
| `q` | `str \| None` | Freitextsuche über Titel und Text |
| `sort` | `'created_at' \| 'analyzed_at'` (Vorgabe `created_at`) | Sortierung, absteigend |
| `limit`, `offset` | `int` | Seitenweise, Vorgabe 50 |

Die Antwort trägt je Eintrag die Felder der Übersichtstabelle plus `analysis_state`,
`analysis.summary` (nur die Zusammenfassung, nicht das ganze Ergebnis) und die Kennung der
ersten Vorschau-Rendition. Das vollständige Ergebnis liefert erst der Einzelabruf — sonst
transportiert eine Liste mit 50 Zeilen 50 Befundlisten mit.

Die Liste ist strikt auf `tenant_key` gefiltert. Für die Filterung nach Analyse-Zustand ist
derselbe persistente Index nötig, den auch der MCP-Arbeitsvorrat braucht (§5).

#### 2.5.3 Darstellung des Ergebnisses

Wo ein Ergebnis vorliegt — in der Detailansicht des Eintrags, an beiden Orten gleich:

- Zusammenfassung als Erstes.
- Aufklappbare Befundliste: je Befund Bezeichnung, Konfidenz und Begründung. Die Konfidenz wird
  als Zahl **und** sprachlich eingeordnet; eine nackte Prozentzahl suggeriert eine Genauigkeit,
  die ein Sprachmodell nicht hat.
- Empfohlene Maßnahmen als Liste.
- Herkunftsangabe: Modell, Rezeptversion, Zeitpunkt, welche Fotos ausgewertet wurden.
- **Der Vorbehalt ist immer sichtbar**, nicht aufklappbar versteckt (§2.4).

#### 2.5.4 Aktualisierung

Der Zustand wird nicht live gepusht; ein Nachladen beim Öffnen der Ansicht genügt, ergänzt um
eine Auffrischen-Schaltfläche in der Übersicht. Es gibt keinen Server-zu-Client-Kanal im
MCP-Transport (REQ-033 §4.3a) und keinen Grund, für diese Funktion einen einzuführen.

---

## 3. Betriebsmodell: warum Kamerplanter Goose nicht kennt

Die Analyse führt ein **externer Agent** aus, den der Nutzer selbst betreibt — in der ersten
Ausbaustufe lokal auf seinem Rechner. Die Rezeptlogik entsteht im getrennten Repository
`kamerplanter-goose` und ist **nicht** Bestandteil dieses Produkts.

```
Nutzer markiert Eintrag                 externer Agent (lokal, Repo kamerplanter-goose)
        │                                            │
        ▼                                            │
  analysis_state = requested                         │
                                                     │
                             ┌───────────────────────┤
                             │  1. list_pending_diary_analyses   (mcp.read)
                             │  2. claim_diary_analysis          (mcp.write)
                             │  3. get_diary_entry               (mcp.read)
                             │  4. get_diary_entry_photos        (mcp.read, Bild-Content)
                             │  5. → Sprachmodell des Nutzers
                             │  6. submit_diary_analysis         (mcp.write)
                             └───────────────────────┤
                                                     │
        ▼                                            │
  analysis_state = completed, analysis = {...}       │
```

**Warum abholend und nicht anstoßend:** Kamerplanter enthält an keiner Stelle Kenntnis über
Goose — kein Abbild, kein Geheimnis, kein Modellschlüssel, kein ausgehender Aufruf, keine
Zustellgarantie zu verantworten. Der Server ist eine reine Datenquelle und -senke. Damit
funktioniert die Anforderung unverändert, wenn der Nutzer morgen ein anderes Agenten-Werkzeug
einsetzt, und sie hält die Self-Hosted-Zusage aus REQ-033 ein: Ohne den externen Agenten
funktioniert Kamerplanter unverändert, nur bleiben markierte Einträge in `requested` stehen.

**Konsequenz, die zu akzeptieren ist:** Es gibt keine Zusage über die Bearbeitungsdauer. Ein
Eintrag bleibt so lange `requested`, bis ein Agent läuft. Das ist der Preis der Entkopplung und
in der Oberfläche ehrlich als „wartet auf Analyse" zu benennen — nicht als Fortschrittsbalken zu
verkleiden.

---

## 4. MCP-Vertrag

Dies ist die Schnittkante zu `kamerplanter-goose` und die eigentliche normative Substanz dieser
Anforderung: Das Rezept muss sich **allein aus diesem Abschnitt** schreiben lassen, ohne in den
Kamerplanter-Quellcode zu sehen.

Alle fünf Werkzeuge sind mandantengebunden (Argument `tenant`, aufgelöst durch den Dispatcher
gegen die Mitgliedschaften des Schlüssels, bevor Rechte geprüft werden). Alle laufen durch den
`ToolDispatcher` als einzigen Kontrollpunkt und werden dort revisionssicher protokolliert
(REQ-033 §4.4, §6).

### 4.0 Gemeinsamer Vertrag aller fünf Werkzeuge

Ohne diesen Abschnitt kann ein externes Rezept weder eine Erfolgsantwort auslesen noch einen
Fehler erkennen. Er gilt für alle Werkzeuge in §4.1–§4.5.

**Erfolgsantwort.** Ein Werkzeugaufruf liefert das MCP-Standardergebnis: `content` mit dem
`summary`-Text als führendem Block, und `structuredContent` mit dem eigentlichen Nutzdatenobjekt.
Ein Rezept liest **`structuredContent`**, nicht den Text.

```json
{
  "content": [{ "type": "text", "text": "3 Einträge warten auf Analyse" }],
  "structuredContent": {
    "summary": "3 Einträge warten auf Analyse",
    "data": { "...": "werkzeugspezifisch, siehe §4.1–§4.5" },
    "links": [{ "type": "ui", "url": "https://kp.example.org/t/mein-garten/plants" }]
  },
  "isError": false
}
```

Schreibwerkzeuge tragen zusätzlich `dry_run`, `idempotency_key` und `idempotent_replay`
neben `summary` (REQ-033 §2.6).

**Fehlerantwort.** Jeder in §4.1–§4.5 genannte Fehlercode kommt als Werkzeug-Ergebnis mit
`isError: true` an — **nicht** als JSON-RPC-`error`. Ein JSON-RPC-`error` bedeutet ausschließlich
Protokoll- oder Authentifizierungsversagen (unbekannte Methode, ungültiger Schlüssel) und ist für
das Rezept nicht behandelbar.

```json
{
  "content": [{ "type": "text", "text": "Eintrag wird bereits analysiert" }],
  "structuredContent": {
    "error_code": "conflict.already_claimed",
    "message": "Eintrag wird bereits analysiert",
    "details": { "claimed_by": "goose-laptop", "lease_expires_at": "2026-08-04T12:15:00Z" }
  },
  "isError": true
}
```

`error_code` ist der maschinenlesbare Vertrag, `message` ist für Menschen und darf sich ändern.
Ein Rezept verzweigt **nie** über `message`.

**Für alle fünf Werkzeuge gilt zusätzlich:**

| Situation | `error_code` |
|-----------|--------------|
| `tenant` fehlt, aber der Schlüssel hat mehr als eine Mitgliedschaft | `validation.tenant_required` |
| `tenant` unbekannt oder Schlüssel dort nicht Mitglied | `not_found` |
| Rolle im aufgelösten Mandanten reicht für die Permission nicht | `permission.denied` |
| `entry_key` existiert nicht oder liegt in einem anderen Mandanten | `not_found` |

Ein fremder Mandant und ein fremder Eintrag liefern beide `not_found` und **nie**
`permission.denied` — sonst verriete die Fehlermeldung die Existenz fremder Daten (REQ-033).

**Zeitangaben** sind durchgängig ISO-8601 in UTC mit `Z`-Suffix.

### 4.1 `list_pending_diary_analyses` (`mcp.read`)

Liefert den Arbeitsvorrat.

| Eingabe | Typ | Bedeutung |
|---------|-----|-----------|
| `tenant` | `str \| None` | Mandant; entfällt bei genau einer Mitgliedschaft |
| `limit` | `int = 20` | Obergrenze 100; darüber `validation.error` |
| `include_stale` | `bool = true` | auch Einträge mit abgelaufenem Lease |

`data`:

```json
{
  "entries": [
    {
      "entry_key": "8271634",
      "plant_key": "5512099",
      "plant_name": "Tomate Beet 2 #05",
      "species_name": "Solanum lycopersicum",
      "entry_type": "problem",
      "title": "Braune Flecken unten",
      "created_at": "2026-08-03T18:22:11Z",
      "requested_at": "2026-08-04T07:05:00Z",
      "photo_count": 2,
      "analysis_state": "requested"
    }
  ],
  "total": 3
}
```

**Kein** Freitext, **keine** Bilder — der Arbeitsvorrat soll klein bleiben und ist noch keine
Übermittlung von Inhalten. `total` ist die Gesamtzahl wartender Einträge, unabhängig von `limit`.

Sortierung: `requested_at` aufsteigend (ältester zuerst). Ein leerer Arbeitsvorrat ist **kein**
Fehler, sondern `entries: []` mit `total: 0`.

Weitere Fehler über §4.0 hinaus: keine.

### 4.2 `claim_diary_analysis` (`mcp.write`)

Beansprucht einen Eintrag exklusiv.

| Eingabe | Typ | Bedeutung |
|---------|-----|-----------|
| `tenant` | `str \| None` | Mandant |
| `entry_key` | `str` | Eintrag |
| `worker_id` | `str` | frei wählbare Kennung des Agenten, landet in `analysis_claimed_by` |
| `lease_seconds` | `int = 900` | Obergrenze 3600 |
| `dry_run`, `idempotency_key` | | Standardvertrag für Schreibwerkzeuge (REQ-033 §2) |

Erfolg: Zustand `in_progress`, `analysis_claimed_at` und `analysis_claimed_by` gesetzt.

`data`:

```json
{
  "entry_key": "8271634",
  "lease_token": "01J9F2K7QW3M8N5P6R2S4T8V0X",
  "lease_expires_at": "2026-08-04T07:20:00Z",
  "photo_count": 2
}
```

`lease_token` muss `submit_diary_analysis` vorlegen. `lease_expires_at` sagt dem Agenten, wie
lange er Zeit hat — ohne diese Angabe müsste er `lease_seconds` selbst mitrechnen und läge bei
Uhrendrift daneben.

Fehlerfälle über §4.0 hinaus:

| Situation | `error_code` |
|-----------|--------------|
| Zustand ist nicht `requested` und Lease nicht abgelaufen | `conflict.already_claimed` |
| Revision hat sich zwischen Lesen und Setzen geändert | `conflict.concurrent_update` |
| `lease_seconds` über 3600 | `validation.error` |

`conflict.already_claimed` liefert in `details` die Felder `claimed_by` und `lease_expires_at`,
damit ein Agent entscheiden kann, ob er später wiederkommt. Auf `conflict.concurrent_update`
gehört ein sofortiger Wiederholungsversuch — er bedeutet nur, dass jemand parallel geschrieben
hat, nicht dass der Eintrag vergeben ist.

### 4.3 `get_diary_entry` (`mcp.read`)

Liefert den Eintrag **ohne** Bilddaten.

| Eingabe | Typ | Bedeutung |
|---------|-----|-----------|
| `tenant` | `str \| None` | Mandant |
| `entry_key` | `str` | Eintrag |

`data`:

```json
{
  "entry_key": "8271634",
  "entry_type": "problem",
  "title": "Braune Flecken unten",
  "text": "Seit dem Umtopfen hängen die unteren Blätter, Substrat riecht sauer.",
  "tags": ["blatt", "substrat"],
  "measurements": { "height_cm": 84, "leaf_count": 22 },
  "photo_refs": ["01HQ8X9V3J7P5K2N4M6T8R0S2W", "01HQ8X9V3J7P5K2N4M6T8R0S2X"],
  "created_at": "2026-08-03T18:22:11Z",
  "created_by": "user/4471023",
  "analysis_state": "in_progress",
  "plant": {
    "plant_key": "5512099",
    "plant_name": "Tomate Beet 2 #05",
    "instance_id": "HOCHBEETA_TOM_05",
    "species_key": "solanum_lycopersicum",
    "species_name": "Solanum lycopersicum",
    "cultivar_name": "San Marzano",
    "current_phase": "flowering",
    "phase_started_at": "2026-07-12T00:00:00Z",
    "location_name": "Hochbeet A",
    "planted_on": "2026-04-18"
  }
}
```

`measurements` ist ein offenes Objekt (REQ-013) — ein Rezept darf keine feste Schlüsselmenge
annehmen. Felder des `plant`-Objekts, die am Datensatz fehlen, kommen als `null`, nicht als
ausgelassener Schlüssel; damit bleibt die Struktur über alle Einträge gleich.

Getrennt von den Bildern, damit ein Agent den Textteil lesen kann, ohne das Token-Budget mit
Bilddaten zu belasten — etwa um zu entscheiden, ob er die Bilder überhaupt braucht.

Fehlerfälle über §4.0 hinaus: keine.

### 4.4 `get_diary_entry_photos` (`mcp.read`)

Liefert die Fotos als **Bild-Content-Blöcke**, damit ein bildverstehendes Modell sie unmittelbar
sieht.

| Eingabe | Typ | Bedeutung |
|---------|-----|-----------|
| `tenant` | `str \| None` | Mandant |
| `entry_key` | `str` | Eintrag |
| `photo_ids` | `list[str] \| None` | Auswahl; `None` = alle Fotos des Eintrags |
| `size` | `512 \| 1280` (Vorgabe `1280`) | auszuliefernde Rendition |

**Antwortform.** Dieses Werkzeug ist das einzige, dessen Nutzdaten **nicht** vollständig in
`structuredContent` liegen: Die Bilder sind Content-Blöcke, weil nur dort ein Sprachmodell sie
als Bild sieht. Reihenfolge der `content`-Liste: erst der `summary`-Textblock, dann ein
`image`-Block je geliefertem Foto — in derselben Reihenfolge wie `photos` in `structuredContent`.

```json
{
  "content": [
    { "type": "text", "text": "2 von 3 Fotos geliefert (1280 px)" },
    { "type": "image", "data": "UklGRt4…", "mimeType": "image/webp" },
    { "type": "image", "data": "UklGRp8…", "mimeType": "image/webp" }
  ],
  "structuredContent": {
    "summary": "2 von 3 Fotos geliefert (1280 px)",
    "data": {
      "entry_key": "8271634",
      "size": 1280,
      "photos": [
        { "photo_id": "01HQ…S2W", "status": "delivered", "content_index": 1, "byte_size": 184320 },
        { "photo_id": "01HQ…S2X", "status": "delivered", "content_index": 2, "byte_size": 201114 }
      ],
      "pending": [
        { "photo_id": "01HQ…S2Y", "status": "thumbnail_pending" }
      ]
    }
  },
  "isError": false
}
```

`content_index` verweist auf die Position im `content`-Array. Ein Rezept ordnet Bild und Kennung
darüber zu und **nicht** über die Position allein — sonst bricht die Zuordnung, sobald ein
weiterer Textblock hinzukommt.

**Es wird niemals das Original ausgeliefert**, sondern ausschließlich die beim Upload erzeugten
WebP-Renditions (NFR-013 §8.2). Drei Gründe, alle bindend:

1. **Token-Budget.** Ein Originalfoto darf 25 MB groß sein. Als Basis-64 im Protokoll wäre das
   für jedes Modell unbrauchbar.
2. **Datenschutz.** Renditions tragen keine EXIF-Daten — auch dann nicht, wenn der Mandant
   `STORAGE_KEEP_EXIF_DIARY=true` gesetzt hat; jenes Setting betrifft nur die Originaldatei.
   NFR-013 §8.2 hält das seit v1.3 ausdrücklich als Anforderung fest, statt es als Nebenwirkung
   der Neukodierung anzunehmen. Genau darauf stützt sich die Zulässigkeit der Auslieferung.
3. **Kosten.** 1280 px ist für eine Blattdiagnose ausreichend und ein Vielfaches billiger als
   ein Originalbild.

**Obergrenze:** Die Gesamt-Nutzlast eines Aufrufs ist auf **4 MB** Basis-64 begrenzt
(`MCP_MAX_IMAGE_PAYLOAD_MB`, Vorgabe 4). Wird sie überschritten, antwortet das Werkzeug mit
`payload.too_large` und nennt in `details.photo_ids` die betroffenen Bilder sowie in
`details.suggested_size` die Rendition, mit der der Abruf passen würde.
**Stilles Kürzen ist unzulässig** — ein Agent, der glaubt, alle Fotos gesehen zu haben, während
zwei fehlten, zieht falsche Schlüsse und merkt es nie.

**Fehlende Rendition:** Renditions werden verzögert nachgeneriert (NFR-013 §8.2). Fehlt eine,
erscheint das Foto **nicht** in `photos` und **nicht** im `content`-Array, sondern in `pending`
mit `status: "thumbnail_pending"`; die Erzeugung wird angestoßen. Der Aufruf selbst bleibt
erfolgreich (`isError: false`); der Agent kann es später erneut versuchen. Ein harter Fehlschlag
wäre hier falsch, weil er einen Eintrag mit vier fertigen und einem fehlenden Bild vollständig
blockieren würde. Ein Rezept, das Vollständigkeit braucht, prüft `pending` auf leer — und darf
sich nicht darauf verlassen, dass ein erfolgreicher Aufruf alle Fotos enthält.

Fehlerfälle über §4.0 hinaus:

| Situation | `error_code` |
|-----------|--------------|
| Gesamt-Nutzlast über der Obergrenze | `payload.too_large` |
| `photo_ids` enthält Kennungen, die nicht an diesem Eintrag hängen | `validation.error` |
| `size` ist weder 512 noch 1280 | `validation.error` |

### 4.5 `submit_diary_analysis` (`mcp.write`)

Schreibt das Ergebnis zurück und beendet die Bearbeitung.

| Eingabe | Typ | Bedeutung |
|---------|-----|-----------|
| `tenant` | `str \| None` | Mandant |
| `entry_key` | `str` | Eintrag |
| `lease_token` | `str` | aus `claim_diary_analysis` |
| `status` | `'completed' \| 'failed'` | Ausgang |
| `summary` | `str`, max. 2000 Zeichen | ein bis drei Sätze, Pflicht bei `completed` |
| `findings` | `list`, max. 10 Einträge | je `label` (max. 200), `confidence` (0.0–1.0), `rationale` (max. 2000) |
| `recommended_actions` | `list[str]`, max. 10 | konkrete Maßnahmen |
| `analyzed_photo_ids` | `list[str]`, max. 5 | welche Fotos tatsächlich eingingen |
| `model` | `str`, max. 200 | verwendetes Modell |
| `recipe_version` | `str`, max. 50 | Version des Rezepts |
| `error` | `str \| None` | Pflicht bei `failed` |
| `dry_run`, `idempotency_key` | | Standardvertrag für Schreibwerkzeuge |

Die Längengrenzen stehen hier bewusst **doppelt** (auch in §5) — ein Rezept, das nur §4 liest,
muss sie kennen, sonst läuft es blind in `validation.error`.

`data` bei Erfolg — das persistierte Ergebnis wird zurückgespiegelt, inklusive des
serverseitig gesetzten `disclaimer`, damit der Agent sieht, was tatsächlich am Eintrag steht:

```json
{
  "entry_key": "8271634",
  "analysis_state": "completed",
  "analysis": {
    "summary": "Vermutlich Staunässe nach dem Umtopfen, kein Pilzbefall erkennbar.",
    "findings": [
      { "label": "Staunässe / Wurzelstress", "confidence": 0.72, "rationale": "Saurer Substratgeruch …" }
    ],
    "recommended_actions": ["Substrat abtrocknen lassen", "Drainage prüfen"],
    "analyzed_photo_ids": ["01HQ…S2W", "01HQ…S2X"],
    "model": "claude-opus-5",
    "recipe_version": "1.0.0",
    "analyzed_at": "2026-08-04T07:14:52Z",
    "disclaimer": "Diese Einschätzung stammt von einem Sprachmodell …"
  }
}
```

Bei `status: 'failed'` entfällt `analysis`; stattdessen steht `analysis_error` mit dem
übermittelten Text im `data`-Objekt.

Fehlerfälle über §4.0 hinaus:

| Situation | `error_code` |
|-----------|--------------|
| Eintrag nicht `in_progress` | `conflict.not_claimed` |
| `lease_token` passt nicht zum aktuellen Lease | `conflict.lease_expired` |
| `status='completed'` ohne `summary` | `validation.error` |
| `status='failed'` ohne `error` | `validation.error` |
| `analyzed_photo_ids` enthält Kennungen, die nicht am Eintrag hängen | `validation.error` |
| eine der Längengrenzen überschritten | `validation.error` |
| `confidence` außerhalb 0.0–1.0 | `validation.error` |

Der Vorbehalt (`disclaimer`) wird **serverseitig** gesetzt, nicht vom Agenten geliefert — sonst
könnte ein Rezept ihn weglassen oder abschwächen.

### 4.6 Protokoll-Erweiterung: Bild-Content

Der MCP-Transport liefert heute ausschließlich Text-Blöcke. `get_diary_entry_photos` erfordert
daher eine echte Erweiterung des Protokoll-Layers, die in **REQ-033 §4.3b** spezifiziert wird und
hier nur in ihren Auswirkungen festgehalten ist:

- Eine Werkzeug-Antwort kann neben `summary` und den strukturierten Daten eine Liste von
  Content-Blöcken tragen; `image`-Blöcke führen Basis-64-Daten und `mimeType`.
- Der führende Text-Block bleibt `summary` — er ist heute das Einzige, was ein Sprachmodell aus
  der Antwort sieht, und das muss so bleiben, damit bestehende Werkzeuge sich nicht ändern.
- Bilder laufen bewusst über `tools/call` und **nicht** über MCP-Ressourcen. Ressourcen sind im
  Server nicht implementiert und würden am `ToolDispatcher` als einzigem Kontrollpunkt für
  Mandantenbindung, Rechteprüfung und Protokollierung vorbeiführen. Das wäre für Bilddaten die
  falsche Reihenfolge.
- Die protokollierte Antwortgröße muss Bild-Nutzlasten gesondert ausweisen oder deckeln, sonst
  verzerrt ein einziger Fotoabruf die Betriebsmetrik gegenüber allen anderen Werkzeugen.

---

## 5. Datenmodell

Additive Felder an `PlantDiaryEntry` (`plant_diary_entries`). Alle optional, Vorgabewerte
entsprechen dem heutigen Verhalten — bestehende Einträge bleiben unverändert gültig und brauchen
keine Datenmigration.

| Feld | Typ | Vorgabe | Bedeutung |
|------|-----|---------|-----------|
| `analysis_state` | `'none' \| 'requested' \| 'in_progress' \| 'completed' \| 'failed'` | `'none'` | Zustand (§2.2) |
| `analysis_requested_at` | `datetime \| None` | `None` | wann markiert |
| `analysis_requested_by` | `str \| None` | `None` | `user_key` des Markierenden |
| `analysis_claimed_at` | `datetime \| None` | `None` | Beginn des Lease |
| `analysis_claimed_by` | `str \| None` | `None` | `worker_id` des Agenten |
| `analysis_lease_expires_at` | `datetime \| None` | `None` | Ablauf des Lease |
| `analysis` | `DiaryAnalysis \| None` | `None` | jüngstes Ergebnis |
| `analysis_error` | `str \| None` | `None` | Fehlertext bei `failed` |

```python
class DiaryFinding(BaseModel):
    """Ein einzelner Befund der KI-Analyse."""
    label: str = Field(max_length=200)
    confidence: float = Field(ge=0.0, le=1.0)
    rationale: str = Field(max_length=2000)


class DiaryAnalysis(BaseModel):
    """Ergebnis einer KI-Analyse eines Tagebuch-Eintrags (REQ-050)."""
    summary: str = Field(max_length=2000)
    findings: list[DiaryFinding] = Field(default_factory=list, max_length=10)
    recommended_actions: list[str] = Field(default_factory=list, max_length=10)
    analyzed_photo_ids: list[str] = Field(default_factory=list, max_length=5)
    model: str = Field(max_length=200)
    recipe_version: str = Field(max_length=50)
    analyzed_at: datetime
    disclaimer: str  # serverseitig gesetzt, siehe §4.5
```

**Kein neuer Knoten, keine neue Kante.** Das Ergebnis ist ein eingebettetes Teildokument am
Eintrag. Eine eigene Collection wäre erst mit der Historie (§9, O-01) gerechtfertigt.

**Index:** Für `list_pending_diary_analyses` (§4.1) **und** für die Zustandsfilter der
mandantenweiten Übersicht (§2.5.2) ist ein persistenter Index über
`(tenant_key, analysis_state, analysis_requested_at)` anzulegen, sonst wird beides zum
Sammelscan über alle Tagebuch-Einträge des Mandanten.

---

## 6. Berechtigungen

Vokabular gemäß REQ-049 §3.1: Beobachter → Gärtner → Leitung.

| Handlung | Beobachter | Gärtner | Leitung | MCP-Recht |
|----------|-----------|---------|---------|-----------|
| Analyse-Zustand und Ergebnis lesen | ✓ | ✓ | ✓ | `mcp.read` |
| Tagebuch-Übersicht öffnen (§2.5.2) | ✓ | ✓ | ✓ | `mcp.read` |
| Eintrag markieren / Markierung zurücknehmen | ✗ | ✓ (nur eigene, §7.2) | ✓ | `mcp.write` |
| Eintrag beanspruchen | ✗ | ✓ | ✓ | `mcp.write` |
| Ergebnis zurückschreiben | ✗ | ✓ | ✓ | `mcp.write` |

Die MCP-Rechte werden aus der Rolle im **handelnden Mandanten** abgeleitet (REQ-033 §4.4), nicht
je Schlüssel vergeben. Ein Nutzer, der in Mandant A Gärtner und in Mandant B Beobachter ist, kann
mit demselben Schlüssel in A markieren und in B nicht.

> **Bekannte Vokabular-Drift in der zitierten Autorität:** REQ-033 §4.4 führt die Rollen noch als
> `viewer` / `grower` / `admin`, also im Einachsen-Modell vor REQ-049. REQ-024 v1.6 hat die
> Datenbasis bereits auf das Zwei-Achsen-Modell umgestellt; die Rolle `admin` existiert dort nicht
> mehr (`admin` → `lead` + beide Zusatzberechtigungen). Für REQ-050 gilt **REQ-049 als Autorität**;
> die Zuordnung ist `viewer` → Beobachter, `grower` → Gärtner, `admin` → Leitung. Die Migration von
> REQ-033 §4.4 und §2.3 auf das REQ-049-Vokabular ist eine eigene, hier bewusst nicht
> mitgezogene Aufgabe — sie betrifft alle 37 MCP-Werkzeuge, nicht nur diese fünf.

Ein Dienstkonto (REQ-023) kann Träger des Schlüssels sein. Das ist der saubere Weg für einen
dauerhaft laufenden Agenten, weil sich sein Zugriff getrennt vom persönlichen Konto widerrufen
lässt.

---

## 7. Datenschutz

Dies ist der Abschnitt, an dem diese Anforderung steht oder fällt: Ein markierter Eintrag
verlässt das System als Freitext **und** als Bild in Richtung eines Sprachmodells.

### 7.1 Einwilligung und Freiwilligkeit

- Die Analyse ist **opt-in je Eintrag** und wird nie automatisch ausgelöst (§2.1). Das ist die
  tragende Schutzmaßnahme.
- Zusätzlich greift der Verarbeitungszweck `diary_ai_analysis`, registriert in REQ-025 v1.5.
  Widerrufbar; ein Widerruf verhindert neue Markierungen und lässt bestehende Ergebnisse
  unberührt.
- **Aufgelöster Widerspruch:** Der Zweck des serverseitigen KI-Assistenten
  (`ai_tenant_data_access`, REQ-025 / REQ-031) sagte pauschal zu, **Tagebuch-Freitexte würden
  nie übertragen**. Wörtlich gelesen hätte das die hier spezifizierte Freigabe verboten. REQ-025
  v1.5 präzisiert die Zusage auf den **serverseitigen** Weg und trennt beide Wege ausdrücklich;
  keiner der beiden Consents impliziert den anderen. Auch `ai_cloud_processing` gilt hier
  **nicht** — Modell und Anbieter wählt allein der Nutzer, außerhalb der Verantwortung der
  Instanz.

### 7.2 Wer sieht was

Der Abruf läuft über einen `kp_`-Schlüssel des Nutzers und sieht damit nichts, was der Nutzer
nicht auch in der Weboberfläche sieht (REQ-033).

**Das reicht hier aber nicht als Begründung.** In einem Gemeinschaftsgarten umfasst „was der
Nutzer sieht" auch Beobachtungen und Fotos anderer Mitglieder. Ein Mitglied könnte dort fremde
Einträge markieren und an sein Modell geben, ohne dass die Verfasser davon erfahren.

Für v1.0 gilt daher: **Markieren darf nur, wer den Eintrag selbst verfasst hat**
(`created_by == user_key`), oder wer die Rolle Leitung im Mandanten hat. Das ist die
konservative Auslegung; eine Lockerung auf mandantenweites Markieren ist eine bewusste
Produktentscheidung und bleibt offen (§9, O-02).

### 7.3 Datenminimierung

- Übermittelt werden ausschließlich Renditions, keine Originale (§4.4).
- Renditions tragen keine EXIF-Daten, also keine GPS-Position und keine Gerätekennung — auch
  nicht bei `STORAGE_KEEP_EXIF_DIARY=true`.
- Der Arbeitsvorrat (§4.1) enthält keinen Freitext und keine Bilder. Inhalte fließen erst, wenn
  ein Agent einen Eintrag beansprucht und gezielt abruft.
- `analysis_requested_by` und `analysis_claimed_by` sind für die Nachvollziehbarkeit nötig; ihre
  Behandlung bei Nutzerlöschung regelt §7.4.

### 7.4 Löschung und Aufbewahrung

- Das Analyse-Ergebnis ist Teil des Tagebuch-Eintrags und teilt dessen Schicksal: Löschen des
  Eintrags löscht das Ergebnis, Löschen der Pflanze löscht beides.
- **Nutzerlöschung — hier fehlt heute eine Regel, und REQ-050 schließt die Lücke.** Die
  Löschklasse `user_diary_attachments` (REQ-025 AK-OS-02) anonymisiert ausschließlich das
  `created_by` an den **Anhängen** in der `attachments`-Collection. Für das
  `plant_diary_entries`-Dokument selbst existiert bis heute **keine** Anonymisierungsregel —
  weder in REQ-025 noch in REQ-013. Der Eintragstext eines gelöschten Nutzers bliebe damit
  namentlich zugeordnet stehen.
  REQ-025 v1.5 ergänzt daher: In Erasure-Phase 2 werden an `plant_diary_entries` die Felder
  `created_by`, `analysis_requested_by` und `analysis_claimed_by` auf `_anonymized` gesetzt; das
  Dokument selbst bleibt erhalten, weil es zum Pflanzen-Datensatz eines womöglich geteilten
  Mandanten gehört — dieselbe Abwägung wie bei den Anhängen.
- Die Datenauskunft nach Art. 15 umfasst den Tagebuch-Eintrag samt Analyse-Ergebnis.
- Eine eigene Aufbewahrungsfrist für Analyse-Ergebnisse gibt es nicht; sie wäre gegenüber dem
  Eintrag, an dem sie hängen, willkürlich.

### 7.5 Light-Modus (REQ-027)

Eine Light-Instanz kennt keine Konten, und der Einwilligungsmechanismus ist dort abgeschaltet
(REQ-027) — es gibt niemanden, der `diary_ai_analysis` erteilen könnte. Ohne eine ausdrückliche
Regel wäre REQ-050 im Light-Modus dauerhaft unbenutzbar: Der MCP-Zugang funktioniert dort
(API-Schlüssel des System-Nutzers, REQ-033 §4.3a), aber die Markierung scheiterte immer an einer
Einwilligung, die niemand geben kann.

Das ist keine tragfähige Lage, denn der Light-Modus ist genau der Fall, in dem die Anforderung am
besten passt: eine Einzelperson auf eigener Hardware, die ihren eigenen Agenten betreibt.

**Festlegung:** Im Light-Modus gilt der Zweck `diary_ai_analysis` als erteilt und die Markierung
ist ohne Einwilligungsprüfung möglich. Die Begründung ist dieselbe, mit der REQ-027 den
Einwilligungsmechanismus insgesamt abschaltet: Es gibt keine getrennten Betroffenen, deren Daten
gegeneinander zu schützen wären, und die Verarbeitung fällt unter die Haushaltsausnahme. Auch die
Einschränkung „nur eigene Einträge" (§7.2) entfällt dort, weil alle Einträge demselben
System-Nutzer gehören.

**Abgrenzung zu `ai_cloud_processing`:** REQ-027 sperrt Cloud-Anbieter im Light-Modus hart, weil
dort *die Instanz* die Daten an einen Dritten überträgt und die fehlende Einwilligung nicht
heilbar ist. Hier ist es umgekehrt: Die Instanz überträgt nichts: Sie gibt Daten an einen Client
heraus, den der Nutzer selbst betreibt. Die Vertrauensgrenze einer Light-Instanz ist ihr Netz;
ein Agent, der ihren API-Schlüssel hat, ist innerhalb dieser Grenze. Die beiden Fälle sehen
ähnlich aus und sind es nicht.

### 7.6 Was Kamerplanter ausdrücklich nicht tut

- Kein Aufruf eines Sprachmodells durch die Instanz.
- Keine Speicherung von Modellschlüsseln.
- Keine Weitergabe an einen von Kamerplanter betriebenen Dienst.
- Keine Auswertung nicht markierter Einträge, zu keinem Zweck, auch nicht statistisch.

---

## 8. Akzeptanzkriterien

| ID | Kriterium |
|----|-----------|
| **AK-01** | Ein Nutzer mit Schreibrecht kann einen Tagebuch-Eintrag zur Analyse markieren; `analysis_state` wechselt von `none` auf `requested` und `analysis_requested_at`/`_by` sind gesetzt. |
| **AK-02** | Ein Beobachter kann Zustand und Ergebnis lesen, aber nicht markieren, nicht beanspruchen und nicht zurückschreiben (jeweils `permission.denied`). |
| **AK-03** | Eine Markierung im Zustand `requested` ist zurücknehmbar; im Zustand `in_progress` ist sie es nicht. |
| **AK-04** | `list_pending_diary_analyses` liefert ausschließlich Einträge des angefragten Mandanten, aufsteigend nach `requested_at`, ohne Freitext und ohne Bilddaten. |
| **AK-05** | `claim_diary_analysis` setzt `in_progress` plus Lease; ein zweiter Beanspruchungsversuch auf denselben Eintrag scheitert mit `conflict.already_claimed`, ohne den Zustand zu verändern. |
| **AK-06** | Nach Ablauf des Lease erscheint der Eintrag wieder in `list_pending_diary_analyses` und ist erneut beanspruchbar. |
| **AK-07** | `get_diary_entry_photos` liefert Bild-Content-Blöcke mit Basis-64 und `mimeType: image/webp` aus den 512- bzw. 1280-px-Renditions — niemals das Originalbild. |
| **AK-08** | Überschreitet die Gesamt-Nutzlast eines Fotoabrufs die konfigurierte Obergrenze, antwortet das Werkzeug mit `payload.too_large` und benennt die betroffenen `photo_ids`. Es wird **nie** still gekürzt. |
| **AK-09** | Fehlt eine Rendition, liefert der Abruf für dieses Foto `thumbnail_pending`, stößt die Erzeugung an und bleibt für die übrigen Fotos erfolgreich. |
| **AK-10** | `submit_diary_analysis` mit gültigem Lease persistiert das Ergebnis am Eintrag und setzt `completed` bzw. `failed`; ohne gültigen Lease scheitert es mit `conflict.not_claimed` oder `conflict.lease_expired`. |
| **AK-11** | Der Vorbehalt wird serverseitig gesetzt und ist auch dann vorhanden, wenn der Agent kein entsprechendes Feld liefert. |
| **AK-12** | Ein Eintrag aus einem fremden Mandanten liefert `not_found`, nie `permission.denied` (keine Preisgabe fremder Mandanten). |
| **AK-13** | Ohne erteilte Einwilligung `diary_ai_analysis` lässt sich kein Eintrag markieren; ein Widerruf verhindert neue Markierungen und lässt vorhandene Ergebnisse unberührt. |
| **AK-14** | Auf der Pflanzeninstanz-Detailseite gibt es einen Tagebuch-Tab, in dem ein Eintrag mit Typ, Titel, Freitext, Tags, Messwerten und bis zu 5 Fotos angelegt, bearbeitet, gelöscht und zur Analyse markiert werden kann (§2.5.1). |
| **AK-15** | Eine mandantenweite Tagebuch-Übersicht listet die Einträge **aller** Pflanzen chronologisch absteigend mit Pflanze, Art, Typ, Titel/Auszug, Fotoanzahl und Analyse-Zustand (§2.5.2). |
| **AK-16** | Die Übersicht unterscheidet alle fünf Analyse-Zustände sichtbar voneinander; `completed` ist als „Ergebnis vorhanden" hervorgehoben und zeigt die Zusammenfassung als Vorschau. |
| **AK-17** | Die Übersicht lässt sich nach Analyse-Zustand filtern — insbesondere „nur mit Ergebnis" und „nur wartend" — sowie nach Pflanze, Art, Typ, Tag und Zeitraum; die Freitextsuche greift auf Titel und Text. |
| **AK-18** | `GET /t/{slug}/diary` liefert ausschließlich Einträge des angefragten Mandanten, seitenweise, mit `analysis_state` und `analysis.summary` — nicht mit dem vollständigen Ergebnis. |
| **AK-19** | Ein Nutzer kann in einem geteilten Mandanten nur eigene Einträge markieren, sofern er nicht die Rolle Leitung hat; fremde Zeilen der Übersicht zeigen den Zustand, aber keinen Schalter. |
| **AK-20** | Der Vorbehalt ist in der Ergebnisdarstellung immer sichtbar und nicht hinter einem Aufklapp-Element versteckt. |
| **AK-21** | Eine erneute Analyse eines `completed`- oder `failed`-Eintrags ist möglich; sie setzt den Zustand auf `requested` und überschreibt beim Abschluss das vorherige Ergebnis vollständig. |
| **AK-22** | `submit_diary_analysis` weist Eingaben zurück, die eine Längengrenze aus §4.5 überschreiten, `confidence` außerhalb 0.0–1.0 tragen, bei `completed` kein `summary` oder bei `failed` kein `error` mitführen (jeweils `validation.error`). |
| **AK-23** | Löschen des Eintrags löscht das Analyse-Ergebnis; Löschen der Pflanze löscht beides. Bei Nutzerlöschung bleibt der Eintrag erhalten und `created_by`, `analysis_requested_by` und `analysis_claimed_by` sind auf `_anonymized` gesetzt. |
| **AK-24** | Die Datenauskunft nach Art. 15 enthält Tagebuch-Einträge samt Analyse-Ergebnis. |
| **AK-25** | Im Light-Modus ist die Markierung ohne Einwilligungsprüfung möglich und die Einschränkung „nur eigene Einträge" greift nicht (§7.5). |
| **AK-26** | Bestehende Tagebuch-Einträge ohne Analyse-Felder bleiben ohne Migration lesbar und schreibbar; `analysis_state` wird als `none` interpretiert. |
| **AK-27** | Ohne laufenden externen Agenten funktioniert Kamerplanter unverändert; markierte Einträge verbleiben in `requested` und die Oberfläche benennt das als „wartet auf Analyse" — ohne Fortschrittsanzeige. |
| **AK-28** | Alle Oberflächentexte liegen in DE und EN vor; DE ist Vorgabe und Rückfallsprache. |

---

## 9. Offene Punkte

| Nr. | Frage | Entscheider | Status |
|-----|-------|-------------|--------|
| O-01 | Soll eine **Historie** mehrerer Analysen je Eintrag geführt werden statt nur der jüngsten? Erst dann lohnt eine eigene Collection. | Produkt | offen |
| O-02 | Darf in einem Gemeinschaftsgarten ein Gärtner **fremde** Einträge zur Analyse markieren? v1.0 verneint das (§7.2); die Lockerung ist eine Produkt- und Datenschutzentscheidung. | Produkt + Datenschutz | offen |
| O-03 | Soll aus einem Befund direkt eine **IPM-Behandlung** (REQ-010) oder eine Diagnose-Sitzung (REQ-036) vorgeschlagen werden können? | Produkt | offen |
| O-04 | Soll `add_plant_diary_entry` (REQ-033 §2.2, bislang nicht umgesetzt) zusammen mit dieser Anforderung realisiert werden, damit ein Agent auch Einträge **anlegen** kann? | Produkt | offen |
| O-05 | Sollen die in REQ-013 §4.7 spezifizierten, aber nie implementierten **Standalone**-Tagebuch-Endpunkte (`/plant-instances/{key}/diary`) mit REQ-050 nachgezogen werden? Ohne sie hat eine Pflanze ohne Pflanzdurchlauf kein Tagebuch — die Erfassung nach §2.5.1 wäre dort nicht bedienbar. | Produkt | **blockierend** |
| O-06 | Soll die Obergrenze der Bild-Nutzlast je Mandant konfigurierbar sein oder global bleiben? | DevOps | offen |
| O-07 | Soll die Tagebuch-Übersicht (§2.5.2) an die Modul-Sichtbarkeit (REQ-042) gebunden werden, damit sie bei Nutzern ohne Tagebuch-Nutzung nicht in der Navigation erscheint? | Produkt | offen |

**Zur Einordnung:** O-05 ist die einzige blockierende Frage. Alle anderen lassen sich nach der
Umsetzung entscheiden, ohne bereits Gebautes zu entwerten. Die zuvor hier geführte Frage nach der
Tagebuch-Oberfläche ist entfallen — sie ist mit §2.5 beantwortet und Bestandteil dieser
Anforderung.

---

**Dokumenten-Ende**
**Version:** 1.0
**Status:** Entwurf
