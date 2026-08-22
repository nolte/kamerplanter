# Spezifikation: REQ-051 - Pflanzen-Tagebuch

```yaml
ID: REQ-051
Titel: Pflanzen-Tagebuch (Erfassung, nachträgliche Bearbeitung, Übersicht — verbindliche Grundlage für Web- und Mobile-Client)
Kategorie: Dokumentation & Beobachtung
Fokus: Beides (Zierpflanze & Nutzpflanze)
Technologie: Python 3.14+, FastAPI, ArangoDB, React 19, TypeScript 6, Flutter (geplant)
Status: Entwurf
Priorität: Hoch
Version: 1.2 (eigene Stellschraube für den Schnappschuss-Verzug)
Datum: 2026-08-16
Tags: [diary, editing, versioning, analysis-archive, mobile, client-neutral]
Abhängigkeit: REQ-052 v1.0 (Bilderfassung — Profil `gallery`), REQ-013 v2.7 (Pflanzdurchlauf — `PlantDiaryEntry`, Endpunkte, Umgebungs-Schnappschuss §2.3a), REQ-050 v1.5 (KI-Analyse — Zustandsmaschine, MCP-Vertrag, Einwilligung), REQ-034 v1.2 (Foto-Galerie — Zuordnung, Titelbild, Metadaten), NFR-013 v1.4 (Object Storage — Attachments, Renditions), REQ-005 (Sensorik-Fallback-Kette, Provenienz), REQ-024 v1.7 (Mandant), REQ-049 v1.4 (Rollenvokabular), REQ-025 v1.6 (DSGVO), REQ-042 v1.1 (Modul `diary`), REQ-021 v1.4 (Navigations-Zuordnung), REQ-027 (Light-Modus)
Wird benötigt von: REQ-050 (Oberfläche der Analyse-Anzeige)
```

## Versionshistorie

| Version | Datum | Änderung |
|---------|-------|----------|
| 1.2 | 2026-08-22 | **`DIARY_SNAPSHOT_MAX_LAG_MINUTES` (§3.5, AK-43).** §3.5 verwendete `DIARY_ENVIRONMENT_MAX_AGE_MINUTES` mit — dieselbe Stellschraube, die REQ-013 §2.3a.5 dafür nutzt, wie alt ein **Sensorwert bei der Erfassung** sein darf. Beide stehen auf 60 Minuten, messen aber Verschiedenes: die eine das Alter der Messung, die andere den Abstand zwischen `environment_captured_at` und `created_at`. Mit einer Schraube für beides hatte jede Bewegung eine unbeabsichtigte zweite Wirkung — die Sensorfrische zu verschärfen hätte fast jeden nachgetragenen Schnappschuss markiert, sie zu lockern den Hinweis stillgelegt. Jetzt getrennt, mit einer Tabelle in §3.5, die benennt, was welche misst und woraus sie folgt. (#1216) |
| 1.1 | 2026-08-22 | **§6.6 Nachforderung erfüllen.** Der Ablauf, mit dem ein Nutzer die von einem Analyse-Lauf nachgeforderten Bilder macht (REQ-050 §2.6). Einstieg ist die **Aufgabe**, nicht der Eintrag — die Bitte wird beantwortet, wenn der Nutzer bei der Pflanze steht, nicht wenn er das Ergebnis liest. Führt Motiv für Motiv, zeigt `why` immer sichtbar, erlaubt **Überspringen** (ein Ablauf, der auf Vollständigkeit besteht, wird abgebrochen und liefert gar nichts) und prüft die Fünf-Foto-Grenze **vor** der ersten Aufnahme statt nach der letzten. Die Erfassung selbst routet über **REQ-052 §2** (Profil `gallery`) — kein zweiter Erfassungsweg. Abgeschickt wird über denselben „Analysieren"-Schalter aus §6.1, damit kein Pfad an `can_request_analysis` und REQ-050 §7.1 vorbeiführt. (#1237) |
| 1.0 | 2026-08-16 | Erstfassung. Bündelt die bislang auf REQ-013 (Datensatz, Endpunkte) und REQ-050 (Oberfläche) verteilte Tagebuch-Funktion zu einer eigenen Anforderung und ergänzt drei neue Fähigkeiten: **nachträgliche Bearbeitung** eines Eintrags samt Fotos und Messwerten (§3), **Aktualitätskennzeichnung** eines Analyse-Ergebnisses nach einer Bearbeitung (§4) und ein **Analyse-Archiv** (§5, entscheidet REQ-050 O-01 mit „ja"). Die Oberflächen-Abschnitte §2.5.1–§2.5.4 aus REQ-050 v1.4 wandern hierher (§6) — samt der Akzeptanzkriterien AK-14 bis AK-17, AK-19, AK-20 und AK-28 bis AK-31, die ihre Nummern behalten, damit bestehende Verweise (u. a. `spec/e2e-testcases/TC-REQ-050.md`) auflösbar bleiben. Neu ist außerdem §7: die Anforderung ist client-neutral formuliert und benennt, was ein mobiler Client zusätzlich braucht. **§2.4** führt die sonst über §3, §5, §9 und §11 verteilten Aussagen zur Mandantentrennung an einem Ort zusammen und beschreibt das Verhalten im geteilten Mandanten über die zweite Achse Autorschaft; dabei ist festgehalten, dass die Standort-Zuweisung nach REQ-049 §3.5 **keine** Schreibgrenze ist (§2.4.5), und eine bislang unausgesprochene Frage als O-58 aufgenommen worden: die mandantenweit offene Analyse-Historie. |

---

## 0. Verhältnis zu bestehenden Spezifikationen

Diese Anforderung erfindet **kein** neues Tagebuch. Sie beschreibt das vorhandene vollständig an
einem Ort und erweitert es um drei Fähigkeiten, die heute fehlen.

| Dokument | Was es liefert | Verhältnis zu REQ-051 |
|----------|----------------|----------------------|
| **REQ-013** | `PlantDiaryEntry` als Knoten, die Tagebuch-Endpunkte in beiden Präfixen, der Umgebungs-Schnappschuss §2.3a | **Bleibt die Quelle für den Datensatz und die Graph-Einbettung.** REQ-051 ergänzt additive Felder (§8) und einen Endpunkt (§9) und beschreibt, was mit dem Datensatz *fachlich* geschieht. |
| **REQ-050** | Analyse-Zustandsmaschine, Lease, MCP-Vertrag, Einwilligungszweck `diary_ai_analysis` | **Bleibt die Quelle für die Analyse.** REQ-051 übernimmt von dort die Oberfläche (§6) und ergänzt Aktualität (§4) und Archiv (§5). Die fünf Zustände aus REQ-050 §2.2 werden **nicht** verändert. |
| **REQ-052** | Erfassungsbaustein: die drei Erfassungswege, Normalisierungsprofile, EXIF-Strip | Tagebuchfotos werden damit erfasst, Profil `gallery` (§3.3, §6.1). |
| **REQ-034** | Galerie-Muster am Pflanzeninstanz-Tab, Foto-Metadaten (`caption`, `taken_on`) | Das Tab-Muster wird wiederverwendet, nicht nachgebaut. Die Erfassungswege lagen bis REQ-034 v1.2 hier und stehen jetzt in REQ-052. |
| **NFR-013** | `attachments`-Collection, Renditions 128/512/1280 px WebP, EXIF-Strip | Bildquelle. Tagebuchfotos sind `category = diary`; REQ-051 führt **keine** neue Storage-Kategorie ein. |
| **REQ-005** | Fallback-Kette und Provenienz je Messwert | Begründet, warum der Umgebungs-Schnappschuss nicht handisch editierbar ist (§3.5). |
| **REQ-042 / REQ-021** | Modul `diary` (`core: false`, `beginner`), Navigationspfad `/tagebuch` | Unverändert; nur der Verweis wandert von REQ-050 §2.5.2 auf REQ-051 §6.2. |
| **REQ-025** | Löschklassen, Auskunft, Erasure-Phasen | REQ-051 erweitert die Anonymisierung auf die neue Archiv-Collection (§11). |

### 0.1 Was aus REQ-050 hierher wandert

REQ-050 §1.4 hielt bereits fest, dass die Tagebuch-Oberfläche fachlich zu REQ-013 gehört und nur
aus Zuschnitt-Gründen dort mitspezifiziert wurde — sie war der Anlass, aus dem sie entstand. Mit
einer eigenen Tagebuch-Anforderung entfällt dieser Grund. Damit keine Aussage zweimal existiert
und auseinanderläuft, wandert sie vollständig hierher; REQ-050 behält an ihrer Stelle einen
Verweis.

| REQ-050 v1.4 | REQ-051 | Inhalt |
|--------------|---------|--------|
| §1.4 | §1.2 | Warum die Oberfläche Bestandteil einer Anforderung sein muss |
| §2.5 (Kopf) | §6 | Zwei Orte, verbindlich getrennt |
| §2.5.1 | §6.1 | Erfassung an der Pflanzeninstanz |
| §2.5.2 | §6.2 | Mandantenweite Übersicht, Endpunkt und Antwortschema |
| §2.5.3 | §6.4 | Darstellung des Analyse-Ergebnisses |
| §2.5.4 | §6.5 | Aktualisierung ohne Server-zu-Client-Kanal |
| AK-14…AK-17, AK-19, AK-20, AK-28…AK-31 | §12, gleiche Nummern | Oberflächen-Akzeptanzkriterien |

**Die Nummern der übernommenen Akzeptanzkriterien bleiben erhalten.** Ein Testfall, der heute
„REQ-050 AK-14" nennt, meint danach dieselbe Aussage; nur das Dokument, das sie führt, wechselt.
Neu vergebene Kriterien dieser Anforderung beginnen deshalb bei **AK-40**, damit keine Nummer
doppelt belegt ist.

---

## 1. Business Case

### 1.1 User Stories

> **Als Zimmerpflanzen-Besitzerin** möchte ich zu einer Pflanze schnell eine Notiz und ein Foto
> festhalten, ohne vorher etwas einrichten oder einen Fachbegriff kennen zu müssen — damit ich
> beim nächsten Mal weiß, wie es ihr vor drei Wochen ging.

> **Als Gärtner** möchte ich einen Eintrag später ergänzen können — ein zweites Foto, das ich am
> Abend nachschiebe, eine Höhe, die ich beim Schreiben nicht zur Hand hatte, ein Satz, der beim
> ersten Tippen unpräzise war —, ohne dafür einen zweiten Eintrag anlegen zu müssen, der dieselbe
> Beobachtung ein zweites Mal erzählt.

> **Als Gärtner** möchte ich, dass eine bereits vorhandene KI-Analyse **sichtbar als veraltet
> gekennzeichnet** wird, sobald ich den Eintrag nachträglich ändere — damit ich nicht auf eine
> Einschätzung vertraue, die zu einem Foto gehört, das ich inzwischen ausgetauscht habe.

> **Als Gärtnerin** möchte ich frühere Analyse-Ergebnisse desselben Eintrags nachlesen können,
> statt sie beim erneuten Analysieren zu verlieren — der Vergleich „was hat das Modell vor dem
> Umtopfen gesagt, was danach" ist genau die Information, wegen der ich zweimal analysiere.

> **Als Nutzer der Mobil-App** möchte ich im Gewächshaus mit dem Telefon fotografieren und
> notieren und am Schreibtisch am Browser weiterarbeiten — mit demselben Datenstand und ohne dass
> eine der beiden Oberflächen etwas kann, was die andere nicht kann.

### 1.2 Warum das Tagebuch eine eigene Anforderung braucht

Die Tagebuch-Funktion war bis hierher auf zwei Dokumente verteilt, von denen keines sie als
Ganzes beschreibt: REQ-013 führt den **Datensatz** und die Endpunkte als Nebenaspekt der
Pflanzdurchlauf-Verwaltung; REQ-050 führt die **Oberfläche** als Nebenaspekt der KI-Analyse.
Damit gibt es keinen Ort, an dem steht, was ein Tagebuch ist, wie man es benutzt und was mit
einem Eintrag über seine Lebensdauer geschieht.

Das ist nicht nur eine Ordnungsfrage. Drei konkrete Folgen sind bereits eingetreten:

- Die **nachträgliche Bearbeitung** existiert im Backend (`PUT .../diary/{entry_key}`), ist aber
  in keinem Dokument fachlich beschrieben — es gibt weder eine Aussage darüber, was sie mit einer
  vorhandenen Analyse macht, noch eine Regel für zwei Clients, die gleichzeitig schreiben.
- Der **Umgebungs-Schnappschuss** wird laut REQ-013 §2.3a.8 ausschließlich beim Anlegen erfasst.
  Wer beim Anlegen abwählt oder wessen Sensor gerade nicht antwortete, hat keinen Weg zurück.
- Die **Analyse-Historie** ist in REQ-050 §9 (O-01) als offen geführt, während §2.4 zugleich
  festlegt, dass ein neues Ergebnis das vorherige „vollständig überschreibt". Wer zweimal
  analysiert, verliert den ersten Befund unwiederbringlich.

Diese Anforderung schließt die drei Lücken und beschreibt die Funktion vollständig. Sie ist
zugleich die **verbindliche Grundlage für beide Clients**: Der Web-Client existiert
(`src/frontend/src/pages/tagebuch/`, `src/frontend/src/components/diary/`), der mobile Client ist
geplant (Flutter, CLAUDE.md „Tech Stack Summary"). Eine Anforderung, die Web-Annahmen in die
Fachlogik einbaut, macht den zweiten Client teurer als nötig — §7 zieht die Grenze explizit.

### 1.3 Scope-Abgrenzung

**Innerhalb:** Aufbau eines Eintrags, Anlegen, nachträgliche Bearbeitung aller Inhalte, Fotos
ergänzen und entfernen, erneute Erfassung des Umgebungs-Schnappschusses, Inhaltsversionierung,
Aktualitätskennzeichnung einer vorhandenen Analyse, Archiv abgeschlossener Analyseläufe,
Erfassungs- und Übersichtsoberfläche, Client-Neutralität.

**Außerhalb:**

- Die **Analyse selbst** — Zustandsmaschine, Lease, MCP-Vertrag, Einwilligung und das Betriebs­
  modell des externen Agenten bleiben vollständig in REQ-050. REQ-051 sagt nur, was mit einem
  Ergebnis geschieht, wenn sich sein Eintrag ändert.
- **Automatische Einträge.** Kein Regelsatz legt Einträge an; das Tagebuch ist ein Erzeugnis des
  Nutzers. (Das MCP-Werkzeug `add_plant_diary_entry` aus REQ-050 O-04 ist eine ausdrückliche,
  vom Nutzer betriebene Ausnahme und bleibt dort spezifiziert.)
- **Offline-Betrieb** und Konfliktauflösung zusammengeführter Offline-Bearbeitungen (§7.3).
- **Volltextsuche über eine Suchmaschine.** Die Freitextsuche der Übersicht arbeitet auf der
  Datenbank; ein Suchindex ist eine eigene Entscheidung.
- **Versionshistorie des Eintragsinhalts.** Archiviert werden Analyse*ergebnisse* (§5), nicht
  frühere Textfassungen (§13, O-52).

---

## 2. Der Eintrag

### 2.1 Bestandteile

Ein Tagebuch-Eintrag hängt an **genau einer** Pflanzeninstanz und besteht aus:

| Teil | Feld | Pflicht | Grenze |
|------|------|---------|--------|
| Typ | `entry_type` | ja | `observation`, `problem`, `milestone`, `measurement`, `photo`, `note` |
| Titel | `title` | nein | 200 Zeichen |
| Freitext | `text` | ja | 1–5000 Zeichen |
| Schlagworte | `tags` | nein | Freitext-Liste |
| Messwerte | `measurements` | nein | offenes Dict (`height_cm`, `leaf_count`, …) |
| Fotos | `photo_refs` | nein | bis zu 5 `attachment_id` (NFR-013 §2.2) |
| Umgebung | `environment` | — | serverseitig erfasst, siehe §2.3 |
| Analyse | `analysis*` | — | siehe REQ-050 |

Es gibt **keine** Pflichtfelder außer Typ und Freitext. Das ist Absicht: Das Tagebuch ist die
niedrigschwelligste Funktion des Systems (REQ-042, Einstufung `beginner`), und jedes zusätzliche
Pflichtfeld ist eine Hürde vor genau der Zielgruppe, für die es gedacht ist.

### 2.2 Anlegen

Ein Eintrag wird an der Pflanze angelegt (§6.1). Beim Anlegen löst der Server den
Umgebungs-Schnappschuss auf (REQ-013 §2.3a); der Client steuert darüber nur mit
`capture_environment: bool` (Vorgabe `true`), ob überhaupt **geschaut** wird — nie, was gespeichert
wird.

Ein Fehler bei der Umgebungserfassung darf die Anlage **nie** verhindern (REQ-013 §2.3a.4). Diese
Regel gilt unverändert und wird durch diese Anforderung nicht aufgeweicht: Wer gerade ein Problem
dokumentiert, ist im denkbar schlechtesten Moment, um wegen eines Sensors abgewiesen zu werden.

### 2.3 Drei Wertklassen, die getrennt bleiben müssen

Am Eintrag stehen drei Arten von Zahlen und Text, die aus verschiedenen Quellen stammen. Sie
sehen im Datensatz ähnlich aus und dürfen trotzdem nie vermischt werden:

| Klasse | Feld | Herkunft | Nachträglich änderbar (§3) |
|--------|------|----------|----------------------------|
| **Handnotiert** | `measurements`, `text`, `title`, `tags` | die Gärtnerin tippt sie | **ja**, frei |
| **Maschinell gelesen** | `environment` | Server löst sie über die REQ-005-Kette auf, mit Provenienz je Wert | **nein** — aber neu erfassbar (§3.5) |
| **Maschinell erzeugt** | `analysis`, `analysis_error` | externer Agent über MCP (REQ-050) | **nein** — nur über die Zustandsmaschine |

Die Trennung ist keine Ordnungsvorliebe, sondern eine Anforderung aus REQ-005 §1 und
NFR-011/REQ-025: maschinell erhobene Werte müssen von handnotierten unterscheidbar bleiben,
weil sie unterschiedlichen Aufbewahrungs- und Beweisregeln unterliegen. Ein „22,4 °C", das aus
`environment` nach `measurements` wandert, verliert dabei Provenienz, Messzeitpunkt und
Sensorbezug und ist danach von einer Handablesung nicht mehr zu unterscheiden.

### 2.4 Mandantentrennung und geteilte Mandanten

Dieser Abschnitt führt an einem Ort zusammen, was sonst über §3, §5, §9 und §11 verteilt steht.
Er ist **beschreibend, nicht zusätzlich**: Jede Regel hat ihre Quelle in einer der genannten
Anforderungen; hier steht sie im Zusammenhang.

#### 2.4.1 Anker ist die Pflanze, nicht der Eintrag

Ein Tagebuch-Eintrag trägt selbst einen `tenant_key`, aber die Zugriffsprüfung hängt **nicht**
daran. Sie hängt an der Pflanze: Sie wird geladen und ihr `tenant_key` fail-closed gegen den
Aufrufer geprüft, **bevor** irgendetwas anderes geschieht (REQ-013 §2.3a.8). Jeder weitere
Zugriff — Eintragsliste, einzelner Eintrag, Fotos, Umgebungserfassung, Archiv — startet damit von
einem Schlüssel, der nachweislich diesem Mandanten gehört.

**Warum das die richtige Verankerung ist:** Ein Prädikat, das nur den `tenant_key` des Eintrags
prüft, verlässt sich auf einen Wert, der beim Schreiben korrekt gesetzt worden sein muss. Ein
Prädikat am Anker prüft die Kette, über die der Aufrufer tatsächlich gekommen ist. Dieselbe
Überlegung steht hinter REQ-013 §2.3a.8: Ein `Sensor` trägt keinen eigenen `tenant_key` — genau
deshalb ist die Pflanzenprüfung dort nicht optional.

Für die **mandantenweite Übersicht** (§6.2) und das **Archiv** (§5) gibt es keinen Pflanzen-Anker
im Aufruf; beide filtern deshalb strikt auf `tenant_key` und tragen ihn im Index an erster Stelle
(§9.1, §8).

#### 2.4.2 Ein fremder Mandant antwortet `404`

Jeder Endpunkt dieser Anforderung antwortet auf einen Schlüssel aus einem fremden Mandanten mit
`404`, nie mit `403`. Ein `403` bestätigte, dass der Schlüssel existiert — das ist die Auskunft,
die gerade nicht gegeben werden soll. Die Regel gilt auch für die neuen Endpunkte
`POST .../capture-environment` und `GET .../analyses` (AK-57).

Ein **leerer** Umgebungs-Schnappschuss ist keine zulässige Antwort auf eine fremde Pflanze: Er
bestätigte immer noch, dass der Schlüssel irgendwo existiert (REQ-013 §4.7).

#### 2.4.3 Im geteilten Mandanten trennt die Autorschaft, nicht der Mandant

Im Gemeinschaftsgarten teilen sich alle Mitglieder **einen** Mandanten. Die Mandantengrenze
trennt dort nichts mehr — die zweite Achse ist die **Autorschaft** (`created_by == user_key`),
und sie ist je Handlung verschieden streng:

| Handlung | Beobachter | Gärtner, fremder Eintrag | Gärtner, eigener Eintrag | Leitung |
|----------|:---------:|:------------------------:|:------------------------:|:-------:|
| Eintrag und Fotos lesen | ✓ | ✓ | ✓ | ✓ |
| Analyse-Ergebnis und Archiv lesen | ✓ | ✓ | ✓ | ✓ |
| Eintrag anlegen | ✗ | — | ✓ | ✓ |
| Bearbeiten, Fotos ändern, Umgebung neu erfassen | ✗ | ✗ | ✓ | ✓ |
| Zur KI-Analyse markieren | ✗ | ✗ | ✓ | ✓ |
| Eintrag löschen | ✗ | ✗ | **✗** | ✓ |

Kurzform: **sehen alle alles, ändern darf jeder nur sein eigenes, löschen nur die Leitung.**

Drei Regeln in dieser Tabelle haben je eine eigene Begründung, die nicht ineinander aufgeht:

- **Lesen ist offen**, weil ein Gemeinschaftsgarten genau dafür geteilt wird. Die Übersicht ist
  mandantenweit und zeigt bewusst auch Einträge anderer Mitglieder (§6.2).
- **Markieren nur eigene** ist eine Datenschutzmaßnahme, keine Rollenfrage (REQ-050 §7.2): Sonst
  gäbe ein Mitglied fremde Beobachtungen und Fotos an sein eigenes Sprachmodell, ohne dass die
  Verfasser davon erfahren. Die Lockerung auf mandantenweites Markieren ist als REQ-050 O-02
  offen.
- **Löschen nur Leitung** ist die Irreversibilitätsgrenze aus REQ-049 §2.3 und läuft ausdrücklich
  **nicht** entlang der Autorschaft (§3.2, O-57).

**Diese zwei Achsen bleiben getrennt implementiert.** Die Rollenachse entscheidet
`require_permission` über die Prädikate der `MembershipEngine` und ist zugleich Autorität für die
MCP-Oberfläche und die Anhang-Wache; die Autorschaftsachse ist eine zusätzliche Prüfung am
Tagebuch-Dienst. Sie zusammenzulegen zöge eine Tagebuch-Sonderregel in eine Tabelle, die 27
andere Ressourcen mitgatet (§10).

**Fotos tragen eine dritte, engere Regel.** Ein Gärtner darf nur Attachments referenzieren, die
er selbst hochgeladen hat; die Leitung ist ausgenommen (SEC-003, §3.3). Das ist strenger als die
Eintrags-Autorschaft und bleibt es: Ein eigener Eintrag ist kein Freibrief, ein fremdes Foto
anzuhängen.

**Eine Bearbeitung durch die Leitung entwertet die Analyse des Verfassers.** Ändert die Leitung
einen fremden Eintrag, steigt dessen `content_version`, und ein vorhandenes Ergebnis gilt für
alle Betrachter als veraltet (§4.1). Das ist gewollt — das Ergebnis passt tatsächlich nicht mehr
zum Inhalt —, aber es ist eine Handlung mit Wirkung auf einen fremden Datensatz, und die
Oberfläche muss den Hinweis aus §6.3 auch dort zeigen.

#### 2.4.4 Persönlicher Mandant und Light-Modus

Im **persönlichen Mandanten** (bei der Registrierung automatisch angelegt, REQ-024) ist der
Nutzer selbst Leitung; alle Einschränkungen dieses Abschnitts sind dort ohne Wirkung.

Im **Light-Modus** (REQ-027) gibt es keine Konten. Alle Einträge gehören demselben System-Nutzer,
die Einschränkung „nur eigene" entfällt und die Einwilligungsprüfung ebenfalls
(REQ-050 §7.5, §11).

#### 2.4.5 Die Standort-Zuweisung ist **keine** Schreibgrenze

Wer im Mandanten Gärtner ist, darf an **jeder** Pflanze des Mandanten ein Tagebuch führen —
unabhängig davon, wem die Parzelle zugewiesen ist, auf der sie steht. Das ist keine Lücke dieser
Anforderung, sondern die geltende Regel: **REQ-049 §3.5** stellt fest, dass die Standort-Zuweisung
Koordination ist und kein Recht, und hebt die zuweisungsbasierte Schreibkontrolle aus
REQ-024 §1a.5 **ersatzlos** auf; REQ-024 v1.7 hat den Abschnitt daraufhin gestrichen.

Das Tagebuch prüft die Zuweisung also nicht, **weil es sie nicht prüfen soll**. Die Begründung aus
REQ-049 §2.1 (P1/P2) trägt hier besonders gut: Eine Beobachtung ist kein Eingriff. „An der Pflanze
im Nachbarbeet sind Blattläuse" ist genau die Meldung, die ein Gemeinschaftsgarten haben will, und
eine Zuweisungsprüfung am Tagebuch verhinderte sie. Wer echte Trennung braucht, bekommt einen
eigenen Mandanten.

REQ-024 beschrieb bis v1.6 in §1.1 Szenario 2 und in den Matrixzellen von §1a.1 noch den
abgelösten Zustand und widersprach damit REQ-049 §3.5. Das ist mit **REQ-024 v1.7** nachgeführt:
§1a.5 ist ersatzlos gestrichen, die Matrix trägt kein `own`/`community` mehr. Wer die
Berechtigungsfrage nachschlägt, findet in beiden Dokumenten dieselbe Antwort.

---

## 3. Nachträgliche Bearbeitung

### 3.1 Was änderbar ist

Ein bestehender Eintrag ist nachträglich änderbar. Änderbar sind:

- **Freitext** (`text`), **Titel** (`title`), **Typ** (`entry_type`), **Schlagworte** (`tags`),
- **Messwerte** (`measurements`) — einzeln ergänzbar, korrigierbar und entfernbar,
- **Fotos** (`photo_refs`) — ergänzbar und entfernbar, bis zur Obergrenze von fünf.

Nicht über den generischen Bearbeitungspfad änderbar sind:

- der **Umgebungs-Schnappschuss** (`environment`, `environment_captured_at`,
  `environment_status`) — er hat einen eigenen, ausdrücklichen Weg (§3.5),
- alle **Analysefelder** — jeder Zustandswechsel hat in REQ-050 §2.2 seinen eigenen, geprüften
  Endpunkt, und ein generisches Update, das `analysis_state` mitschreiben dürfte, wäre ein Weg an
  Lease und Rechteprüfung vorbei,
- `created_by`, `created_at`, `plant_key`, `tenant_key`.

**Ein Eintrag wandert nie zu einer anderen Pflanze.** Eine Beobachtung gehört zu der Pflanze, an
der sie gemacht wurde; eine Verschiebung wäre eine nachträgliche Umdeutung der Beobachtung, keine
Korrektur. Wer sich in der Pflanze geirrt hat, löscht und legt neu an — dann ist auch die
Zuordnung der Fotos und des Umgebungs-Schnappschusses wieder stimmig.

### 3.2 Wer bearbeiten darf

Bearbeiten ist ein Schreibrecht und folgt derselben Regel wie das Markieren zur Analyse
(REQ-050 §7.2): Gärtner bearbeiten **eigene** Einträge, die Rolle Leitung bearbeitet alle,
Beobachter bearbeiten keine.

**Warum „eigene" hier zulässig ist, obwohl REQ-049 §3.1 es für Fachdaten verbietet.** Die Regel
dort lautet: `Eigene` gilt **ausschließlich** bei verfassten Inhalten — Pinnwand-Beiträge,
Kommentare, eigene Betroffenenanfragen — und **nie** bei Fachdaten. Ein Tagebuch-Eintrag ist ein
verfasster Inhalt: eine Beobachtung in den Worten ihres Verfassers, keine Zustandsangabe über die
Pflanze. Er steht damit in derselben Kategorie wie ein Pinnwand-Beitrag, nicht in der von
Pflanzdurchlauf, Ernte oder Messreihe.

Die Abgrenzung trägt innerhalb dieser Anforderung: Ein **Foto** an einem Eintrag ist Fachdatum —
es dokumentiert die Pflanze, nicht die Meinung des Fotografen — und unterliegt deshalb der
Herkunftsregel SEC-003 (§3.3) statt der Autorschaft. Die Prüfung „nur eigene" ist außerdem
**keine Rollenfrage** und liegt deshalb nicht in `MembershipEngine.can_edit_resource`, dessen
Zusage („jede Fachressource, unabhängig von Zuweisung", REQ-024 AK-30) davon unberührt bleibt,
sondern als zusätzliche Prüfung am Tagebuch-Dienst (§10).

**Löschen ist ausschließlich der Rolle Leitung vorbehalten** — auch dem Verfasser eines Eintrags
steht es nicht zu. Das ist die Irreversibilitätsgrenze aus REQ-049 §2.3, die dem Gärtner
ausdrücklich „kein Löschen" zuweist und in `MembershipEngine.can_delete_resource` als
`role == LEAD` durchgesetzt wird. Die Grenze verläuft nicht entlang der Autorschaft, sondern
entlang der Umkehrbarkeit: Ein Gärtner korrigiert einen Fehler, indem er den Wert überschreibt —
und genau dafür gibt es seit dieser Anforderung die vollständige Bearbeitung. Geschichte zu
tilgen ist eine andere Art von Handlung.

**Praktische Folge, die zu kennen ist:** Im persönlichen Mandanten ist der Nutzer selbst Leitung,
dort ändert sich nichts. Im Gemeinschaftsgarten kann ein Gärtner seinen eigenen versehentlichen
Eintrag **nicht** löschen, sondern nur leeren. Ob das die gewollte Härte ist, ist als O-57 (§13)
geführt — die Regel selbst wird hier nicht aufgeweicht, weil eine Ausnahme „eigene Einträge" die
Grenze für genau die Datensätze auflöste, für die REQ-049 sie gezogen hat.

Im Light-Modus (REQ-027) entfällt die Einschränkung „nur eigene", weil dort alle Einträge
demselben System-Nutzer gehören — dieselbe Begründung wie in REQ-050 §7.5.

### 3.3 Fotos

Fotos werden über den Erfassungsbaustein **REQ-052 §2** erfasst (Live-Kamera, Gerätekamera,
Datei-Upload) mit dem Profil `gallery` (REQ-052 §3) und als `attachment_id` referenziert, nie als Storage-URL.

- **Ergänzen** ist bis zur Obergrenze von fünf möglich. Der Versuch, eine sechste Referenz zu
  setzen, wird abgewiesen (`validation.error`) und **nie** still gekürzt.
- **Entfernen** löst die Referenz am Eintrag. Ob das Attachment selbst gelöscht wird, entscheidet
  NFR-013 — nicht diese Anforderung; ein Attachment kann grundsätzlich von mehreren Stellen
  referenziert sein.
- Eine Referenz auf ein Attachment, das dem Mandanten nicht gehört, wird abgewiesen. Ein
  Gärtner darf nur Attachments referenzieren, die er selbst hochgeladen hat; die Rolle Leitung
  ist davon ausgenommen (SEC-003, dieselbe Regel, die REQ-050 O-04 für das MCP-Werkzeug zitiert).

### 3.4 Messwerte

`measurements` ist ein offenes Dict ohne Provenienz. Es ist frei änderbar: Schlüssel ergänzen,
Werte korrigieren, Schlüssel entfernen. Eine Korrektur ersetzt den Wert; frühere Werte werden
nicht aufbewahrt (§13, O-52).

**Warum offen und nicht auf einen Katalog festgelegt:** Das Vokabular der Messwerte ist
kulturabhängig (`stem_diameter_mm` an der Tomate, `pseudobulb_count` an der Orchidee). Ein
geschlossener Katalog müsste für jede neue Kultur nachgezogen werden und würde in der Zwischenzeit
genau die Notiz verhindern, für die das Feld da ist.

### 3.5 Umgebungs-Schnappschuss: neu erfassen statt bearbeiten

Der Schnappschuss ist **nicht editierbar**. Ein Wert, den der Client schreiben kann, ist ein Wert,
den der Client erfinden kann — und dieser hier soll Belegmaterial sein (REQ-013 §2.3a.8). Ein
handisch korrigiertes `environment` wäre nach der Korrektur ununterscheidbar von einer
Sensorablesung und damit als Beleg wertlos.

Stattdessen gibt es eine **ausdrückliche Handlung**, die den Schnappschuss neu auflöst:

```
POST .../diary/{entry_key}/capture-environment
```

Der Server durchläuft dieselbe Kette wie beim Anlegen (Standort → Gelände → Wetterdienst →
nichts), mit demselben Zeitbudget, derselben Aktualitätsgrenze und denselben Statuswerten
(REQ-013 §2.3a.3 bis §2.3a.6). Das Ergebnis **ersetzt** `environment`, `environment_captured_at`
und `environment_status` und erhöht `content_version` (§3.6).

**Verhältnis zu REQ-013 §2.3a.8.** Dort steht: „Erfasst wird nur beim Anlegen. Eine spätere
Textkorrektur darf den Eintrag nicht **still** mit einem anderen Klima neu stempeln, deshalb
schützt `update_entry` die drei Felder wie die Analysefelder." Diese Regel bleibt **unverändert
gültig** und wird durch §3.5 nicht aufgehoben: Der generische Bearbeitungspfad rührt die drei
Felder weiterhin nicht an. Was hinzukommt, ist das Gegenteil eines stillen Neustempelns — eine
Handlung, die der Nutzer benennt und auslöst und deren Zeitpunkt der Datensatz festhält.

**`environment_captured_at` ist die Ehrlichkeitsgarantie.** Weicht es von `created_at` ab, wurde
der Schnappschuss nachträglich geholt, und der Datensatz sagt das von selbst. Die Oberfläche muss
diese Abweichung sichtbar machen, sobald sie `DIARY_SNAPSHOT_MAX_LAG_MINUTES` (Vorgabe
**60 Minuten**) überschreitet — sonst liest sich am Eintrag von gestern das Klima von heute wie
das Klima von gestern (AK-43).

**Warum das eine eigene Stellschraube ist (#1216).** Bis hierher stand hier
`DIARY_ENVIRONMENT_MAX_AGE_MINUTES` — dieselbe Einstellung, die REQ-013 §2.3a.5 dafür verwendet,
wie alt ein **Sensorwert bei der Erfassung** sein darf. Die beiden Zahlen sind heute gleich, aber
sie messen nicht dasselbe und folgen nicht demselben Grund:

| Einstellung | Misst | Folgt aus |
|---|---|---|
| `DIARY_ENVIRONMENT_MAX_AGE_MINUTES` (REQ-013 §2.3a.5) | Alter der **Messung** zum Zeitpunkt der Erfassung | der Melde-Taktung der Hardware |
| `DIARY_SNAPSHOT_MAX_LAG_MINUTES` (hier) | Abstand zwischen `environment_captured_at` und `created_at` | wie weit ein **nachgetragener** Schnappschuss noch als „die Bedingungen, als hingesehen wurde" durchgeht |

Mit einer Stellschraube für beides hatte jede Bewegung eine unbeabsichtigte zweite Wirkung: Die
Sensorfrische zu verschärfen — etwa auf 15 Minuten, weil ein Sensor stündlich meldet und das zu
grob ist — hätte nebenbei fast jeden nachgetragenen Schnappschuss mit dem Warnhinweis versehen;
sie zu lockern hätte den Hinweis stillgelegt. Getrennt lässt sich jede Zahl aus ihrem eigenen
Grund wählen. Beide sind global konfigurierbar und **nicht** mandantenspezifisch.

**Ein bereits erfolgreicher Schnappschuss wird nur nach Rückfrage ersetzt.** Steht
`environment_status` auf `captured`, ist bereits Belegmaterial vorhanden; eine erneute Erfassung
verwirft es. Die Oberfläche verlangt dafür eine Bestätigung, die benennt, was verloren geht
(AK-44). Die Hauptanwendung des Endpunkts ist der umgekehrte Fall: `opted_out`, `no_source`,
`not_attempted` oder ein durch eine Störung abgeschnittenes `unavailable` — dort gibt es nichts zu
verlieren und heute keinen Weg zurück.

### 3.6 Inhaltsversion

Der Eintrag trägt einen monoton steigenden Zähler:

```python
content_version: int = 1
```

Er wird bei **jeder** Änderung an einem analyse-relevanten Feld um eins erhöht:
`entry_type`, `title`, `text`, `tags`, `measurements`, `photo_refs`, `environment`.

Er wird **nicht** erhöht bei Änderungen, die die Analysegrundlage nicht berühren — heute betrifft
das nur `updated_at` selbst und die Analysefelder, die ihre eigenen Pfade haben.

**Die Erhöhung hat genau eine Stelle.** Sie liegt im Schreibpfad des Tagebuch-Dienstes
(`PlantDiaryService`), nicht in den Routern und nicht im Repository-Aufrufer. Ein Zähler, den
jeder Schreibpfad selbst hochzählen muss, wird beim nächsten hinzukommenden Pfad vergessen — und
zwar unbemerkt, weil das Weglassen keinen Fehler erzeugt, sondern nur eine veraltete Analyse
weiterhin als aktuell ausweist. Das ist die schädliche Richtung. Die Umsetzung muss deshalb
zusätzlich einen Test führen, der die **Abwesenheit** eines zweiten Schreibpfads prüft: kein
Modul außerhalb des Dienstes schreibt `plant_diary_entries` direkt (AK-46).

**Bestandsdokumente.** Ein Eintrag ohne `content_version` wird als `1` gelesen; eine Migration ist
nicht nötig. Ein gespeichertes Ergebnis ohne `analyzed_content_version` wird ebenfalls als `1`
gelesen und gilt damit als aktuell, solange der Eintrag seit Einführung dieser Anforderung nicht
bearbeitet wurde. Das ist die ehrlichere von zwei unvollkommenen Auslegungen: Vor dieser
Anforderung war eine Bearbeitung überhaupt nicht feststellbar, und pauschal „veraltet" zu melden
hieße, eine Tatsache zu behaupten, die niemand geprüft hat. Ein Eintrag, der **vor** Einführung
nach seiner Analyse bearbeitet wurde, wird als aktuell gelesen — diese Unschärfe ist nicht
auflösbar und läuft mit dem ersten Bearbeitungsvorgang danach aus.

### 3.7 Gleichzeitige Bearbeitung

Zwei Clients desselben Nutzers — Telefon im Gewächshaus, Browser am Schreibtisch — können
denselben Eintrag offen haben. Ohne Regel gewinnt der letzte Schreibvorgang und überschreibt den
anderen stillschweigend. Das ist die Lost-Update-Klasse, die in diesem Projekt bereits einmal
aufgetreten ist.

**Regel:** Der Bearbeitungsaufruf darf die Inhaltsversion mitführen, gegen die er geschrieben
wurde:

```
PUT .../diary/{entry_key}
{ "text": "...", "expected_content_version": 7 }
```

- Stimmt sie mit dem gespeicherten Wert überein, wird geschrieben.
- Weicht sie ab, antwortet der Server `409` mit `conflict.stale_write` und liefert die aktuelle
  Inhaltsversion mit, damit der Client neu laden und den Konflikt anzeigen kann. Es wird **nichts**
  geschrieben und **nichts** zusammengeführt.
- Fehlt das Feld, gilt das bisherige Verhalten (letzter Schreibvorgang gewinnt).

**Warum optional und nicht verpflichtend:** Das Feld verpflichtend zu machen wäre eine brechende
Änderung an einem Endpunkt, der bereits Aufrufer hat. Beide Clients **sollen** es setzen (AK-47),
und die Kennzeichnung als optional ist eine Übergangsregel, kein Dauerzustand — sie ist in §13
(O-53) als Verschärfung geführt.

---

## 4. Aktualität einer vorhandenen Analyse

### 4.1 „Veraltet" wird abgeleitet, nicht gesetzt

Eine abgeschlossene Analyse gilt als **veraltet**, wenn sie gegen eine ältere Inhaltsversion
gerechnet wurde als die, die der Eintrag jetzt trägt:

```
analysis_outdated  ⟺  analysis ≠ null  ∧  analysis.analyzed_content_version < entry.content_version
```

Das Feld `analysis_outdated: bool` steht in jeder Antwort (`DiaryEntryResponse`,
`DiaryOverviewItem`) und **nicht** im Datensatz.

**Warum abgeleitet und nicht als Flag gespeichert:** Ein gespeichertes Flag müsste an jedem
Schreibpfad gesetzt werden — Text, Fotos, Messwerte, Schnappschuss, künftige Felder. Wird es an
einem davon vergessen, ist der Wächter genau dort inert, wo er gebraucht wird, und der Fehler ist
nicht sichtbar: Der Eintrag zeigt weiterhin „aktuell" an, obwohl er es nicht ist. Ein Vergleich
zweier Zahlen kann diese Drift nicht entwickeln, weil es keine zweite Stelle gibt, an der er
vergessen werden könnte. Der Preis ist ein Vergleich je Antwortzeile — messbar nichts.

### 4.2 Kein sechster Zustand

`analysis_state` behält seine fünf Werte aus REQ-050 §2.2. Veraltetheit ist **kein** sechster
Zustand.

Die beiden Angaben beantworten verschiedene Fragen: `analysis_state` sagt, ob Arbeit existiert,
läuft oder abgeschlossen ist; `analysis_outdated` sagt, ob das vorliegende Ergebnis noch zu dem
passt, was am Eintrag steht. Sie zusammenzulegen kostet Information. Ein Zustand `outdated`
verdeckte, dass überhaupt ein Ergebnis vorliegt — obwohl das Ergebnis der Grund ist, warum die
Frage gestellt wird — und zöge Übergänge nach sich (`completed → outdated → requested`), die
nichts beschreiben, was tatsächlich geschieht.

Ein veralteter Eintrag bleibt also `completed` (bzw. `failed`) **und** ist als veraltet
gekennzeichnet. Erneutes Markieren führt ihn nach `requested`, unverändert nach REQ-050 §2.2.

### 4.3 Bearbeitung während einer laufenden Analyse

| Zustand bei der Bearbeitung | Was geschieht |
|-----------------------------|---------------|
| `none` | nichts Besonderes; es gibt kein Ergebnis, das veralten könnte |
| `requested` | Bearbeitung erlaubt, Zustand unverändert. Der Agent beansprucht später und liest die **neue** Fassung — es entsteht kein veraltetes Ergebnis. |
| `in_progress` | Bearbeitung erlaubt. Der laufende Agent rechnet gegen die Fassung, die beim Beanspruchen galt; sein Ergebnis wird angenommen, archiviert und ist beim Eintreffen bereits als veraltet gekennzeichnet. |
| `completed` / `failed` | Bearbeitung erlaubt, Zustand unverändert, vorhandenes Ergebnis wird veraltet. |

**Die Bearbeitung wird während `in_progress` nicht gesperrt.** Eine Sperre bestrafte die
Gärtnerin für einen Lauf, dessen Dauer ihr niemand zusagt (REQ-050 §3) und dessen Lease bis zu
15 Minuten hält. Die abgeleitete Veraltetheit macht die Sperre überflüssig: Das Ergebnis ist
korrekt für die Fassung, gegen die es gerechnet wurde, und es sagt selbst, welche das war.

**Das eingetroffene Ergebnis wird nicht verworfen.** Es zurückzuweisen vernichtete eine
Modellabfrage, die der Nutzer bezahlt hat, und hinterließe einen Eintrag ohne Ergebnis, obwohl
eines existiert. Es wird angenommen, archiviert (§5) und angezeigt — mit dem Hinweis, worauf es
sich bezieht.

### 4.4 Welche Fassung als analysiert gilt

`analyzed_content_version` wird **serverseitig** gesetzt, aus der Inhaltsversion, die beim
**Beanspruchen** galt. Dafür hält der Eintrag zusätzlich `analysis_claimed_content_version`
(§8).

Ein vom Agenten mitgeschickter Wert wird **ignoriert**. Der Agent ist die Partei, die von einem
zu hohen Wert profitiert — er ließe sein Ergebnis als aktuell erscheinen —, und der Server weiß
ohnehin genau, welche Fassung er beim Beanspruchen ausgehändigt hat.

Der Rand des Verfahrens ist bekannt und bewusst so gewählt: Wird zwischen Beanspruchen und
Abrufen bearbeitet, liest der Agent bereits die neue Fassung, während der Server die alte
vermerkt hat — das Ergebnis gilt dann als veraltet, obwohl es aktuell ist. Der umgekehrte Irrtum
wäre der schädliche; die Regel irrt bewusst in die harmlose Richtung.

---

## 5. Analyse-Archiv

Diese Anforderung entscheidet REQ-050 §9 (O-01) mit **ja**: Es wird eine Historie geführt.
REQ-050 §5 nennt genau diesen Fall als den, ab dem eine eigene Collection gerechtfertigt ist.

### 5.1 Eigene Collection, keine eingebettete Liste

Archivierte Läufe liegen in einer **eigenen Document-Collection** `plant_diary_analyses`, nicht
als Liste im Eintragsdokument.

**Warum nicht eingebettet:** Eine eingebettete Historie hinge an jedem Lesevorgang des Eintrags.
Die mandantenweite Übersicht lädt 50 Zeilen je Seite; REQ-013 §4.7 führt bereits aus, warum sie
deshalb nicht einmal *ein* vollständiges Ergebnis je Zeile transportiert. Zehn Befundlisten je
Zeile wären dieselbe Fehlentscheidung, nur zehnfach. Der Eintrag behält deshalb ausschließlich das
**jüngste** Ergebnis in `analysis` — denormalisiert, damit die Anzeige eines Eintrags ohne
Nachschlag auskommt.

**Kein Kanten-Eintrag im Named Graph.** Die einzige Abfrage lautet „alle Läufe zu Eintrag X,
neueste zuerst" und wird von einem persistenten Index über `(tenant_key, entry_key, recorded_at)`
beantwortet. Eine Kante wäre eine zweite Zuordnung neben `entry_key`, die mit ihr auseinanderlaufen
kann und von keiner Traversierung gebraucht wird.

### 5.2 Jeder Lauf wird archiviert, auch der fehlgeschlagene

Ein Archiveintrag entsteht **in dem Moment, in dem ein Ergebnis eintrifft** — also bei
`submit_diary_analysis` (REQ-050 §4.5), für `completed` **und** für `failed`.

**Warum beim Eintreffen und nicht beim Überschreiben:** „Das Vorherige wegschreiben, bevor das
Neue kommt" klingt sparsamer, hat aber zwei Löcher. Das jeweils jüngste Ergebnis erreichte das
Archiv nie — es wird ja nie überschrieben —, sodass ein Eintrag mit genau einer Analyse eine leere
Historie hätte. Und ein Lauf, der die Verdrängung nicht auslöst, hinterließe eine Lücke. Beim
Eintreffen zu archivieren hat einen Schreibpfad, keine Sonderfälle und dieselbe Transaktion wie
das Setzen des Zustands.

**Warum auch `failed`:** Ein Fehlschlag ist diagnostische Information — „das Modell ist an diesem
Eintrag dreimal an derselben Stelle gescheitert" ist genau das, was man beim vierten Versuch
wissen will. Ihn nicht aufzubewahren hieße, die Historie ausgerechnet dort zu unterbrechen, wo
etwas schiefging.

Die Denormalisierung ist gewollt: Das jüngste Ergebnis steht zweimal — am Eintrag und im Archiv.
Das Archiv ist die vollständige Reihe, `entry.analysis` der schnelle Zugriff auf ihr letztes Glied.

### 5.3 Lesen

```
GET .../diary/{entry_key}/analyses
```

liefert die Läufe des Eintrags absteigend nach `recorded_at`, seitenweise (`limit`, `offset`,
Vorgabe 20), mit vollständigem Ergebnis je Lauf. Leseberechtigt ist jedes Mitglied des Mandanten —
dieselbe Regel, die für das jüngste Ergebnis gilt (REQ-050 §6).

Die Oberfläche zeigt die Historie **nicht ausgeklappt**, sondern als abrufbare Liste unter dem
aktuellen Ergebnis (§6.4). Ein Eintrag mit einer einzigen Analyse zeigt keine Historie an — eine
Liste mit einem Element, das schon darüber steht, ist Rauschen.

### 5.4 Löschung und Aufbewahrung

- Ein Archiveintrag teilt das Schicksal seines Tagebuch-Eintrags: Löschen des Eintrags löscht
  seine Archiveinträge, Löschen der Pflanze löscht beides. Ein Archiveintrag ohne Eintrag wäre ein
  verwaistes Personendatum ohne Zugriffspfad — genau das, was NFR-011 verhindern soll.
- Eine eigene Aufbewahrungsfrist gibt es nicht; sie wäre gegenüber dem Eintrag, an dem die Läufe
  hängen, willkürlich (dieselbe Begründung wie REQ-050 §7.4).
- Bei Nutzerlöschung werden `requested_by` und `claimed_by` auf `_anonymized` gesetzt; der Lauf
  selbst bleibt erhalten (§11).
- Die Auskunft nach Art. 15/20 umfasst die archivierten Läufe (§11).

---

## 6. Oberfläche

> Übernommen aus REQ-050 v1.4 §2.5, ergänzt um die Bearbeitung (§6.3) und die
> Aktualitäts-/Historie-Anzeige (§6.4).

Die Oberfläche hat **zwei getrennte Orte** mit unterschiedlichen Aufgaben. Diese Trennung ist
verbindlich, nicht nur eine Layout-Empfehlung: Erfasst wird dort, wo man die Pflanze vor sich hat;
gesichtet wird dort, wo man alle Pflanzen zusammen sieht.

| | Ort | Aufgabe |
|---|-----|---------|
| **Erfassung** | Pflanzeninstanz-Detailseite, Tab „Tagebuch" | Einträge anlegen, bearbeiten, löschen, Fotos anhängen, zur Analyse markieren |
| **Sichtung** | Eigene Tagebuch-Übersicht, mandantenweit | Alle Einträge **aller** Pflanzen zusammen, mit Analyse-Status auf einen Blick |

### 6.1 Erfassung an der Pflanzeninstanz

Das Tagebuch einer Pflanze ist ein **Tab auf der Pflanzeninstanz-Detailseite** — neben dem
Foto-Galerie-Tab aus REQ-034, nach demselben Muster. Der Nutzer sieht dort ausschließlich die
Einträge dieser einen Pflanze, chronologisch absteigend.

- Anlegen: Typ, Titel, Freitext, Tags, optionale Messwerte, bis zu 5 Fotos (Erfassung nach REQ-052 §2,
  Profil `gallery`).
- Je Eintrag: Bearbeiten (§6.3), Löschen, Fotos als Vorschau (512-px-Rendition), Lightbox bei
  Klick.
- Je Eintrag: Schalter **„Analysieren"** (nur mit Schreibrecht und nur für eigene Einträge bzw.
  bei Rolle Leitung, REQ-050 §7.2). Ist der Eintrag bereits markiert, wird der Schalter zu
  „Markierung zurücknehmen" — solange der Zustand `requested` ist.

**Warum die Erfassung nicht in der Übersicht liegt:** Ein Eintrag gehört immer zu genau einer
Pflanze. Ein Anlegen-Dialog in einer mandantenweiten Liste müsste die Pflanze erst erfragen — ein
zusätzlicher Schritt genau dort, wo der Nutzer ihn schon beantwortet hat, wenn er von der Pflanze
kommt.

### 6.2 Tagebuch-Übersicht (mandantenweit)

Eine eigene Seite unter `/tagebuch` listet die Einträge **aller** Pflanzen des Mandanten in einer
gemeinsamen, chronologisch absteigenden Ansicht. Sie ist der Ort, an dem ein Nutzer den
Analyse-Stand überblickt, ohne Pflanze für Pflanze durchzuklicken.

Je Zeile:

| Spalte | Inhalt |
|--------|--------|
| Datum | `created_at` des Eintrags |
| Pflanze | Name und Kennung der Pflanzeninstanz, verlinkt auf deren Detailseite |
| Art | Wissenschaftlicher bzw. gebräuchlicher Name |
| Typ | Eintragstyp |
| Titel / Auszug | Titel, sonst die ersten Zeichen des Freitexts |
| Fotos | Anzahl angehängter Fotos, mit Miniaturvorschau des ersten |
| **Analyse** | Zustandsanzeige, siehe unten |

**Die Analyse-Spalte ist der Kern dieser Ansicht** und unterscheidet fünf Zustände sichtbar
voneinander — nicht nur „Ergebnis ja/nein":

| Zustand | Darstellung |
|---------|-------------|
| `none` | neutral, „nicht markiert"; bei Schreibrecht als Schalter „Analysieren" bedienbar |
| `requested` | „wartet auf Analyse" — ausdrücklich **kein** Fortschrittsbalken, es gibt keine Zusage über die Dauer (REQ-050 §3) |
| `in_progress` | „wird analysiert", mit dem Zeitpunkt des Beanspruchens |
| `completed` | **Ergebnis vorhanden** — deutlich hervorgehoben, mit der Zusammenfassung als einzeilige Vorschau |
| `failed` | Fehlerhinweis mit der gemeldeten Ursache und der Möglichkeit, erneut zu markieren |

**Zusätzlich, quer zu diesen fünf:** Ist `analysis_outdated` gesetzt, trägt die Zelle einen
sichtbaren Zusatz „nicht mehr aktuell" (§4). Er ersetzt die Zustandsanzeige nicht, sondern ergänzt
sie — sonst ginge verloren, dass überhaupt ein Ergebnis vorliegt (AK-40).

Filter und Sortierung, mindestens:

- **nach Analyse-Zustand** — insbesondere „nur mit Ergebnis" und „nur wartend". Das ist der
  häufigste Zugriff überhaupt: „Was ist inzwischen fertig?"
- **nach Aktualität** — „nur veraltete Ergebnisse". Das ist die Arbeitsliste nach einer
  Bearbeitungsrunde (AK-41).
- nach Pflanze, Art, Eintragstyp, Tag und Zeitraum
- Freitextsuche über Titel und Text
- Sortierung nach Erfassungsdatum (Vorgabe) oder Analyse-Zeitpunkt

Ein Klick auf eine Zeile öffnet den vollständigen Eintrag samt Fotos und — falls vorhanden — dem
Analyse-Ergebnis.

Die Übersicht ist **mandantenweit**, zeigt also im Gemeinschaftsgarten auch Einträge anderer
Mitglieder. Markieren und bearbeiten darf der Nutzer dort trotzdem nur die eigenen
(REQ-050 §7.2, §3.2); fremde Zeilen zeigen den Zustand, aber keinen Schalter.

Endpunkt, Filterparameter und Antwortschema stehen in §9.

### 6.3 Bearbeiten

Bearbeiten geschieht im selben Dialog wie das Anlegen, mit denselben Feldern — kein zweites,
abweichendes Formular. Zusätzlich gilt:

- Fotos lassen sich im Dialog **einzeln entfernen** und **ergänzen**, bis zur Obergrenze von fünf;
  die verbleibende Anzahl ist sichtbar, bevor der fünfte Platz belegt ist.
- Liegt ein Analyse-Ergebnis vor, weist der Dialog **vor dem Speichern** darauf hin, dass die
  Bearbeitung es als nicht mehr aktuell kennzeichnet (AK-42). Der Hinweis verhindert das Speichern
  nicht — er verhindert die Überraschung.
- Der Umgebungs-Schnappschuss ist im Dialog **unveränderlich dargestellt**, mit
  `environment_captured_at` und `environment_status` im Klartext, und trägt daneben die Handlung
  „neu erfassen" (§3.5).
- Der Dialog schickt `expected_content_version` mit (§3.7) und zeigt bei `409` an, dass der
  Eintrag zwischenzeitlich verändert wurde, statt still zu überschreiben.

### 6.4 Darstellung des Analyse-Ergebnisses

Wo ein Ergebnis vorliegt — in der Detailansicht des Eintrags, an beiden Orten gleich:

- Zusammenfassung als Erstes.
- Aufklappbare Befundliste: je Befund Bezeichnung, Konfidenz und Begründung. Die Konfidenz wird
  als Zahl **und** sprachlich eingeordnet; eine nackte Prozentzahl suggeriert eine Genauigkeit,
  die ein Sprachmodell nicht hat.
- Empfohlene Maßnahmen als Liste.
- Herkunftsangabe: Modell, Rezeptversion, Zeitpunkt, welche Fotos ausgewertet wurden.
- **Der Vorbehalt ist immer sichtbar**, nicht aufklappbar versteckt (REQ-050 §2.4).
- **Ist das Ergebnis veraltet, steht das über der Zusammenfassung**, nicht darunter und nicht als
  Fußnote — mit der Handlung „erneut analysieren" daneben. Ein Nutzer, der die Zusammenfassung
  gelesen hat, hat die Entscheidung bereits getroffen; ein Hinweis darunter kommt zu spät (AK-40).
- **Frühere Läufe** sind als eingeklappte Liste erreichbar, sobald mehr als einer existiert (§5.3).
  Je Lauf: Zeitpunkt, Ausgang (`completed`/`failed`), Modell, Rezeptversion und die Angabe, ob er
  sich auf eine ältere Fassung des Eintrags bezog. Aufklappen zeigt das vollständige Ergebnis
  (AK-45).

### 6.5 Aktualisierung

Der Zustand wird nicht live gepusht; ein Nachladen beim Öffnen der Ansicht genügt, ergänzt um eine
Auffrischen-Schaltfläche in der Übersicht. Es gibt keinen Server-zu-Client-Kanal im MCP-Transport
(REQ-033 §4.3a) und keinen Grund, für diese Funktion einen einzuführen.

### 6.6 Nachforderung erfüllen

Fordert ein Analyse-Lauf Bilder nach (REQ-050 §2.6), erscheint dafür eine gewöhnliche Aufgabe in
der Warteschlange. Dieser Abschnitt beschreibt, was der Nutzer sieht, wenn er sie öffnet — nicht,
wie die Aufgabe entsteht (REQ-006 § FreeStyle, „Foto-Auftrag") und nicht, wie die Kamera bedient
wird (REQ-052).

**Der Einstieg ist die Aufgabe, nicht der Eintrag.** Die Nachforderung ist eine Bitte, die der
Nutzer irgendwann beantwortet — vielleicht morgen, vielleicht wenn er ohnehin bei der Pflanze
steht. Sie in die Eintragsansicht zu legen hieße, sie nur dort zu zeigen, wo er gerade nicht ist.
Der Auftrag steht deshalb in Aufgabenliste, Dashboard und Kalender wie jede andere Aufgabe, mit
dem Maschinen-Badge aus REQ-006. Aus der Eintragsansicht führt umgekehrt ein Verweis auf den
offenen Auftrag, damit die beiden Orte sich nicht widersprechen.

**Ein Motiv nach dem anderen.** Der Ablauf führt durch die Motive der Nachforderung einzeln, in der
Reihenfolge, in der der Agent sie genannt hat. Je Motiv:

- **Was** aufzunehmen ist (`what`) als Überschrift.
- **Warum** es fehlt (`why`) darunter, immer sichtbar. Das ist der Grund, aus dem der Nutzer die
  Bitte überhaupt befolgt; eingeklappt wäre er wertlos.
- **Wie** (`how`), sofern der Agent es mitgegeben hat.
- Die Erfassung selbst nach **REQ-052 §2**, Profil `gallery` — dieselben drei Wege (Kamera, Datei,
  Zwischenablage), dieselbe Normalisierung, dieselbe Vorschau wie in §6.1. Diese Anforderung
  beschreibt keinen zweiten Erfassungsweg.

Ein Motiv darf **übersprungen** werden. Wer keine Blattunterseite fotografieren kann, weil die
Pflanze verschenkt ist, soll den Auftrag trotzdem abschließen können; ein Ablauf, der auf
Vollständigkeit besteht, wird stattdessen abgebrochen und liefert gar nichts. Übersprungene Motive
werden beim Abschluss benannt, damit der nächste Lauf weiß, dass sie nicht vergessen, sondern nicht
möglich waren.

**Abschicken ist eine Nutzerhandlung, und zwar dieselbe wie sonst.** Am Ende hängt der Nutzer die
aufgenommenen Fotos an den Eintrag und markiert ihn erneut zur Analyse — genau der Schalter aus
§6.1, mit genau derselben Serverprüfung. Es entsteht **kein** eigener „Nachforderung
abschicken"-Pfad, der an `can_request_analysis` und der Einwilligungsprüfung (REQ-050 §7.1)
vorbeiliefe. Der Auftrag gilt damit als erledigt.

Bricht der Nutzer ab, bleibt der Auftrag offen und der Eintrag unverändert. Nichts an der
Nachforderung setzt den Eintrag von selbst zurück (REQ-050 §2.6).

**Was passiert, wenn der Eintrag schon fünf Fotos trägt.** Dann ist er voll (REQ-013), und die
neuen Bilder haben keinen Platz. Der Ablauf sagt das **vor** der ersten Aufnahme, nicht nach der
letzten, und bietet an, Fotos des Eintrags zu entfernen. Erst danach beginnt die Erfassung. Ein
Ablauf, der den Nutzer erst fotografieren lässt und dann ablehnt, verliert genau die Arbeit, um
die gebeten wurde.

**Ist der Auftrag `superseded`** — ein neuer Lauf hat die Nachforderung ersetzt, während der Nutzer
sie offen hatte —, wird das beim Öffnen angezeigt und die aktuelle Nachforderung angeboten. Der
Nutzer fotografiert sonst nach einer Liste, die niemand mehr auswertet.

---

## 7. Client-Neutralität: Web und Mobile

### 7.1 Was die API zusagt

Die Fachlogik dieser Anforderung liegt vollständig hinter der REST-API. Verbindlich:

1. **Kein Client leitet eine Regel selbst ab.** Ob ein Nutzer markieren darf, entscheidet der
   Server und liefert es als `can_request_analysis` (REQ-050 §5). Dasselbe gilt für
   `analysis_outdated` (§4.1) und für `can_edit` (§8). Eine Regel, die zweimal existiert, wird
   beim nächsten Wechsel an einer Stelle vergessen — und dann verhalten sich Web und Mobile
   verschieden, ohne dass es jemandem auffällt.
2. **Kein Endpunkt setzt einen Browser voraus.** Keine Antwort verlangt eine Interpretation, die
   nur eine DOM-Umgebung leisten kann; alle Zeitstempel sind ISO-8601 mit Zeitzone; alle
   Auflistungen sind seitenweise mit `total`/`limit`/`offset`.
3. **Fehlende Werte kommen als `null`, nicht als ausgelassener Schlüssel.** Damit bleibt die
   Struktur über alle Zeilen gleich — für einen typisierten Client (Dart, TypeScript) ist das der
   Unterschied zwischen einem Feld und einem Sonderfall.
4. **Alle Oberflächentexte liegen in DE und EN vor**, DE ist Vorgabe und Rückfallsprache. Der
   Server liefert keine für den Nutzer bestimmten Sätze außer denen, die aus Daten stammen
   (Analyse-Zusammenfassung, Fehlertext des Agenten).

### 7.2 Was ein mobiler Client zusätzlich braucht

| Thema | Anforderung |
|-------|-------------|
| **Kamera** | Die Foto-Erfassung nutzt die native Kamera. Der Upload-Vertrag ist derselbe wie im Web (NFR-013): Der Client erhält eine `attachment_id` und referenziert sie; er kennt keine Storage-URL. |
| **Bandbreite** | Listen laden die **128-px**-Rendition, die Detailansicht die **512-px**-, die Lightbox die **1280-px**-Rendition. Ein Client lädt nie ein Original — im Mobilnetz ist das der Unterschied zwischen einer benutzbaren und einer unbenutzbaren Liste. |
| **Gleichzeitigkeit** | Telefon und Browser sind der Regelfall, nicht die Ausnahme. Beide Clients setzen `expected_content_version` (§3.7) und zeigen den `409` als Konflikt an. |
| **Bedienung mit einer Hand** | Die Erfassung ist die häufigste Handlung und muss ohne Zwischenschritt erreichbar sein. Bedienelemente folgen den Touch-Vorgaben aus `spec/ui-nfr/`. |
| **Unterbrochene Verbindung** | Ein abgebrochener Schreibvorgang darf keinen halben Eintrag hinterlassen. Anlegen ist eine Transaktion; ein Foto-Upload, dessen Eintrag nie geschrieben wurde, hinterlässt ein unreferenziertes Attachment, das NFR-013 aufräumt — nicht diese Anforderung. |
| **Zeitzone** | Der Client zeigt lokal an, sendet und empfängt aber in UTC. Ein Gerät, das im Urlaub die Zeitzone wechselt, darf die Reihenfolge der Einträge nicht verändern. |

### 7.3 Was ausdrücklich nicht zugesagt wird

**Kein Offline-Betrieb.** Es gibt keine lokale Entwurfsablage, keine Foto-Warteschlange und keine
Zusammenführung von Bearbeitungen, die ohne Verbindung entstanden sind. Der Grund ist nicht
Bequemlichkeit: Eine zusammengeführte Offline-Bearbeitung braucht eine Konfliktauflösung auf
Feldebene, und das Backend führt heute nichts, worauf sich eine solche stützen könnte — die
Inhaltsversion aus §3.6 erkennt einen Konflikt, sie löst ihn nicht auf. Ein halb umgesetzter
Offline-Modus ist schlechter als keiner, weil er Datenverlust erzeugt, den der Nutzer für
Synchronisation hält. Die Frage ist als O-54 geführt (§13).

Ein Client **darf** einen unabgeschickten Entwurf lokal halten, solange er ihn nicht als
gespeichert ausweist. Das ist eine Client-Entscheidung ohne Serverbeteiligung und keine Zusage
dieser Anforderung.

---

## 8. Datenmodell

Additive Felder an `PlantDiaryEntry` (`plant_diary_entries`). Alle mit Vorgabewert; bestehende
Einträge bleiben ohne Migration gültig.

| Feld | Typ | Vorgabe | Bedeutung |
|------|-----|---------|-----------|
| `content_version` | `int` | `1` | Inhaltsversion (§3.6) |
| `analysis_claimed_content_version` | `int \| None` | `None` | Inhaltsversion zum Zeitpunkt des Beanspruchens (§4.4) |

Ergänzung am eingebetteten Ergebnis `DiaryAnalysis` (REQ-050 §5):

```python
class DiaryAnalysis(BaseModel):
    # ... unverändert aus REQ-050 §5 ...
    #: Inhaltsversion, gegen die dieser Lauf gerechnet hat (REQ-051 §4.4).
    #: Serverseitig gesetzt; ein vom Agenten gelieferter Wert wird ignoriert.
    #: Fehlt der Wert an einem Bestandsdokument, wird er als 1 gelesen (§3.6).
    analyzed_content_version: int = 1
```

Neue Document-Collection `plant_diary_analyses` (§5.1):

```python
class DiaryAnalysisRecord(BaseModel):
    """Ein archivierter Analyselauf eines Tagebuch-Eintrags (REQ-051 §5)."""

    key: str | None = Field(default=None, alias="_key")
    tenant_key: str
    entry_key: str
    plant_key: str

    outcome: Literal["completed", "failed"]
    #: Bei ``failed`` ``None`` — dann trägt ``error`` die Ursache.
    analysis: DiaryAnalysis | None = None
    error: str | None = None
    analyzed_content_version: int

    requested_at: datetime | None = None
    requested_by: str | None = None
    claimed_at: datetime | None = None
    claimed_by: str | None = None
    #: Wann der Lauf archiviert wurde — der Zeitpunkt des Eintreffens (§5.2).
    #: Sortierschlüssel der Historie, weil ``analyzed_at`` vom Agenten kommt und
    #: damit weder monoton noch überprüfbar ist.
    recorded_at: datetime
```

**Index:** persistent über `(tenant_key, entry_key, recorded_at)`. Ohne ihn wird jede
Historie-Abfrage zum Sammelscan über die Läufe aller Einträge des Mandanten.

Zusätzliche, **nicht gespeicherte** Antwortfelder (an `DiaryEntryResponse` und
`DiaryOverviewItem`):

| Feld | Typ | Herleitung |
|------|-----|-----------|
| `content_version` | `int` | direkt |
| `analysis_outdated` | `bool` | `analysis.analyzed_content_version < content_version`; `false`, wenn kein Ergebnis vorliegt |
| `analysis_run_count` | `int` | Anzahl der Archiveinträge; steuert, ob die Historie angeboten wird (§5.3) |
| `can_edit` | `bool` | serverseitige Auswertung von §3.2 für den Nutzer *dieser* Anfrage |

`can_edit` hat aus demselben Grund keinen Vorgabewert wie `can_request_analysis` (REQ-050 §5):
dasselbe Dokument beantwortet es für den Verfasser mit `true` und für einen anderen Gärtner mit
`false`; ein Vorgabewert wäre genau der eine Wert, der für die Hälfte der Aufrufer falsch ist.

---

## 9. API-Endpunkte

Bestehende Endpunkte aus REQ-013 §4.7 bleiben unverändert. Beide Präfixe tragen dieselben
Handlungen:

```
/api/v1/planting-runs/{run_key}/plants/{plant_key}/diary...     (Run-Kontext)
/api/v1/t/{tenant_slug}/plant-instances/{plant_key}/diary...    (Standalone)
```

**Neu mit dieser Anforderung:**

| Methode | Pfad | Beschreibung | Auth |
|---------|------|-------------|------|
| `POST` | `.../diary/{entry_key}/capture-environment` | Umgebungs-Schnappschuss neu auflösen (§3.5) | Ab Gärtner, §3.2 |
| `GET` | `.../diary/{entry_key}/analyses` | Archivierte Läufe, absteigend nach `recorded_at`, seitenweise | Alle Rollen |

**Geändert:**

| Methode | Pfad | Änderung |
|---------|------|----------|
| `PUT` | `.../diary/{entry_key}` | nimmt optional `expected_content_version` entgegen; bei Abweichung `409 conflict.stale_write` (§3.7) |
| `GET` | `/api/v1/t/{slug}/diary` | zusätzlicher Filter `analysis_outdated`; die Zeile trägt vier neue Felder — siehe §9.1 |

### 9.1 Die mandantenweite Übersicht

> Übernommen aus REQ-050 v1.4 §2.5.2, ergänzt um die Felder dieser Anforderung.

```
GET /api/v1/t/{tenant_slug}/diary
```

| Parameter | Typ | Bedeutung |
|-----------|-----|-----------|
| `analysis_state` | `list[DiaryAnalysisState] \| None` | Filter, mehrfach angebbar |
| `analysis_outdated` | `bool \| None` | **neu** — „nur veraltete Ergebnisse" (§6.2, AK-41) |
| `plant_key`, `species_key` | `str \| None` | Filter |
| `entry_type`, `tag` | `str \| None` | Filter |
| `from`, `to` | `date \| None` | Zeitraum über `created_at` |
| `q` | `str \| None` | Freitextsuche über Titel und Text |
| `sort` | `'created_at' \| 'analyzed_at'` (Vorgabe `created_at`) | Sortierung, absteigend |
| `limit`, `offset` | `int` | Seitenweise, Vorgabe 50 |

**Die Zeile ist nicht `DiaryEntryResponse`.** Sie trägt vom Analyse-Ergebnis **nur** die
Zusammenfassung. Andernfalls transportierte eine Seite mit 50 Zeilen 50 vollständige Befundlisten
samt Begründungen für eine Ansicht, die davon eine Zeile anzeigt. Das vollständige Ergebnis
liefert der Einzelabruf, die Historie `GET .../diary/{entry_key}/analyses`.

```python
class DiaryOverviewItem(BaseModel):
    """Eine Zeile der mandantenweiten Tagebuch-Übersicht (REQ-051 §6.2)."""

    key: str
    created_at: datetime | None            # nullable wie am Datensatz, siehe unten
    entry_type: DiaryEntryType
    title: str | None
    excerpt: str = Field(max_length=200)      # Anfang von `text`, serverseitig gekürzt
    tags: list[str]

    plant_key: str
    plant_name: str | None
    instance_id: str
    species_name: str | None

    photo_count: int
    preview_photo_id: str | None              # erstes Foto, für die Miniatur

    analysis_state: DiaryAnalysisState        # der ANGEZEIGTE Zustand, REQ-050 §5
    analysis_summary: str | None              # NUR die Zusammenfassung, nie `findings`
    analysis_error: str | None
    analysis_claimed_at: datetime | None       # Beginn des Lease, nicht sein Abschluss
    analyzed_at: datetime | None

    can_request_analysis: bool                # REQ-050 §7.2, serverseitig ausgewertet

    # ── neu mit REQ-051 ───────────────────────────────────────────────────────
    content_version: int
    analysis_outdated: bool                   # §4.1
    analysis_run_count: int                   # §5.3 — steuert, ob Historie angeboten wird
    can_edit: bool                            # §3.2, serverseitig ausgewertet


class DiaryOverviewResponse(BaseModel):
    items: list[DiaryOverviewItem]
    total: int                                # Treffer über alle Seiten
    limit: int
    offset: int
```

Drei Verhaltensregeln der Zeile stammen aus REQ-050 und gelten unverändert:

- **`analysis_state` ist der *angezeigte* Zustand.** Ist das Agenten-Lease abgelaufen, liest sich
  der Eintrag überall als `requested`, obwohl `in_progress` gespeichert ist (REQ-050 §5, AK-06).
  Der Filter folgt derselben Korrektur — „nur wartend" findet den Eintrag eines abgestürzten
  Agenten. Lesen schreibt nichts.
- **`analysis_claimed_at` gehört zu dem Lauf, den der angezeigte Zustand beschreibt**, und wird
  bei abgelaufenem Lease auf `null` unterdrückt. Die Oberfläche zeigt ihn als Tatsache, nie als
  Laufzeit — ein mitlaufendes „läuft seit 14 Minuten" wäre die Andeutung eines Fortschritts, den
  REQ-050 §3 ausdrücklich nicht zusagt.
- **`created_at` ist bewusst `datetime | None`.** Ein einziges Altdokument ohne Zeitstempel würde
  eine nicht-nullable Zeile beim Serialisieren sprengen und damit die **ganze** Übersichtsseite in
  einen 500 verwandeln. Ein `null` in einer Zelle ist der ehrliche und der billigere Ausgang.

Die Liste ist strikt auf `tenant_key` gefiltert. Für die Zustandsfilter ist derselbe persistente
Index nötig, den auch der MCP-Arbeitsvorrat braucht (REQ-050 §5):
`(tenant_key, analysis_state, analysis_requested_at)`.

**`analysis_outdated` ist ein abgeleiteter Filter, kein indiziertes Feld.** Er vergleicht zwei
Zahlen desselben Dokuments (§4.1) und ist damit nicht über einen Sekundärindex bedienbar. Für die
heutige Größenordnung — Tagebuch-Einträge eines Mandanten — ist das unkritisch, solange er **nach**
den indizierten Filtern greift und nicht als einziges Kriterium eines Sammelscans steht. Die
Umsetzung muss ihn entsprechend anordnen.

### 9.2 Rumpf des Umgebungs-Endpunkts

`POST .../capture-environment` hat **keinen Rumpf**. Es ist die Erlaubnis zu schauen, nie der
Inhalt — dieselbe Begründung, aus der `DiaryEntryCreateRequest` nur `capture_environment: bool`
trägt (REQ-013 §2.3a.8). Die Antwort ist der vollständige, aktualisierte Eintrag, damit der Client
`environment_status` und die neue `content_version` ohne zweiten Abruf hat.

**Fehlerbehandlung** folgt NFR-006. Ein Eintrag aus einem fremden Mandanten antwortet `404`, nie
`403` — sonst bestätigte die Antwort die Existenz eines fremden Schlüssels (REQ-050 AK-12,
dieselbe Regel).

---

## 10. Berechtigungen

Vokabular gemäß REQ-049 §3.1: Beobachter → Gärtner → Leitung.

| Handlung | Beobachter | Gärtner | Leitung |
|----------|-----------|---------|---------|
| Eintrag und Analyse-Ergebnis lesen | ✓ | ✓ | ✓ |
| Analyse-Historie lesen (§5.3) | ✓ | ✓ | ✓ |
| Übersicht öffnen (§6.2) | ✓ | ✓ | ✓ |
| Eintrag anlegen | ✗ | ✓ | ✓ |
| Eintrag bearbeiten | ✗ | ✓ (nur eigene) | ✓ |
| Fotos ergänzen / entfernen | ✗ | ✓ (nur eigene) | ✓ |
| Umgebung neu erfassen | ✗ | ✓ (nur eigene) | ✓ |
| Eintrag löschen | ✗ | **✗** | ✓ |
| Zur Analyse markieren | ✗ | ✓ (nur eigene) | ✓ |

Die Rollenprüfung läuft über die vorhandenen Abhängigkeiten aus `app/common/auth.py`
(`require_permission` für Anlegen/Ändern/Löschen), die auf den reinen Prädikaten der
`MembershipEngine` entscheiden — `can_edit_resource` (Leitung/Gärtner) für Anlegen und Ändern,
`can_delete_resource` (**nur Leitung**) für Löschen. Die zusätzliche Einschränkung „nur eigene"
ist **keine** Rollenfrage und liegt deshalb nicht dort, sondern als eigene Prüfung am Dienst;
REQ-050 §7.2 führt sie bereits so für das Markieren.

Die beiden Prüfungen sind bewusst getrennt und dürfen nicht zusammengelegt werden: Die
Rollenprüfung ist auch die Autorität für die MCP-Oberfläche und die Anhang-Wache
(`app/core/permissions.py`), die Autorschaftsprüfung gilt nur für Tagebuch-Einträge. Eine
Zusammenlegung zöge die Tagebuch-Sonderregel in eine Tabelle, die 27 andere Ressourcen mitgates.

---

## 11. Datenschutz

- **Bearbeitung erzeugt keine neue Verarbeitung.** Ein bearbeiteter Eintrag bleibt derselbe
  Datensatz mit demselben Zweck. Die Einwilligung `diary_ai_analysis` (REQ-025) gilt weiterhin je
  Markierung, nicht je Eintrag: Wer einen analysierten Eintrag bearbeitet und erneut analysieren
  lässt, markiert erneut und braucht die Einwilligung erneut (sie ist zu diesem Zeitpunkt zu
  prüfen, nicht die von damals).
- **Widerruf der Einwilligung** verhindert neue Markierungen und lässt vorhandene Ergebnisse
  unberührt — im Archiv wie am Eintrag. Ein Widerruf ist kein Löschbegehren; wer die Ergebnisse
  entfernt haben will, löscht den Eintrag oder verlangt Löschung nach Art. 17.
- **Erasure (Art. 17).** In Erasure-Phase 2 werden zusätzlich zu den in REQ-025 AK-DA-01 genannten
  Feldern in `plant_diary_analyses` die Felder `requested_by` und `claimed_by` auf `_anonymized`
  gesetzt. Der Lauf selbst bleibt erhalten — dieselbe Abwägung wie beim Eintragsdokument: Er
  gehört zum Pflanzen-Datensatz eines womöglich geteilten Mandanten (AK-48).
- **Auskunft (Art. 15/20).** Der Datenexport umfasst die archivierten Läufe, nicht nur das jüngste
  Ergebnis (AK-49).
- **Der Umgebungs-Schnappschuss ist datenschutzrelevant.** REQ-025 führt CO₂- und
  Bewegungsmesswerte als Daten, die Anwesenheitsmuster offenlegen können (DSFA-pflichtig). Eine
  erneute Erfassung nach §3.5 fügt einem Eintrag Werte hinzu, die er vorher nicht hatte, und
  unterliegt denselben Aufbewahrungsregeln wie die Erfassung beim Anlegen. Sie ist eine
  Nutzerhandlung und kein Automatismus — genau deshalb gibt es keinen Regelsatz, der
  Schnappschüsse nachträglich flächig nachträgt.
- **Im Light-Modus** (REQ-027) entfällt die Einwilligungsprüfung und die Einschränkung „nur
  eigene", weil alle Einträge demselben System-Nutzer gehören (REQ-050 §7.5).

---

## 12. Akzeptanzkriterien

### Übernommen aus REQ-050 v1.4 (Nummern unverändert)

| ID | Kriterium |
|----|-----------|
| **AK-14** | Auf der Pflanzeninstanz-Detailseite gibt es einen Tagebuch-Tab, in dem ein Eintrag mit Typ, Titel, Freitext, Tags, Messwerten und bis zu 5 Fotos angelegt, bearbeitet, gelöscht (Löschen ab Rolle Leitung, §3.2/AK-56 — einem Gärtner wird die Handlung nicht angeboten) und zur Analyse markiert werden kann (§6.1). |
| **AK-15** | Eine mandantenweite Tagebuch-Übersicht listet die Einträge **aller** Pflanzen chronologisch absteigend mit Pflanze, Art, Typ, Titel/Auszug, Fotoanzahl und Analyse-Zustand (§6.2). |
| **AK-16** | Die Übersicht unterscheidet alle fünf Analyse-Zustände sichtbar voneinander; `completed` ist als „Ergebnis vorhanden" hervorgehoben und zeigt die Zusammenfassung als Vorschau. |
| **AK-17** | Die Übersicht lässt sich nach Analyse-Zustand filtern — insbesondere „nur mit Ergebnis" und „nur wartend" — sowie nach Pflanze, Art, Typ, Tag und Zeitraum; die Freitextsuche greift auf Titel und Text. |
| **AK-19** | Ein Nutzer kann in einem geteilten Mandanten nur eigene Einträge markieren und bearbeiten, sofern er nicht die Rolle Leitung hat; fremde Zeilen der Übersicht zeigen den Zustand, aber keinen Schalter. |
| **AK-20** | Der Vorbehalt ist in der Ergebnisdarstellung immer sichtbar und nicht hinter einem Aufklapp-Element versteckt. |
| **AK-28** | Alle Oberflächentexte liegen in DE und EN vor; DE ist Vorgabe und Rückfallsprache. |
| **AK-29** | Die Übersicht bietet eine Auffrischen-Schaltfläche und lädt den Zustand beim Öffnen nach. Es gibt keinen Server-zu-Client-Kanal und keine Fortschrittsanzeige für `requested` (§6.5). |
| **AK-30** | Die Konfidenz eines Befunds wird als Zahl **und** sprachlich eingeordnet dargestellt — eine nackte Prozentzahl allein erfüllt das Kriterium nicht (§6.4). |
| **AK-31** | Die Tagebuch-Übersicht ist als Modul in REQ-042 registriert und in der Navigations-Zuordnung von REQ-021 eingeordnet. |

### Neu mit dieser Anforderung

| ID | Kriterium |
|----|-----------|
| **AK-40** | Wird ein Eintrag mit vorhandenem Analyse-Ergebnis bearbeitet, liefern Einzelabruf **und** Übersichtszeile `analysis_outdated: true`; `analysis_state` bleibt dabei unverändert `completed` bzw. `failed`. Die Oberfläche zeigt den Hinweis **über** der Zusammenfassung, mit der Handlung „erneut analysieren" daneben. |
| **AK-41** | Die Übersicht lässt sich auf veraltete Ergebnisse filtern. Der Filter findet genau die Einträge, die **ein Ergebnis haben** und deren `analyzed_content_version` kleiner ist als ihre `content_version`. Ein nie analysierter, aber bearbeiteter Eintrag darf **nicht** erscheinen — ohne die erste Bedingung wäre eine Liste „nur mit veraltetem Ergebnis" voller Einträge ohne jedes Ergebnis (§4.1, §8). |
| **AK-42** | Der Bearbeitungsdialog weist vor dem Speichern darauf hin, dass ein vorhandenes Ergebnis als nicht mehr aktuell gekennzeichnet wird. Der Hinweis erscheint nur, wenn tatsächlich ein Ergebnis vorliegt, und verhindert das Speichern nicht. |
| **AK-43** | `POST .../capture-environment` löst den Schnappschuss serverseitig neu auf, setzt `environment`, `environment_captured_at` und `environment_status` und erhöht `content_version`. Weicht `environment_captured_at` um mehr als `DIARY_SNAPSHOT_MAX_LAG_MINUTES` von `created_at` ab, weist die Oberfläche darauf hin — **nicht** um mehr als `DIARY_ENVIRONMENT_MAX_AGE_MINUTES`, das eine andere Größe misst (§3.5). |
| **AK-44** | Steht `environment_status` auf `captured`, verlangt die Oberfläche vor der erneuten Erfassung eine Bestätigung, die benennt, dass der vorhandene Schnappschuss ersetzt wird. |
| **AK-45** | Jeder eintreffende Analyselauf — `completed` **und** `failed` — erzeugt einen Datensatz in `plant_diary_analyses`. `GET .../diary/{entry_key}/analyses` liefert sie absteigend nach `recorded_at`, seitenweise. Die Oberfläche bietet die Historie erst an, wenn mehr als ein Lauf existiert. |
| **AK-46** | `content_version` wird an genau einer Stelle erhöht. Ein Test weist die **Abwesenheit** eines zweiten Schreibpfads nach: kein Modul außerhalb von `PlantDiaryService` schreibt `plant_diary_entries`. Der Test muss rot werden, wenn ein solcher Pfad eingefügt wird — die Gegenprobe ist Bestandteil der Umsetzung. |
| **AK-47** | Ein `PUT` mit `expected_content_version`, die vom gespeicherten Wert abweicht, antwortet `409 conflict.stale_write`, schreibt **nichts** und liefert die aktuelle `content_version` mit. Ohne das Feld gilt das bisherige Verhalten. Beide Clients setzen das Feld. |
| **AK-48** | Nach einem Erasure-Request sind in `plant_diary_analyses` die Felder `requested_by` und `claimed_by` auf `_anonymized` gesetzt; der Lauf selbst bleibt vollständig erhalten. |
| **AK-49** | Die Datenauskunft nach Art. 15/20 enthält die archivierten Analyseläufe, nicht nur das jüngste Ergebnis. |
| **AK-50** | Löschen eines Tagebuch-Eintrags löscht seine Archiveinträge; nach dem Löschen der Pflanze existiert weder Eintrag noch Archiv. Ein verwaister Archiveintrag ist ein Fehlschlag des Kriteriums. |
| **AK-51** | Bestandsdokumente ohne `content_version` bzw. ohne `analyzed_content_version` bleiben ohne Migration lesbar und schreibbar; beide werden als `1` gelesen, und ein solcher Eintrag gilt als **nicht** veraltet, solange er nicht bearbeitet wurde. |
| **AK-52** | Wird ein Eintrag im Zustand `in_progress` bearbeitet, wird das später eintreffende Ergebnis angenommen, archiviert und als veraltet gekennzeichnet — es wird weder verworfen noch als aktuell ausgewiesen. Ein vom Agenten mitgeschicktes `analyzed_content_version` wird ignoriert. |
| **AK-53** | Der Versuch, `environment`, `environment_captured_at`, `environment_status` oder ein Analysefeld über `PUT .../diary/{entry_key}` zu setzen, verändert diese Felder nicht. |
| **AK-54** | Eine sechste Foto-Referenz wird mit `validation.error` abgewiesen; die Liste wird **nie** still gekürzt. |
| **AK-55** | Alle in §9 genannten Antworten liefern fehlende Werte als `null` statt als ausgelassenen Schlüssel, und alle Zeitstempel als ISO-8601 mit Zeitzone. |
| **AK-56** | Ein Gärtner kann seinen **eigenen** Tagebuch-Eintrag bearbeiten, aber **nicht** löschen (`permission.denied`); die Rolle Leitung kann beides, auch an fremden Einträgen; ein Beobachter kann keines von beidem. Die Oberfläche zeigt einem Gärtner keine Löschen-Handlung an — ein Schalter, der immer abgewiesen wird, ist eine Fähigkeit, die es nicht gibt. |
| **AK-57** | Jeder Endpunkt aus §9 antwortet auf einen Schlüssel aus einem fremden Mandanten mit `404`, nie mit `403` — einschließlich `POST .../capture-environment` und `GET .../analyses`. Eine fremde Pflanze liefert **nie** einen leeren Umgebungs-Schnappschuss als Antwort, weil auch der die Existenz des Schlüssels bestätigte (§2.4.2). |
| **AK-58** | Im geteilten Mandanten wird `POST .../capture-environment` auf einem **fremden** Eintrag mit `permission.denied` abgewiesen, obwohl derselbe Eintrag für denselben Nutzer lesbar ist; mit der Rolle Leitung gelingt er. Lesen und Ändern folgen getrennten Achsen (§2.4.3). |

---

## 13. Offene Punkte

| Nr. | Frage | Entscheider | Status |
|-----|-------|-------------|--------|
| O-51 | Soll die erneute Erfassung des Umgebungs-Schnappschusses auf Einträge beschränkt werden, deren `environment_status` **nicht** `captured` ist — also als reiner Wiederholungsversuch statt als Ersetzung? v1.0 erlaubt sie immer und sichert sie über eine Bestätigung ab (§3.5, AK-44). | Produkt | offen |
| O-52 | Soll auch der **Inhalt** eines Eintrags versioniert werden (frühere Textfassungen, ersetzte Messwerte, ausgetauschte Fotos), oder bleibt die Historie auf Analyseläufe beschränkt? v1.0 archiviert nur Analysen. | Produkt | offen |
| O-53 | Ab wann wird `expected_content_version` **verpflichtend**? Der optionale Zustand ist eine Übergangsregel für vorhandene Aufrufer, kein Ziel (§3.7). | Produkt + Entwicklung | offen |
| O-54 | Soll der mobile Client Offline-Erfassung mit Synchronisation bekommen? v1.0 sagt sie ausdrücklich **nicht** zu (§7.3); die Entscheidung braucht ein Konfliktmodell auf Feldebene, das heute nirgends existiert. | Produkt | offen |
| O-55 | Soll das Archiv eine Obergrenze bekommen (z. B. die letzten 50 Läufe je Eintrag)? Unbegrenzt ist heute unproblematisch, weil jeder Lauf eine Nutzerhandlung voraussetzt; ein fehlgeleitetes Agenten-Rezept, das im Minutentakt neu analysiert, wäre der Fall, der sie nötig macht. | DevOps | offen |
| O-56 | Soll ein Befund aus einem archivierten Lauf mit dem aktuellen **verglichen** werden können („was hat sich seit dem Umtopfen geändert")? Das ist der eigentliche Grund, zweimal zu analysieren, und v1.0 liefert dafür nur die beiden Listen nebeneinander. | Produkt | offen |
| O-57 | Soll ein Gärtner seinen **eigenen** Tagebuch-Eintrag löschen dürfen? v1.0 verneint das und folgt damit REQ-049 §2.3 ohne Ausnahme (§3.2); die vollständige Bearbeitung deckt den Korrekturfall ab, das Leeren eines versehentlichen Eintrags bleibt aber unbefriedigend. Eine Lockerung wäre nicht die erste Ausnahme — REQ-024 AK-35 (eigener Pinnwand-Beitrag) und REQ-006 (eigener Aufgaben-Kommentar) haben je eine, beide gedeckt durch REQ-049 §3.1 „verfasste Inhalte". Der Tagebuch-Eintrag ist nach §3.2 dieselbe Kategorie; die Frage ist deshalb, warum das **Löschen** hier anders behandelt wird als das Bearbeiten, nicht ob eine Ausnahme zulässig wäre. | Produkt | offen |
| O-58 | Soll das **Analyse-Archiv** im geteilten Mandanten für alle Mitglieder vollständig lesbar sein? v1.0 sagt ja (§5.3, konsistent zu REQ-050 §6). Die Übersicht zeigt fremden Zeilen nur die Zusammenfassung; die Historie liefert dagegen jedem Mitglied die vollständigen Befunde samt Begründungen aller Läufe aller anderen — dieselbe Rechtsgrundlage, aber ein Vielfaches der Menge. | Produkt + Datenschutz | offen |

---

**Dokumenten-Ende**
**Version:** 1.0
**Status:** Entwurf
