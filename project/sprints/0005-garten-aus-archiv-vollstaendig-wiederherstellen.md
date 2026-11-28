---
number: 5
status: planned
started: null
ended: null
value_statement: Plattform-Admins stellen einen Garten aus seinem Archiv vollständig wieder her – samt Sensor-Historie, nach einer Vorprüfung mit Mitgliederzuordnung per E-Mail und bis zu einer Archivgröße von etwa 500 MiB.
artifact_ref: null
last_commit: null
roadmap_items: [R-19]
features: [F-15, F-32, F-17, F-16]
---

## Goal

Export und Import eines Mandanten sind geliefert, stellen einen Garten aber
nur bis rund 50 MiB und ohne Sensor-Historie wieder her; die Mitglieder ordnet
der Admin über abgetippte Schlüssel zu, und ein verändertes Archiv kann Werte
einspielen, die spätere Lesezugriffe brechen. Nach diesem Sprint kommen
Archive bis etwa 500 MiB durch (F-15), der Hintergrundprozess prüft jeden
Datensatz gegen das Datenmodell (F-32), der Admin sieht vor dem Import eine
Vorschau, ordnet die Mitglieder per E-Mail zu und findet frühere Importe in
einer Liste (F-17), und die Sensor-Historie wird mit wiederhergestellt (F-16)
(R-19, Issue #3140).

Umsetzungsreihenfolge: **F-15 → F-32 → F-17 → F-16**, streng seriell; alle
vier ändern `tenant_export_service.py`. Die vom Betreiber vorgegebene
Reihenfolge wurde am 2026-11-28 gegen die Abhängigkeiten in den Feature-Dateien
geprüft und trägt, mit einer Anpassung:

- F-15 hängt von keinem der anderen ab und liefert, worauf die übrigen bauen:
  die Prüfung nur noch im Hintergrundprozess, die Ablehnungsdetails am
  Import-Datensatz und die Größenwerte.
- F-32 fügt der Hintergrundprüfung die Dokumentprüfung hinzu und schreibt ihre
  Befunde in das Detailfeld aus F-15. Vor F-17 ist das Ergebnis an der
  Statuskarte eines Imports sichtbar.
- F-17 baut auf der Hintergrundprüfung aus F-15 und zeigt in der Importliste
  jede fehlgeschlagene Vorprüfung, auch die Befunde aus F-32.
- F-16 steht zuletzt: Sein Wertnachweis läuft über die Vorprüfung aus F-17,
  und es ergänzt die Phasenanzeige der Importliste.
- **Anpassung:** Die Phase „Messwerte“ der Fortschrittsanzeige stand in F-17
  (Kriterium 5 vom 2026-11-17), obwohl erst F-16 Messwerte schreibt. Mit F-17
  vor F-16 wäre F-17 nicht abschließbar gewesen. Die Phase ist nach F-16
  `acceptance-9` verschoben; F-17 hängt damit nicht mehr von F-16 ab.

Der value-verifizierende Nachweis ist **F-16 `acceptance-7`**: Ein Garten mit
Datensätzen, Fotos, Mitgliedern und Messwerten wird exportiert, das Archiv
hochgeladen, vorgeprüft, die Mitglieder per E-Mail zugeordnet und aus der
Vorprüfung importiert; der erneute Export des neuen Gartens enthält dieselben
Daten einschließlich aller Rohwerte, Stunden- und Tageswerte. Das Kriterium liegt im letzten Feature
und läuft durch alle vier: Hintergrundprüfung (F-15), Dokumentprüfung eines
unveränderten Archivs (F-32), Vorprüfung mit E-Mail-Zuordnung und Start aus
dem gespeicherten Archiv (F-17), Messwerte (F-16). Ein Kriterium aus F-17
wiese die Vollständigkeit nicht nach, weil die Messwerte dort noch fehlen.
Nicht nachgewiesen wird damit die Größe von rund 500 MiB.

**Verpflichtender Handlauf (Betreiberentscheidung 2026-11-28).** Der Wertsatz
bleibt, wie er ist; die Größe weist der Handlauf zu F-15 `acceptance-1` nach.
Der Sprint schließt nicht ohne bestandenen Handlauf: Der Hook zu F-15
`acceptance-1` darf nur mit `passing` enden, nie mit `skipped`. Der Betreiber
(oder die Hauptsitzung in seinem Auftrag) startet dazu den
`workflow_dispatch`-Lauf gegen die Testinstallation, mit den mitgelieferten
Helm-Werten: Export eines fotolastigen Gartens von rund 500 MiB, Import des
Archivs, einmal über die Admin-Seite hochgeladen. Der Import braucht eine
zweite ArangoDB-Datenbank oder einen Quell-Garten ohne eigene Arten, weil ein
Import neben dem Original an eigenen Arten scheitert. Dieselbe Voraussetzung
(zwei ArangoDB-Datenbanken) gilt für den Wertnachweis F-16 `acceptance-7`.

Betreiberentscheidungen vom 2026-11-27:

- **Sprint 5 enthält nur R-19.**
- **D1 (F-17):** Archivfehler erscheinen als fehlgeschlagene Vorprüfung in der
  Importliste; „nur im Audit“ gilt nur noch für Ablehnungen vor dem Speichern
  (Rolle, Größe, Step-up).
- **D2 (F-17):** Die Step-up-Bestätigung der Vorprüfung gilt eine Stunde für
  den anschließenden Import und ist an denselben Admin gebunden; danach oder
  für einen anderen Admin ist ein neuer Step-up nötig.
- **Dokumentvalidierung nach REQ-056 §12.4:** eigenes kleines Feature in R-19
  (F-32). Die Prüfung läuft im Hintergrundprozess, die Vorprüfung zeigt das
  Ergebnis, ein manipulierter Wert wird abgelehnt statt geschrieben.
- **F-15 Kriterium 4, Option B:** Synchron bleiben Rolle, Größe, Step-up,
  „Plan vorhanden“ und E-Mail → Konto; alles Übrige läuft asynchron; die
  Ablehnungsdetails werden am Import-Datensatz gespeichert; REQ-056 §8.4,
  AK-34, AK-46 und die Runbook-Tabelle werden nachgezogen.
- **Upload-Temp-Speicher:** `/tmp` des Backends liegt auf Disk (Volume im
  Helm-Chart) und wird nicht speicherbasiert vergrößert.
- **Reihenfolge:** F-15 → Dokumentvalidierung → F-17 → F-16.
- Weiter gültig aus derselben Runde: nur eine Installation, der 500-MiB-Test
  läuft nur manuell (`workflow_dispatch`), das Speicherlimit des Workers von
  rund 2 GiB ist akzeptabel, die Datenschutz-Befunde zum Archiv laufen in
  einer eigenen Lane.

Betreiberentscheidungen vom 2026-11-28:

- **F-16:** Messwerte ohne zuordenbaren Sensor werden ausgelassen und gezählt,
  auch die Stunden- und Tageswerte eines solchen Sensors.
- **F-15:** `/tmp` des Workers liegt auch auf Disk.
- **F-16:** Archivierte Stunden- und Tageswerte werden direkt geschrieben,
  nichts wird neu berechnet; ein Neuberechnen über einen Zeitbereich träfe die
  Werte anderer Mandanten.
- **Sprintwert:** Der Satz bleibt, der Handlauf mit rund 500 MiB ist
  verpflichtend (oben).

Festlegungen der Planung vom 2026-11-28, nicht vom Betreiber entschieden und
vor dem Start des jeweiligen Features widerrufbar (Einzelheiten unter „Offene
Punkte“ der Feature-Dateien): der Upload-Pfad bleibt, neu sind Liste und
Start-Route (F-17); die Mitgliedervorschau liegt am Import-Datensatz, ist nur
mit gültiger Bestätigung sichtbar und wird am Ende geleert (F-17); jedes an
eine Collection gebundene Modell muss einen Datensatz annehmen (F-32); eine
falsche Prüfsumme des Messwert-Teils scheitert schon in der Vorprüfung (F-16).
Aus dem Repository nicht belegt und durch einen Integrationstest zu klären:
das Verhalten der Aggregat-Policies gegenüber direkt geschriebenen Stunden-
und Tageswerten (F-16 `acceptance-3`).

## Features

- [F-15](../features/tenant-archive-size-limits.md) — status: ready
- [F-32](../features/tenant-import-document-validation.md) — status: ready
- [F-17](../features/tenant-import-preflight.md) — status: ready
- [F-16](../features/tenant-readings-import.md) — status: ready

## Out of scope

- R-27 (gemessener Regen und Bewässerung, F-28 bis F-31) — kommt in Sprint 6.
- Kc-Tabelle (#3160) — danach.
- Heben älterer Archive durch Migrationen (REQ-056 §8.4 Schritt 1) — hat keinen Besitzer; nach F-32 werden solche Archive abgelehnt statt fehlerhaft importiert.
- Die Datenschutz-Befunde zum Archiv (Abgleich mit abgeschlossenen Löschungen, `anon_`-Pseudonyme, GPS-Genauigkeit) — eigene Lane.
- Umzug eines Mandanten zwischen Installationen; es gibt nur eine Installation.
- Ein automatischer 500-MiB-Test je Pull Request oder nachts.

## Review notes

_Populated by `sprint-review` at closure._
