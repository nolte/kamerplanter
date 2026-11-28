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
Daten einschließlich aller Messwerte. Das Kriterium liegt im letzten Feature
und läuft durch alle vier: Hintergrundprüfung (F-15), Dokumentprüfung eines
unveränderten Archivs (F-32), Vorprüfung mit E-Mail-Zuordnung und Start aus
dem gespeicherten Archiv (F-17), Messwerte (F-16). Ein Kriterium aus F-17
wiese die Vollständigkeit nicht nach, weil die Messwerte dort noch fehlen.
Nicht nachgewiesen wird damit die Größe von rund 500 MiB: Nach
Betreiberentscheidung läuft dieser Test nur manuell (F-15 `acceptance-1`) und
ist zusätzlich vor dem Sprint-Review einmal auszuführen.

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

Festlegungen der Planung vom 2026-11-28, nicht vom Betreiber entschieden und
vor dem Start des jeweiligen Features widerrufbar (Einzelheiten unter „Offene
Punkte“ der Feature-Dateien): Messwerte ohne zuordenbaren Sensor werden
ausgelassen und gezählt (F-16); der Upload-Pfad bleibt, neu sind Liste und
Start-Route (F-17); die Mitgliedervorschau liegt am Import-Datensatz und wird
am Ende geleert (F-17); `/tmp` des Workers wählt die Umsetzung innerhalb des
Limits von 2 GiB (F-15).

Readiness-Prüfung vom 2026-11-28 (manuell, nach den Kriterien des
`sprint-readiness-reviewer`): **go**, kein blockierender Befund.

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
