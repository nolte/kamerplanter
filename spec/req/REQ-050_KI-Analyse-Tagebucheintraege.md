# Spezifikation: REQ-050 - KI-Analyse von Tagebuch-Einträgen

```yaml
ID: REQ-050
Titel: KI-Analyse von Tagebuch-Einträgen (Nutzer markiert, externer Agent analysiert asynchron über MCP)
Kategorie: KI & Beratung
Fokus: Beides (Zierpflanze & Nutzpflanze)
Technologie: Python 3.14+, FastAPI, ArangoDB, React 19, TypeScript 6, MCP (JSON-RPC über Streamable HTTP)
Status: Entwurf
Priorität: Mittel
Version: 1.6
Datum: 2026-08-16
Tags: [diary, ai-analysis, mcp, image-content, goose, async, opt-in]
Abhängigkeit: REQ-051 v1.0 (Pflanzen-Tagebuch — Oberfläche, Bearbeitung, Inhaltsversion, Analyse-Archiv), REQ-013 v2.7 (Pflanzdurchlauf — PlantDiaryEntry, Umgebungs-Schnappschuss §2.3a), REQ-033 v1.7 (MCP-Server — Werkzeuge, Bild-Content), NFR-013 v1.4 (Object-Storage — Attachments, Thumbnail-Renditions), REQ-024 v1.7 (Mandant, Permission-Matrix), REQ-049 v1.4 (Rollenvokabular), REQ-025 v1.6 (DSGVO — Einwilligungszweck), REQ-023 v1.13 (API-Keys), REQ-042 v1.1 (Modul-Sichtbarkeit — Registrierung der Übersicht), REQ-021 v1.4 (Erfahrungsstufen — Navigations-Zuordnung), REQ-027 (Light-Modus)
Wird benötigt von: REQ-051 (Analyse-Anzeige im Tagebuch)
```

## Versionshistorie

| Version | Datum | Änderung |
|---------|-------|----------|
| 1.6 | 2026-08-22 | **Nachforderung (§2.6).** Der häufigste Grund für einen schwachen Befund ist ein fehlendes Bild, und der Agent ist die einzige Partei im Ablauf, die weiß, welches — bis hierher konnte er es niemandem sagen. Eine Nachforderung ist die **Bitte** um bestimmte Motive, gestellt als Teil des Ergebnisses: sie markiert den Eintrag **nicht** neu, sodass §2.1 („Markieren ist immer eine Nutzerhandlung") und die Einwilligungsprüfung nach §7.1 unangetastet bleiben. Höchstens fünf Motive (die Fotogrenze eines Eintrags, REQ-013), höchstens eine offene je Eintrag (ein neuer Lauf setzt die alte auf `superseded`). §4.5 trägt dafür das Feld `photo_request`; den Auftrag legt der **Server** als FreeStyle-Aufgabe an (REQ-006 § FreeStyle, „Foto-Auftrag"), nicht der Aufrufer — die einzige Variante, die mit der Herkunfts-Vertrauensregel (#1000) und dem MCP-Katalog ohne schreibendes Aufgaben-Werkzeug (REQ-033) verträglich ist. Was der Nutzer beim Erfüllen sieht: REQ-051 §6.6. (#1237) |
| 1.5 | 2026-08-16 | **Die Tagebuch-Oberfläche wandert nach REQ-051.** §1.4 und §2.5.1–§2.5.4 sind dort aufgegangen, ebenso die Oberflächen-Kriterien AK-14…AK-17, AK-19, AK-20 und AK-28…AK-31 — **unter denselben Nummern**, damit bestehende Verweise (u. a. `spec/e2e-testcases/TC-REQ-050.md`) auflösbar bleiben. §1.4 hatte den Umzug bereits vorgezeichnet: die Oberfläche gehört fachlich nicht hierher, sie wurde nur hier mitspezifiziert, weil REQ-050 der Anlass ihrer Entstehung war. Mit einer eigenen Tagebuch-Anforderung entfällt dieser Grund. Gleichzeitig **O-01 mit „ja" entschieden** (Analyse-Historie, REQ-051 §5): §2.4 sagt nicht mehr, ein neues Ergebnis überschreibe das vorherige ersatzlos — es verdrängt es nur am Eintrag und wird archiviert. §5 trägt zusätzlich `analyzed_content_version` (REQ-051 §4.4). Zustandsmaschine, MCP-Vertrag und Datenschutz bleiben unverändert hier. |
| 1.4 | 2026-08-07 | **Umgebungs-Schnappschuss im Analyse-Payload (Issue #961).** §4.3 trägt zusätzlich `environment`, `environment_captured_at` und `environment_status`: der Agent bekam bisher die Fotos und den Freitext, aber nicht das Klima, in dem die Pflanze steht — die diagnostisch wertvollste Information, die kostenlos verfügbar ist. Das Feld ist **getrennt** von `measurements` und bleibt es (Begründung in REQ-013 §2.3a.1). `list_diary_entries` trägt es bewusst **nicht** — dieselbe Linie, die dieses Werkzeug schon beim Freitext zieht. `add_plant_diary_entry` meldet im Ergebnis `environment_status`, hat aber kein Eingabefeld dafür: ein Agent, der die Werte schreiben könnte, könnte sie erfinden. |
| 1.3 | 2026-08-05 | **O-04 entschieden: `add_plant_diary_entry` kommt, ohne `photo_refs`** (§9). Ein Agent konnte bis hierhin analysieren, aber nicht dokumentieren. Die beiden Grenzen der Entscheidung — keine Foto-Referenzen (SEC-003 lässt sie einem Service-Account ohnehin nicht zu) und kein Selbst-Markieren (§1.3, §7.1) — sind dort begründet. Das Werkzeug steht **außerhalb** des Analyse-Vertrags aus §4 und gehört zu REQ-033 §2.2. Ergänzt: `plant.cultivar_key` in §4.3 — die Prozess-Spezifikation des externen Agenten löst die Sorte über `get_cultivar` auf, das einen Schlüssel nimmt, und das Antwortschema trug nur `cultivar_name`. Nebenbei korrigiert: das Dokumentende trug noch „Version 1.1", während der Kopf 1.2 auswies. |
| 1.2 | 2026-08-05 | **Anlass: §2.5.2 verlangt für `in_progress` den „Zeitpunkt des Beanspruchens", das Antwortschema trug ihn nicht.** `DiaryOverviewItem` bekommt `analysis_claimed_at` (Beginn des Lease — nicht `analyzed_at`, das der Abschluss ist), samt der Regel, dass der Wert zu dem Lauf gehört, den der **angezeigte** Zustand beschreibt, und bei abgelaufenem Lease als `null` unterdrückt wird. Ergänzt um die Klarstellung, dass `analysis_state` auf **allen** Lesepfaden der angezeigte Zustand ist (abgelaufenes Lease liest sich überall als `requested`) und `can_request_analysis` **auch** an `DiaryEntryResponse` steht, nicht nur an der Übersichtszeile — beides war seit dem Vorgängerpaket so gebaut, die Spezifikation hinkte nach (§2.5.2, §5). |
| 1.1 | 2026-08-05 | **Korrekturen aus der Umsetzung (Issue #921)**, plus die beiden blockierenden offenen Punkte entschieden. §4.3: `created_by` ist der blanke `user_key` ohne Collection-Präfix; `analysis` und `analysis_error` ergänzt, ohne die ein Agent den Vorbefund einer Wiederholungsanalyse (AK-21) über keines der fünf Werkzeuge erreichte. §4.4: `pending[].status` kennt zusätzlich `unavailable`. §2.5.2: `created_at` ist `datetime \| None`, wie am Datensatz. §4.4/§7.3: das nie existierende `STORAGE_KEEP_EXIF_<CATEGORY>` durch das tatsächlich vorhandene `STORAGE_STRIP_EXIF` ersetzt (NFR-013 v1.4 §6.4). §9: **O-05 mit ja entschieden** (Standalone-Endpunkte nachgezogen), **O-07 entschieden** (Modul `diary`, Kategorie „Pflege & Planung", Stufe Einsteiger, `core: false`, `/tagebuch`) und in REQ-042 v1.1 §1.3 sowie REQ-021 v1.4 §3.3 eingetragen. |
| 1.0 | 2026-08-04 | Erstentwurf — Markierung, Zustandsmaschine, Ergebnis-Ablage am Eintrag, MCP-Vertrag für externe Agenten. |

---

## 0. Verhältnis zu bestehenden Spezifikationen

REQ-050 erfindet **kein** neues Tagebuch, **kein** neues Speicherkonzept, **keinen** neuen
Server-KI-Pfad. Es fügt einem bestehenden Datensatz einen Zustand und ein Ergebnisfeld hinzu und
macht beides zusammen mit den Bildern über eine bereits vorhandene Schnittstelle zugänglich.

| Dokument | Was es liefert | Was REQ-050 daraus nutzt |
|----------|----------------|--------------------------|
| **REQ-051** | Das Tagebuch als Ganzes: Aufbau des Eintrags, Erfassung, nachträgliche Bearbeitung, Inhaltsversion, Analyse-Archiv, **die Oberfläche (§6)** | Die Darstellung dieser Analyse und der Ort, an dem ein Eintrag markiert wird. Seit v1.5 steht sie dort, nicht mehr hier. |
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
| Ein Analyse-Ergebnis **am Eintrag** (das jüngste) | Die Archivierung selbst — sie ist mit v1.5 beschlossen (O-01) und in **REQ-051 §5** spezifiziert, nicht hier |
| Fünf MCP-Werkzeuge als Vertrag für externe Agenten | Das Agenten-Rezept selbst (Repository `kamerplanter-goose`) |
| Bilder als MCP-Bild-Content aus vorhandenen Renditions | Ausliefern von Originalbildern über MCP |
| **Tagebuch-Erfassung an der Pflanzeninstanz** (REQ-051 §6.1) | Serverseitiger Modellaufruf jeglicher Art |
| **Mandantenweite Tagebuch-Übersicht mit Analyse-Status** (REQ-051 §6.2) | Analyse-Übersicht über Mandantengrenzen hinweg |
| Einwilligungszweck + Löschklassifizierung | Automatische Übernahme in IPM-Behandlungen (§9, O-03) |

### 1.4 Die Tagebuch-Oberfläche — seit v1.5 in REQ-051

> **Verlagert.** Bis v1.4 spezifizierte dieser Abschnitt, warum die Tagebuch-Oberfläche Bestandteil
> von REQ-050 sein muss: Sie existierte nicht, und eine Anforderung, die nur einen Zustand am
> Datensatz einführt und die Oberfläche einer anderen überlässt, wäre nicht benutzbar gewesen.
> Zugleich hielt er fest, dass sie **fachlich nicht hierher gehört** und die Einordnung eine
> bewusste Zuschnitt-Entscheidung war.
>
> Mit **REQ-051 (Pflanzen-Tagebuch)** gibt es die Anforderung, in die sie gehört. Der Grund für
> die Ausnahme ist damit entfallen; die Oberfläche steht vollständig in REQ-051 §6 und wird hier
> nicht wiederholt. REQ-050 bleibt die Quelle für alles, was die **Analyse** ausmacht:
> Zustandsmaschine (§2.2), Gegenstand (§2.3), Ergebnisform (§2.4), Betriebsmodell (§3),
> MCP-Vertrag (§4), Datenmodell der Analysefelder (§5), Rechte (§6) und Datenschutz (§7).

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

Am Eintrag steht genau **ein** Ergebnis: das jüngste. Eine erneute Analyse verdrängt das vorherige
von diesem Platz — sie vernichtet es aber seit v1.5 **nicht** mehr. Jeder eintreffende Lauf wird
archiviert (REQ-051 §5, entscheidet O-01 mit „ja"); `entry.analysis` ist der schnelle Zugriff auf
das letzte Glied der Reihe, die vollständige Reihe liefert
`GET .../diary/{entry_key}/analyses`.

Ein Ergebnis trägt zusätzlich die **Inhaltsversion**, gegen die es gerechnet wurde
(`analyzed_content_version`, §5). Ändert sich der Eintrag danach, gilt das Ergebnis als veraltet —
die Regel steht in REQ-051 §4 und lässt die fünf Zustände dieses Dokuments unangetastet.

### 2.5 Weboberfläche — seit v1.5 in REQ-051

> **Verlagert nach REQ-051 §6.** Die Oberfläche des Tagebuchs ist keine Eigenschaft der Analyse,
> sondern des Tagebuchs; §1.4 hielt das schon in v1.0 fest. Sie steht vollständig in
> **REQ-051 (Pflanzen-Tagebuch)** und wird hier nicht wiederholt, damit keine Aussage zweimal
> existiert und auseinanderläuft.

| Bis REQ-050 v1.4 | Jetzt | Inhalt |
|------------------|-------|--------|
| §2.5 (Kopf) | REQ-051 §6 | Zwei Orte, verbindlich getrennt |
| §2.5.1 | REQ-051 §6.1 | Erfassung an der Pflanzeninstanz |
| §2.5.2 | REQ-051 §6.2 | Mandantenweite Übersicht, `GET /t/{slug}/diary`, `DiaryOverviewItem` |
| §2.5.3 | REQ-051 §6.4 | Darstellung des Analyse-Ergebnisses |
| §2.5.4 | REQ-051 §6.5 | Aktualisierung ohne Server-zu-Client-Kanal |
| AK-14…AK-17, AK-19, AK-20, AK-28…AK-31 | REQ-051 §12, **gleiche Nummern** | Oberflächen-Kriterien |

**Die Nummern der Akzeptanzkriterien wurden bewusst nicht neu vergeben.** Ein Testfall, der heute
„REQ-050 §2.5.2, AK-15" nennt, meint danach dieselbe Aussage; nur das führende Dokument wechselt.
Eine Umnummerierung hätte jeden dieser Verweise entwertet, ohne inhaltlich etwas zu verbessern.

**Was REQ-050 an der Oberfläche weiterhin bindet** — die Aussagen sind fachlich Analyse und
gelten unabhängig davon, wer sie darstellt:

- Für `requested` gibt es **keine** Fortschrittsanzeige und keine Laufzeitangabe. Es existiert
  keine Zusage über die Bearbeitungsdauer (§3), und jede Andeutung einer solchen wäre eine
  Behauptung über einen Agenten, den diese Instanz nicht kennt.
- Der **Vorbehalt** ist Pflichtbestandteil jedes Ergebnisses und immer sichtbar (§2.4).
- **Markieren ist eine Nutzerhandlung, immer** (§2.1). Keine Oberfläche darf eine
  Sammelmarkierung, eine Voreinstellung „alles analysieren" oder eine Regel anbieten, die
  Einträge nach Typ oder Stichwort markiert.
- Ob ein Nutzer markieren darf, wertet der **Server** aus und liefert es als
  `can_request_analysis` (§5). Es ist eine Anzeigehilfe, keine Autorisierung.

### 2.6 Nachforderung: wenn die vorhandenen Bilder nicht reichen

Der häufigste Grund für einen schwachen Befund ist kein schwaches Modell, sondern ein fehlendes
Bild. Wer „braune Flecken unten" fotografiert, fotografiert die Blattoberseite; die Milbe sitzt
unterseits. Der Agent sieht das — er ist die einzige Partei im Ablauf, die weiß, was ihm gefehlt
hat —, und bis hierher konnte er es niemandem sagen. Er konnte nur eine Konfidenz von 0.4 melden
und die Gärtnerin mit der Frage allein lassen, was sie damit anfangen soll.

**Eine Nachforderung ist die Bitte des Agenten um bestimmte Bilder**, gestellt als Teil des
Analyse-Ergebnisses. Sie benennt je Motiv, **was** aufzunehmen ist, **warum** es fehlt und
optional **wie** es aufzunehmen ist. Aus ihr entsteht ein Auftrag, den der Nutzer in seiner
Aufgabenwarteschlange vorfindet und der ihn bei der Erfassung Motiv für Motiv führt
(REQ-051 §6.6).

**Die Nachforderung markiert nicht neu.** Sie ist eine Bitte, kein Auftrag an das System. Der
Eintrag geht mit ihr nach `completed` (bzw. `failed`) wie jeder andere Lauf; er kehrt **nicht**
selbsttätig nach `requested` zurück. Erst wenn der Nutzer die Bilder gemacht und den Auftrag
abgeschickt hat, entsteht die neue Markierung — und das ist dann seine Handlung, nicht die des
Agenten. Damit bleibt §2.1 unangetastet, und die Konstruktion aus §9 (O-04) gilt hier
gleichermaßen: Ein Agent, der sich seine eigene Arbeit einreihen könnte, ginge an der
Einwilligungsprüfung nach §7.1 vorbei. Der Umweg über den Menschen ist hier kein Umstand,
sondern der Zweck — ohne ihn gäbe es die Bilder ohnehin nicht.

**Warum der Agent sie stellt und nicht der Nutzer.** Ein Knopf „erweiterte Analyse anfordern" am
Ergebnis wäre billiger zu bauen und wertlos: Er verlangte vom Nutzer zu wissen, was dem Modell
gefehlt hat. Genau diese Information ist der Inhalt einer Nachforderung, und sie entsteht
ausschließlich beim Analysieren.

**Höchstens fünf Motive.** Ein Tagebuch-Eintrag trägt höchstens fünf Fotos (REQ-013). Eine
Nachforderung, die mehr verlangt, ist in dem Rücklaufweg, den der Nutzer wählt, nicht erfüllbar —
sie erzeugte einen Auftrag, der die Erfüllung von vornherein ausschließt. Die Grenze steht
deshalb am Vertrag (§4.5) und nicht in der Oberfläche.

**Eine offene Nachforderung je Eintrag.** Trifft ein neuer Lauf am selben Eintrag ein, während
eine Nachforderung noch offen ist, wird die alte geschlossen (`superseded`) und ihr Auftrag mit
ihr. Zwei gleichzeitig offene Bitten um Bilder desselben Eintrags beschreiben nichts, was
tatsächlich geschieht: Der zweite Lauf hat dieselben Bilder gesehen wie der erste und eine
aktuellere Meinung dazu.

**Der Auftrag ist eine gewöhnliche Aufgabe.** Er wird als FreeStyle-Aufgabe nach REQ-006
angelegt — dem Mechanismus, den REQ-006 ausdrücklich für „maschinelle Produzenten (z. B.
Goose-Analyse-Pipelines)" vorsieht, um „abgeleitete Arbeit dem Nutzer sichtbar zu machen". Damit
erscheint die Nachforderung in Aufgabenliste, Dashboard und Kalender, ohne dass diese Anforderung
einen zweiten Aufgabenbegriff einführt. Was REQ-006 dafür ergänzen muss, steht dort (§ FreeStyle,
Unterabschnitt „Foto-Auftrag").

**Erzeuger ist der Server, nicht der Aufrufer.** Die Aufgabe entsteht im selben Schreibvorgang,
der das Ergebnis persistiert — nicht durch einen Aufruf des Agenten gegen den
Aufgaben-Endpunkt. Das ist keine Bequemlichkeit, sondern die einzige Variante, die mit zwei
bestehenden Festlegungen verträglich ist:

- Die **Herkunfts-Vertrauensregel** (REQ-006, Issue #1000) leitet `origin` aus dem
  authentifizierten Prinzipal ab und erzwingt für einen interaktiven Nutzer `origin: user`. Ein
  Agent, der unter dem persönlichen Schlüssel seines Betreibers läuft — der Normalfall der ersten
  Ausbaustufe (§3) —, könnte über den HTTP-Pfad also gar keine Pipeline-Aufgabe anlegen.
- Der **MCP-Werkzeugkatalog kennt kein schreibendes Aufgaben-Werkzeug** (REQ-033: zwölf
  Schreibwerkzeuge, keines legt eine Aufgabe an). Der Agent auf die REST-API auszuweichen zu
  lassen, bräche die Zusage aus §4, dass sich das Rezept allein aus diesem Abschnitt schreiben
  lässt.

Der Server legt die Aufgabe daher mit `origin: pipeline` und `source: "diary-analysis"` an, weil
er sie erzeugt hat — in Reaktion auf ein Ergebnis, nicht auf Geheiß des Aufrufers. Der Agent
merkt davon nichts; sein Vertrag aus §4.5 kennt nur das Nachforderungsfeld.

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
**innerhalb** `structuredContent`, neben `summary`. Die Beispiele in REQ-033 §2.6 zeigen dieses
Innere ohne die umgebende Hülle — dort ist der Zusammenhang seit v1.4 ausdrücklich vermerkt; die
Drahtform ist die hier gezeigte (REQ-033 §4.3b).

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
| `worker_id` fehlt oder ist leer | `validation.error` |
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
  "environment": [
    {
      "metric_type": "temperature_celsius",
      "value": 31.2,
      "unit": "\u00b0C",
      "source": "ha_auto",
      "measured_at": "2026-08-03T18:21:44Z",
      "sensor_key": "7710455",
      "origin": "location"
    },
    {
      "metric_type": "humidity_percent",
      "value": 28.0,
      "unit": "%",
      "source": "open-meteo",
      "measured_at": "2026-08-03T18:10:00Z",
      "sensor_key": null,
      "origin": "weather"
    }
  ],
  "environment_captured_at": "2026-08-03T18:22:11Z",
  "environment_status": "captured",
  "photo_refs": ["01HQ8X9V3J7P5K2N4M6T8R0S2W", "01HQ8X9V3J7P5K2N4M6T8R0S2X"],
  "created_at": "2026-08-03T18:22:11Z",
  "created_by": "4471023",
  "analysis_state": "in_progress",
  "analysis": null,
  "analysis_error": null,
  "plant": {
    "plant_key": "5512099",
    "plant_name": "Tomate Beet 2 #05",
    "instance_id": "HOCHBEETA_TOM_05",
    "species_key": "solanum_lycopersicum",
    "species_name": "Solanum lycopersicum",
    "cultivar_key": "san_marzano",
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

**`environment` ist der Umgebungs-Schnappschuss** (REQ-013 §2.3a): die Sensorwerte, die die
Pflanze im Moment der Anlage abdeckten, serverseitig aufgelöst. Genau dafür gibt es dieses
Werkzeug — „warum bräunen die unteren Blätter" ist bei 31 °C und 28 % rF eine andere Frage
als bei 19 °C und 65 %, und die Antwort steht sonst nirgends im Payload.

Es ist ein **eigener Schlüssel neben `measurements` und bleibt einer**. `measurements` ist,
was ein Mensch getippt hat; `environment` ist, was eine Maschine gemeldet hat. Jeder Eintrag
trägt sein eigenes `source` / `measured_at` / `origin`, damit ein Rezept eine Sonde am
Standort der Pflanze gegen einen geländeweiten Wetterwert abwägen kann. Wer die beiden
zusammenlegt, wirft genau das weg.

`origin` und `source` beantworten verschiedene Fragen: `origin` (`location` | `site` |
`weather`) sagt, wie nah an der Pflanze gemessen wurde, `source` sagt, wie der Wert entstand
(REQ-005 §2 — `ha_auto`, `mqtt_auto`, `manual`, …) bzw. welcher Wetterdienst ihn lieferte.

`measured_at` ist der **Messzeitpunkt** und regelmäßig älter als `created_at`. Werte jenseits
der serverseitigen Aktualitätsgrenze werden gar nicht erst erfasst — was hier steht, wurde
also zeitnah zur Beobachtung gemessen.

`environment_status` ist vor jedem Schluss aus einer leeren Liste zu lesen: `no_source` heißt
„nichts misst diese Pflanze", `unavailable` heißt „die Messung kam nicht durch", `opted_out`
heißt „die Autorin wollte es nicht", `not_attempted` heißt „der Eintrag ist älter als das
Feature". Nur das erste ist eine Aussage über den Garten.

Neben `cultivar_name` steht der **`cultivar_key`**, weil `get_cultivar` einen Schlüssel nimmt
und kein Label: mit dem Namen allein hielt ein Agent eine Bezeichnung in der Hand, mit der er
nichts nachschlagen konnte. Dieselbe Begründung wie beim Paar `species_key`/`species_name`.

`created_by` ist der **blanke `user_key`** ohne Collection-Präfix — genau der Wert, der am
Datensatz steht. Ein `user/`-Präfix zu ergänzen hieße, im Vertrag eine Dokument-ID zu
versprechen, die nirgends gespeichert ist. Nach einer Nutzerlöschung steht dort `_anonymized`
(§7.4, AK-23).

`analysis` trägt das **persistierte Ergebnis** in derselben Form wie in §4.5 (also samt
`disclaimer` und `analyzed_at`), `analysis_error` den Fehlertext einer gescheiterten Analyse;
liegt keines von beidem vor, stehen sie auf `null`. Ohne diese beiden Felder käme ein Agent, der
einen bereits analysierten Eintrag erneut zugewiesen bekommt (AK-21), über **keines** der fünf
Werkzeuge an den Vorbefund — er sähe `analysis_state: "completed"` und analysierte blind neu,
ohne zu wissen, was beim letzten Mal herauskam.

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
2. **Datenschutz.** Renditions tragen keine EXIF-Daten — auch dann nicht, wenn die Instanz
   `STORAGE_STRIP_EXIF=false` gesetzt und den Strip beim Upload damit abgeschaltet hat; jenes
   Setting betrifft nur die Originaldatei. NFR-013 §8.2 hält das seit v1.3 ausdrücklich als
   Anforderung fest, statt es als Nebenwirkung der Neukodierung anzunehmen. Genau darauf stützt
   sich die Zulässigkeit der Auslieferung. (Die in NFR-013 §6.4 beschriebene **kategoriescharfe**
   Variante `STORAGE_KEEP_EXIF_<CATEGORY>` ist spezifiziert, aber nicht implementiert; es gibt
   ausschließlich das globale `STORAGE_STRIP_EXIF`. Für diese Anforderung ändert das nichts —
   die Zusage hängt an der Rendition, nicht an der Konfiguration.)
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
blockieren würde.

**`pending[].status` kennt zwei Werte**, und die Unterscheidung ist verhaltensrelevant:

| `status` | Bedeutung | Was ein Rezept damit tut |
|----------|-----------|--------------------------|
| `thumbnail_pending` | Die Rendition existiert **noch** nicht; die Erzeugung ist angestoßen. | Später erneut abrufen. |
| `unavailable` | Für dieses `photo_ref` wird **nie** eine Rendition erscheinen: Der Attachment-Datensatz fehlt, oder der Mime-Typ erzeugt keine Rendition. | Nicht erneut abrufen; das Foto ohne Bild bewerten. |

`unavailable` ist kein Sonderfall, den man auch als `thumbnail_pending` melden könnte: Diese
Meldung wäre eine Lüge, die den Agenten in eine endlose Wiederholung schickt — er wartet auf eine
Erzeugung, die niemand mehr anstoßen kann.

Die Prüfregel bleibt davon **unberührt**: Ein Rezept, das Vollständigkeit braucht, prüft `pending`
auf leer — unabhängig davon, welcher der beiden Werte darin steht — und darf sich nicht darauf
verlassen, dass ein erfolgreicher Aufruf alle Fotos enthält.

**Eintrag ohne Fotos:** Ein Eintrag mit leerem `photo_refs` ist **kein** Fehler. Die Antwort ist
erfolgreich mit `photos: []`, `pending: []` und nur dem `summary`-Textblock im `content`-Array.
Ein Rezept muss diesen Fall behandeln, weil vier der sechs Eintragstypen üblicherweise ohne Foto
erfasst werden.

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
| `photo_request` | `list \| None`, max. **5** Motive | Nachforderung (§2.6). Je Motiv: `what` (max. 200, Pflicht), `why` (max. 500, Pflicht), `how` (max. 500, optional) |
| `dry_run`, `idempotency_key` | | Standardvertrag für Schreibwerkzeuge |

Die Längengrenzen stehen hier bewusst **doppelt** (auch in §5) — ein Rezept, das nur §4 liest,
muss sie kennen, sonst läuft es blind in `validation.error`.

**Zu `photo_request`.** Das Feld ist bei **beiden** Ausgängen zulässig: ein `failed`-Lauf, der an
unbrauchbaren Bildern gescheitert ist, hat dieselbe Auskunft zu geben wie ein `completed`-Lauf mit
schwacher Konfidenz. Es ist in keinem der beiden Fälle Pflicht — ein Agent, der nichts vermisst,
lässt es weg, und ein leeres Feld ist keine Nachforderung.

Die Obergrenze von fünf Motiven ist **keine** Höflichkeitsempfehlung, sondern die Zahl der Fotos,
die ein Eintrag überhaupt tragen kann (REQ-013). Eine sechste Bitte beschriebe einen Auftrag, den
der Rücklaufweg nicht erfüllen kann; sie wird mit `validation.error` abgewiesen, nicht stillschweigend
gekürzt. `why` ist Pflicht, weil eine Bitte ohne Grund den Nutzer wieder in genau die Lage bringt,
die §2.6 auflöst: Er weiß, dass etwas fehlt, aber nicht, wozu.

Was der Server daraus macht, sieht der Agent nicht: Er legt den Foto-Auftrag als FreeStyle-Aufgabe
an (REQ-006 § FreeStyle, „Foto-Auftrag") und schließt eine noch offene Nachforderung desselben
Eintrags als `superseded`. Der Vertrag hier kennt nur das Feld — bewusst, damit ein Rezept sich
allein aus §4 schreiben lässt.

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
    # REQ-051 §4.4 — Inhaltsversion, gegen die dieser Lauf gerechnet hat.
    # Serverseitig aus der beim Beanspruchen geltenden Version gesetzt; ein vom
    # Agenten geliefertes Feld wird ignoriert. Fehlt es an einem Bestandsdokument,
    # wird es als 1 gelesen.
    analyzed_content_version: int = 1
```

**Am Eintrag steht ein eingebettetes Teildokument, im Archiv die Reihe.** `entry.analysis` bleibt
ein eingebettetes Teildokument — der schnelle Zugriff auf das jüngste Ergebnis, ohne Nachschlag.
Die vollständige Reihe abgeschlossener Läufe liegt seit v1.5 in der eigenen Collection
`plant_diary_analyses` (REQ-051 §5, entscheidet O-01). Eine **Kante** im Named Graph gibt es
weiterhin nicht: Die einzige Abfrage lautet „alle Läufe zu Eintrag X" und wird von einem
persistenten Index beantwortet.

Der Eintrag trägt zusätzlich `content_version` und `analysis_claimed_content_version`; beide
gehören zu REQ-051 §8 und sind hier nur genannt, weil `claim_diary_analysis` die zweite setzt.

**Die Tabelle oben beschreibt den Datensatz, nicht die Antwort.** Zwei Unterschiede sind
verhaltensrelevant und gelten für **jeden** Lesepfad — den Einzelabruf (`DiaryEntryResponse`, beide
Präfixe) ebenso wie die Übersichtszeile (`DiaryOverviewItem`, REQ-051 §9.1):

- **`analysis_state` wird als *angezeigter* Zustand geliefert.** Ist das Agenten-Lease abgelaufen,
  antwortet die API `requested`, obwohl `in_progress` gespeichert ist — der Eintrag liegt wieder im
  Arbeitsvorrat (§2.2, AK-06). Der gespeicherte Wert wird nicht zusätzlich veröffentlicht; er bleibt
  aus den Lease-Feldern ableitbar, die der Einzelabruf unverändert mitführt. Ein `requested` mit
  gesetztem `analysis_claimed_by` und einem `analysis_lease_expires_at` in der Vergangenheit ist
  genau der Fall des abgestürzten Agenten. Lesen schreibt nichts; zurückgesetzt wird beim nächsten
  Schreibzugriff.
- **`can_request_analysis: bool` kommt am Datensatz nicht vor, in jeder Antwort aber schon.** Es ist
  die serverseitige Auswertung von §7.2/§7.1/§7.5 für den Nutzer *dieser* Anfrage (AK-18a) und steht
  sowohl an `DiaryEntryResponse` als auch an `DiaryOverviewItem` — nicht nur an der Übersichtszeile.
  Es ist eine Anzeigehilfe, keine Autorisierung.

**Index:** Für `list_pending_diary_analyses` (§4.1) **und** für die Zustandsfilter der
mandantenweiten Übersicht (REQ-051 §6.2) ist ein persistenter Index über
`(tenant_key, analysis_state, analysis_requested_at)` anzulegen, sonst wird beides zum
Sammelscan über alle Tagebuch-Einträge des Mandanten.

---

## 6. Berechtigungen

Vokabular gemäß REQ-049 §3.1: Beobachter → Gärtner → Leitung.

| Handlung | Beobachter | Gärtner | Leitung | MCP-Recht |
|----------|-----------|---------|---------|-----------|
| Analyse-Zustand und Ergebnis lesen | ✓ | ✓ | ✓ | `mcp.read` |
| Tagebuch-Übersicht öffnen (REQ-051 §6.2) | ✓ | ✓ | ✓ | `mcp.read` |
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
> mitgezogene Aufgabe — sie betrifft den gesamten Werkzeugkatalog, nicht nur diese fünf.

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
  nicht, wenn die Instanz den Upload-Strip über `STORAGE_STRIP_EXIF=false` abgeschaltet hat. Das
  ist heute das einzige EXIF-Setting; die kategoriescharfe Variante aus NFR-013 §6.4 ist
  spezifiziert, aber nicht implementiert (NFR-013 v1.4 §6.4).
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
| **AK-09** | Fehlt eine Rendition, liefert der Abruf für dieses Foto `thumbnail_pending`, stößt die Erzeugung an und bleibt für die übrigen Fotos erfolgreich. Für ein `photo_ref`, zu dem **nie** eine Rendition entstehen wird (Attachment-Datensatz fehlt oder Mime-Typ erzeugt keine Rendition), lautet der Status `unavailable` und es wird **keine** Erzeugung angestoßen (§4.4). |
| **AK-10** | `submit_diary_analysis` mit gültigem Lease persistiert das Ergebnis am Eintrag und setzt `completed` bzw. `failed`; ohne gültigen Lease scheitert es mit `conflict.not_claimed` oder `conflict.lease_expired`. |
| **AK-11** | Der Vorbehalt wird serverseitig gesetzt und ist auch dann vorhanden, wenn der Agent kein entsprechendes Feld liefert. |
| **AK-12** | Ein Eintrag aus einem fremden Mandanten liefert `not_found`, nie `permission.denied` (keine Preisgabe fremder Mandanten). |
| **AK-13** | Ohne erteilte Einwilligung `diary_ai_analysis` lässt sich kein Eintrag markieren; ein Widerruf verhindert neue Markierungen und lässt vorhandene Ergebnisse unberührt. |
| **AK-14** | → **verlagert nach REQ-051 §12** (gleiche Nummer): Tagebuch-Tab an der Pflanzeninstanz: anlegen, bearbeiten, löschen, Fotos, markieren. |
| **AK-15** | → **verlagert nach REQ-051 §12** (gleiche Nummer): Mandantenweite Übersicht über die Einträge aller Pflanzen. |
| **AK-16** | → **verlagert nach REQ-051 §12** (gleiche Nummer): Alle fünf Analyse-Zustände sichtbar unterschieden. |
| **AK-17** | → **verlagert nach REQ-051 §12** (gleiche Nummer): Filter und Freitextsuche der Übersicht. |
| **AK-18** | `GET /t/{slug}/diary` liefert ausschließlich Einträge des angefragten Mandanten als `DiaryOverviewResponse`, seitenweise mit `total`/`limit`/`offset`. Jede Zeile trägt `analysis_state` und `analysis_summary`, **nie** `findings` oder `recommended_actions` — das vollständige Ergebnis liefert nur der Einzelabruf. |
| **AK-18a** | `can_request_analysis` je Zeile spiegelt die serverseitige Auswertung von Rolle, Autorschaft, Einwilligung und Betriebsmodus. Ein Markierversuch auf einer Zeile mit `false` wird serverseitig abgelehnt — das Feld ist Anzeigehilfe, nicht Autorisierung. |
| **AK-19** | → **verlagert nach REQ-051 §12** (gleiche Nummer): Nur eigene Einträge markierbar; fremde Zeilen ohne Schalter. |
| **AK-20** | → **verlagert nach REQ-051 §12** (gleiche Nummer): Vorbehalt immer sichtbar, nicht aufklappbar versteckt. |
| **AK-21** | Eine erneute Analyse eines `completed`- oder `failed`-Eintrags ist möglich; sie setzt den Zustand auf `requested` und ersetzt beim Abschluss das Ergebnis **am Eintrag** vollständig. Das vorherige geht dabei **nicht** verloren: Jeder Lauf ist archiviert (REQ-051 §5). |
| **AK-22** | `submit_diary_analysis` weist Eingaben zurück, die eine Längengrenze aus §4.5 überschreiten, `confidence` außerhalb 0.0–1.0 tragen, bei `completed` kein `summary` oder bei `failed` kein `error` mitführen (jeweils `validation.error`). |
| **AK-23** | Löschen des Eintrags löscht das Analyse-Ergebnis; Löschen der Pflanze löscht beides. Bei Nutzerlöschung bleibt der Eintrag erhalten und `created_by`, `analysis_requested_by` und `analysis_claimed_by` sind auf `_anonymized` gesetzt. |
| **AK-24** | Die Datenauskunft nach Art. 15 enthält Tagebuch-Einträge samt Analyse-Ergebnis. |
| **AK-25** | Im Light-Modus ist die Markierung ohne Einwilligungsprüfung möglich und die Einschränkung „nur eigene Einträge" greift nicht (§7.5). |
| **AK-26** | Bestehende Tagebuch-Einträge ohne Analyse-Felder bleiben ohne Migration lesbar und schreibbar; `analysis_state` wird als `none` interpretiert. |
| **AK-27** | Ohne laufenden externen Agenten funktioniert Kamerplanter unverändert; markierte Einträge verbleiben in `requested` und die Oberfläche benennt das als „wartet auf Analyse" — ohne Fortschrittsanzeige. |
| **AK-28** | → **verlagert nach REQ-051 §12** (gleiche Nummer): Oberflächentexte in DE und EN, DE als Vorgabe. |
| **AK-29** | → **verlagert nach REQ-051 §12** (gleiche Nummer): Auffrischen statt Push; keine Fortschrittsanzeige. |
| **AK-30** | → **verlagert nach REQ-051 §12** (gleiche Nummer): Konfidenz als Zahl **und** sprachlich eingeordnet. |
| **AK-31** | → **verlagert nach REQ-051 §12** (gleiche Nummer): Modul in REQ-042 registriert, in REQ-021 eingeordnet. |

---

## 9. Offene Punkte

| Nr. | Frage | Entscheider | Status |
|-----|-------|-------------|--------|
| O-01 | Soll eine **Historie** mehrerer Analysen je Eintrag geführt werden statt nur der jüngsten? Erst dann lohnt eine eigene Collection. | Produkt | **entschieden (v1.5): ja** |
| O-02 | Darf in einem Gemeinschaftsgarten ein Gärtner **fremde** Einträge zur Analyse markieren? v1.0 verneint das (§7.2); die Lockerung ist eine Produkt- und Datenschutzentscheidung. | Produkt + Datenschutz | offen |
| O-03 | Soll aus einem Befund direkt eine **IPM-Behandlung** (REQ-010) oder eine Diagnose-Sitzung (REQ-036) vorgeschlagen werden können? | Produkt | offen |
| O-04 | Soll `add_plant_diary_entry` (REQ-033 §2.2, bislang nicht umgesetzt) zusammen mit dieser Anforderung realisiert werden, damit ein Agent auch Einträge **anlegen** kann? | Produkt | **entschieden (v1.3): ja, ohne `photo_refs`** |
| O-05 | Sollen die in REQ-013 §4.7 spezifizierten, aber nie implementierten **Standalone**-Tagebuch-Endpunkte (`/plant-instances/{key}/diary`) mit REQ-050 nachgezogen werden? Ohne sie hat eine Pflanze ohne Pflanzdurchlauf kein Tagebuch — die Erfassung nach REQ-051 §6.1 wäre dort nicht bedienbar. | Produkt | **entschieden (v1.1): ja** |
| O-06 | Soll die Obergrenze der Bild-Nutzlast je Mandant konfigurierbar sein oder global bleiben? | DevOps | offen |
| O-07 | Unter welchem Modulschlüssel wird die Tagebuch-Übersicht (REQ-051 §6.2) in REQ-042 registriert, und welcher Erfahrungsstufe wird sie in der Navigations-Zuordnung von REQ-021 §3.3 zugewiesen? | Produkt | **entschieden (v1.1)** |

**Zu O-01 — entschieden: ja.** Die Historie kommt, in einer eigenen Collection
`plant_diary_analyses`, und ist in **REQ-051 §5** spezifiziert. Der Auslöser war nicht die Frage
selbst, sondern eine Nachbaranforderung: Sobald ein Eintrag nachträglich bearbeitbar ist
(REQ-051 §3), ist „erneut analysieren" der Normalfall und nicht mehr die Ausnahme — und damit
wird das Überschreiben des vorherigen Befundes zum regelmäßigen Datenverlust statt zum seltenen.
§5 dieses Dokuments hatte die eigene Collection genau für diesen Fall in Aussicht gestellt.

Zwei Festlegungen aus REQ-051 §5 wirken auf den MCP-Vertrag zurück, ohne ihn zu ändern:
`submit_diary_analysis` erzeugt den Archiveintrag **beim Eintreffen** des Ergebnisses — für
`completed` **und** `failed`, in derselben Transaktion, die den Zustand setzt. Der Agent merkt
davon nichts; sein Vertrag aus §4.5 ist unverändert.

**Zu O-05 — entschieden: ja.** Die Standalone-Endpunkte werden mit REQ-050 nachgezogen, unter

```
/api/v1/t/{tenant_slug}/plant-instances/{key}/diary
```

— dasselbe Muster, unter dem die Foto-Galerie aus REQ-034 an derselben Pflanzeninstanz hängt
(`/plant-instances/{key}/photos`). Begründung: Ohne sie hat eine Pflanze **ohne** Pflanzdurchlauf
kein Tagebuch, und die Erfassung nach REQ-051 §6.1 wäre genau dort unbedienbar, wo sie am häufigsten
gebraucht wird — die Einzelpflanze ist der Normalfall, nicht der Sonderfall. Die
Run-Endpunkte (`/planting-runs/{key}/diary`) bleiben **unverändert**; beide Wege bedienen denselben
Dienst und dieselben Dokumente.

**Zu O-04 — entschieden: ja, ohne `photo_refs`.** Das Werkzeug wird nachgezogen, damit ein Agent
nicht nur analysieren, sondern auch **dokumentieren** kann. Es hängt an demselben Dienst und
demselben Endpunkt-Muster wie die Erfassung in der Oberfläche
(`POST /api/v1/t/{tenant_slug}/plant-instances/{key}/diary`, O-05) und legt keinen zweiten
Schreibpfad an.

Zwei Grenzen sind Teil der Entscheidung:

- **Keine Foto-Referenzen.** SEC-003 lässt ein `photo_refs`-Element nur zu, wenn der Erfasser das
  Attachment selbst hochgeladen hat oder die Rolle Leitung hält. Ein Service-Account lädt nie
  etwas hoch, und MCP hat ohnehin keinen Upload-Weg — das Feld wäre eine Dauerablehnung mit dem
  Anschein einer Fähigkeit. Fotos erreichen einen Eintrag über die Oberfläche.
- **Kein Markieren.** Der geschriebene Eintrag steht auf `analysis_state: none`. Ein Werkzeug, das
  seinen eigenen Eintrag zur Analyse einreihen könnte, erzeugte sich seine eigene Arbeit und ginge
  an der Einwilligungsprüfung nach §7.1 vorbei; automatische Markierung ist nach §1.3 ausdrücklich
  außerhalb des Umfangs. Markieren bleibt eine Nutzerhandlung.

Damit ist `add_plant_diary_entry` das erste Tagebuch-Werkzeug **außerhalb** des Analyse-Vertrags
aus §4 — es gehört zu REQ-033 §2.2 und ist für die Recipe der Analyse nicht erforderlich.

**Zu O-07 — entschieden.** REQ-042 §1.3 verlangt ausdrücklich, dass jede neue Anforderung ihr Modul
registriert; REQ-021 §3.3 führt die verbindliche Navigations-Zuordnung. Für ein Tagebuch existierte
in **beiden** kein Eintrag — die Übersicht wäre sonst die einzige Seite ohne Sichtbarkeitssteuerung
und ohne Erfahrungsstufen-Einordnung gewesen. Festgelegt ist (AK-31):

| Feld | Wert |
|------|------|
| Modulschlüssel | `diary` |
| Kategorie | Pflege & Planung (`care_planning`) |
| Erfahrungsstufe (Default-Level) | Einsteiger (`beginner`) |
| `core` | `false` |
| Navigationspfad | `/tagebuch` |

**Warum `core: false`:** AK-31 verlangt Abschaltbarkeit. Ein Kern-Modul ist nach REQ-042 §1.1
gerade das, was **nicht** ausblendbar ist — ein Tagebuch als Kern-Modul wäre die eine Seite, die
ein Nutzer, der kein Tagebuch führt, nicht loswird.

**Warum `beginner`:** Ein Tagebuch ist die niedrigschwelligste Funktion des Systems — eine Notiz
und ein Foto, ohne Fachbegriff und ohne Vorbedingung. Eine Einordnung als `intermediate` würde sie
ausgerechnet vor der Zielgruppe verstecken, für die sie geschrieben ist.

**Zur Einordnung:** Mit v1.1 sind die beiden Punkte entschieden, die der Umsetzung im Weg standen
(O-05 blockierend, O-07 vor dem Bau der Übersichtsseite zu klären). O-01 bis O-04 und O-06 lassen
sich nach der Umsetzung entscheiden, ohne bereits Gebautes zu entwerten. Die zuvor hier geführte
Frage nach der Tagebuch-Oberfläche ist entfallen — sie ist mit REQ-051 §6 beantwortet und
Bestandteil jener Anforderung.

---

**Dokumenten-Ende**
**Version:** 1.5
**Status:** Entwurf
