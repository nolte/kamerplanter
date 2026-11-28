---
number: 5
status: planned
started: null
ended: null
value_statement: Plattform-Admins stellen einen Garten aus seinem Archiv vollständig wieder her – samt Sensor-Historie im Rahmen der Aufbewahrungsfristen, nach einer Vorprüfung mit Mitgliederzuordnung per E-Mail und bis zu einer Archivgröße von etwa 500 MiB.
artifact_ref: null
last_commit: null
roadmap_items: [R-19]
features: [F-15, F-32, F-17, F-33, F-16, F-34]
---

## Goal

Export und Import eines Mandanten sind geliefert, stellen einen Garten aber
nur bis rund 50 MiB und ohne Sensor-Historie wieder her; die Mitglieder ordnet
der Admin über abgetippte Schlüssel zu, und ein verändertes Archiv kann Werte
einspielen, die spätere Lesezugriffe brechen. Nach diesem Sprint kommen
Archive bis etwa 500 MiB durch (F-15), der Hintergrundprozess prüft jeden
Datensatz gegen das Datenmodell (F-32), der Admin sieht vor dem Import eine
Vorschau und ordnet die Mitglieder per E-Mail zu (F-17), findet frühere
Importe in einer Liste (F-33), und die Sensor-Historie wird im Rahmen der
Aufbewahrungsfristen der Installation mit wiederhergestellt: Rohwerte (F-16)
sowie Stunden- und Tageswerte (F-34) (R-19, Issue #3140). Was älter ist als
die Fristen (Rohwerte 90 Tage, Stundenwerte 2 Jahre, Tageswerte 5 Jahre),
kommt nicht zurück; der Importbericht nennt die Zahl.

Umsetzungsreihenfolge: **F-15 → F-32 → F-17 → F-33 → F-16 → F-34**, streng
seriell; alle sechs ändern `tenant_export_service.py`. Begründung aus den
Abhängigkeiten der Feature-Dateien:

- F-15 hängt von keinem der anderen ab und liefert, worauf die übrigen bauen:
  die Prüfung nur noch im Hintergrundprozess, die Ablehnungsdetails am
  Import-Datensatz, den Audit-Eintrag früher Ablehnungen und die Größenwerte.
- F-32 fügt der Hintergrundprüfung die Dokumentprüfung hinzu und schreibt ihre
  Befunde in das Detailfeld aus F-15. Es steht vor F-17, weil die Vorprüfung
  sein Ergebnis zeigen soll und ein Lauf mit einem echten Garten vor dem
  Merge von F-32 klärt, ob eigene Archive bestehen.
- F-17 baut auf der Hintergrundprüfung aus F-15: Vorschau, Bestätigung,
  Zuordnung, Start.
- F-33 listet die Datensätze, die F-17 anlegt, und regelt ihren Ablauf; es
  kann nicht vor F-17 stehen.
- F-16 braucht die Vorprüfung (eine falsche Prüfsumme des Messwert-Teils
  scheitert dort) und die Liste aus F-33 für die Phase „Messwerte“. Es
  schreibt die Rohwerte, lässt ihren Zeitraum neu berechnen und behebt die
  Lücke beim Löschen von Messwerten (Entscheidung F).
- F-34 schreibt mit der Sensor-Zuordnung aus F-16 die älteren Stunden- und
  Tageswerte, lässt die Tageswerte ihres Zeitraums neu berechnen und steht
  zuletzt; es trägt den Rundlauf.

Der value-verifizierende Nachweis ist **F-34 `acceptance-6`**: Ein Garten mit
Datensätzen, Fotos, Mitgliedern, Sensoren und Messwerten wird exportiert, das
Archiv hochgeladen, vorgeprüft, die Mitglieder per E-Mail zugeordnet und aus
der Vorprüfung importiert; der erneute Export des neuen Gartens enthält
dieselben Daten einschließlich der Sensor-Historie im Rahmen der
Aufbewahrungsfristen. Das Kriterium liegt im letzten Feature der
Kette und läuft durch alle sechs. Ein früheres Kriterium wiese die
Vollständigkeit nicht nach, weil bis F-34 die Stunden- und Tageswerte fehlen.
Nicht nachgewiesen wird damit die Größe von rund 500 MiB.

**Verpflichtender Handlauf (Betreiberentscheidung 2026-11-28).** Der Teil
„bis zu einer Archivgröße von etwa 500 MiB“ des Wertsatzes bleibt (der Satz
ist durch E um die Aufbewahrungsfristen präzisiert); die Größe weist der
Handlauf zu F-15 `acceptance-1` nach.
Der Sprint schließt nicht ohne bestandenen Handlauf: Der Hook zu F-15
`acceptance-1` darf nur mit `passing` enden, nie mit `skipped`. Der Betreiber
(oder die Hauptsitzung in seinem Auftrag) startet dazu den
`workflow_dispatch`-Lauf gegen die Testinstallation, mit den mitgelieferten
Helm-Werten: Export eines fotolastigen Gartens von rund 500 MiB mit
realistischer Objektzahl (einige Hundert Fotos von je rund 1 MiB), Import des
Archivs, einmal über die Admin-Seite hochgeladen. Der Import braucht eine
zweite ArangoDB-Datenbank oder einen Quell-Garten ohne eigene Arten, weil ein
Import neben dem Original an eigenen Arten scheitert. Dieselbe Voraussetzung
(zwei ArangoDB-Datenbanken) gilt für den Wertnachweis F-34 `acceptance-6`.

Betreiberentscheidungen vom 2026-11-27:

- **Sprint 5 enthält nur R-19.**
- **D1:** Archivfehler erscheinen als fehlgeschlagene Vorprüfung in der
  Importliste (F-33); Ablehnungen vor dem Speichern (Rolle, Größe, Step-up)
  stehen nur im Audit. Das stimmt seit der Entscheidung C vom 2026-11-28, mit
  der F-15 diese Ablehnungen auditiert; ausgenommen bleiben Anfragen, die
  schon Proxy oder Middleware mit 413 abweist oder die nicht angemeldet sind.
- **D2:** Die Step-up-Bestätigung der Vorprüfung gilt eine Stunde für den
  anschließenden Import und ist an denselben Admin gebunden; danach oder für
  einen anderen Admin ist ein neuer Step-up nötig (F-17).
- **Dokumentvalidierung nach REQ-056 §12.4:** eigenes kleines Feature in R-19
  (F-32). Die Prüfung läuft im Hintergrundprozess, die Vorprüfung zeigt das
  Ergebnis, ein manipulierter Wert wird abgelehnt statt geschrieben.
- **F-15 Kriterium 4, Option B:** Synchron bleiben Rolle, Größe, Step-up,
  „Plan vorhanden“ und E-Mail → Konto; alles Übrige läuft asynchron; die
  Ablehnungsdetails werden am Import-Datensatz gespeichert; REQ-056 §8.4,
  AK-34, AK-46 und die Runbook-Tabelle werden nachgezogen.
- **Upload-Temp-Speicher:** `/tmp` des Backends liegt auf Disk (Volume im
  Helm-Chart) und wird nicht speicherbasiert vergrößert.
- **Reihenfolge:** F-15 → Dokumentvalidierung → F-17 → F-16 (am 2026-11-28
  durch die Teilung zu sechs Features verfeinert, Abfolge unverändert).
- Weiter gültig aus derselben Runde: nur eine Installation, der 500-MiB-Test
  läuft nur manuell (`workflow_dispatch`), das Speicherlimit des Workers von
  rund 2 GiB ist akzeptabel, die Datenschutz-Befunde zum Archiv laufen in
  einer eigenen Lane.

Betreiberentscheidungen vom 2026-11-28:

- **Messwerte ohne zuordenbaren Sensor** werden ausgelassen und gezählt, auch
  die Stunden- und Tageswerte eines solchen Sensors (F-16, F-34).
- **`/tmp` des Workers** liegt auch auf Disk (F-15).
- **Archivierte Stunden- und Tageswerte werden direkt geschrieben** (F-34).
  Der Zusatz „nichts wird neu berechnet“ ist durch D ersetzt.
- **Sprintwert:** Der 500-MiB-Teil des Satzes bleibt, der Handlauf mit rund
  500 MiB ist verpflichtend (oben); präzisiert durch E.
- **A — Teilung:** F-17 in „Vorprüfung und Start“ (F-17) und „Importliste und
  Ablauf“ (F-33); F-16 in „Rohwerte und Bericht“ (F-16) und „Stunden- und
  Tageswerte“ (F-34).
- **B — Zweiter Admin:** Wer startet, handelt (Audit-Akteur,
  Ersatz-Eigentümer); der Hochladende bleibt am Datensatz. Die
  Mitgliedernamen sieht jeder Admin nur nach eigener, frischer Bestätigung
  (höchstens eine Stunde) für dieses Archiv, über eine eigene Route nur zum
  Bestätigen (F-17).
- **C — Audit für früh abgelehnte Uploads:** ja, als Teil von F-15.
- **D — Der Import lässt am Ende gezielt neu berechnen:** genau die
  eingespielten Zeiträume, erst Stunden-, dann Tageswerte (F-16, F-34).
- **E — Sprintwert präzisiert:** „samt Sensor-Historie im Rahmen der
  Aufbewahrungsfristen“; der Handlauf bleibt Pflicht.
- **F — Die Löschlücke wird in F-16 mit behoben:** Jedes Löschen von
  Rohwerten (Sensor, Mandant, Rückrollen eines Imports, Aufräumen
  abgebrochener Importe) berechnet seinen Zeitraum unmittelbar gezielt neu,
  an einer Stelle im Datenzugriff.

Vorgaben der Hauptsitzung vom 2026-11-28, nach ihren Messungen gegen
TimescaleDB 2.32.1-pg16: Was älter ist als die Aufbewahrungsfrist seiner
Ebene (Rohwerte, Stundenwerte, Tageswerte), wird nicht eingespielt, sondern
gezählt, mit Schnitt an einer Tagesgrenze (F-16, F-34); nach dem Import
ändert ein volles Neuberechnen keinen Wert irgendeines Mandanten (F-16,
F-34); der Import berechnet vor dem Schreiben der Stunden- und Tageswerte
genau die Zeiträume neu, die er beschreibt, damit die Werte auch in einer
Installation erhalten bleiben, die bisher nur Policy-Läufe gesehen hat
(F-34 `acceptance-4`); ungültige Angaben in `tenant.json` werden abgelehnt
statt ersetzt (F-32).

Festlegungen der Planung vom 2026-11-28, nicht vom Betreiber entschieden und
vor dem Start des jeweiligen Features widerrufbar (Einzelheiten unter „Offene
Punkte“ der Feature-Dateien): der Upload-Pfad bleibt, neu sind die Routen zum
Bestätigen und Starten (F-17) und die Liste (F-33); die Mitgliedervorschau
liegt am Import-Datensatz; eine Vorprüfung bleibt nach einem gescheiterten
Lauf bis zu ihrem Ablauf startbar (F-17); jedes an eine Collection gebundene
Modell muss einen Datensatz annehmen (F-32); eine falsche Prüfsumme des
Messwert-Teils scheitert schon in der Vorprüfung (F-16); das Neuberechnen
des Rohwert-Zeitraums liegt schon in F-16, abweichend von der Vorgabe der
Hauptsitzung, damit zwischen F-16 und F-34 keine Vormerkung offen bleibt
(F-16); die Grenze von 1 MiB für `manifest.json` bleibt, der Export lehnt
ab (F-15).

Aus dem Repository und den Messungen nicht belegt, durch Integrationstests
zu klären (F-34 `acceptance-4`): ob das begrenzte Neuberechnen vor dem
Schreiben wirkt wie das gemessene volle und was in einer leeren
Zielinstallation gilt. Alte Vormerkungen aus früheren Löschungen: gemessen,
Semantik einzelner Einträge offen. Sie sind im Katalog der
Zeitreihendatenbank lesbar; der Import bricht ab, bevor er schreibt, wenn in
seinen Zielzeiträumen eine liegt, die sich aus Rohwerten nicht mehr heilen
lässt (F-34 `acceptance-8`). Offen ist, wie sich eine solche Vormerkung vom
Normalzustand eines nie voll neu berechneten Aggregats unterscheiden lässt
und was der Betreiber nach einem Abbruch tut (F-34, „Offene Punkte“). Offen für den Betreiber, ohne
ein Feature zu blockieren: ob die Grenze für `manifest.json` steigen soll
(F-15).

## Features

- [F-15](../features/tenant-archive-size-limits.md) — status: ready
- [F-32](../features/tenant-import-document-validation.md) — status: ready
- [F-17](../features/tenant-import-preflight.md) — status: ready
- [F-33](../features/tenant-import-list.md) — status: ready
- [F-16](../features/tenant-readings-import.md) — status: ready
- [F-34](../features/tenant-readings-aggregates-import.md) — status: ready

## Out of scope

- R-27 (gemessener Regen und Bewässerung, F-28 bis F-31) — kommt in Sprint 6.
- Kc-Tabelle (#3160) — danach.
- Heben älterer Archive durch Migrationen (REQ-056 §8.4 Schritt 1) — hat keinen Besitzer; nach F-32 werden solche Archive abgelehnt statt fehlerhaft importiert.
- Messwerte außerhalb der Aufbewahrungsfristen der Zielinstallation (Rohwerte 90 Tage, Stundenwerte 2 Jahre, Tageswerte 5 Jahre) — werden gezählt, nicht eingespielt.
- Eine höhere Grenze für `manifest.json` (Gärten mit vielen Tausend Dateien).
- Die Datenschutz-Befunde zum Archiv (Abgleich mit abgeschlossenen Löschungen, `anon_`-Pseudonyme, GPS-Genauigkeit) — eigene Lane.
- Umzug eines Mandanten zwischen Installationen; es gibt nur eine Installation.
- Ein automatischer 500-MiB-Test je Pull Request oder nachts.

## Review notes

_Populated by `sprint-review` at closure._
