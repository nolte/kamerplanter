# Reach-Probe-Entwürfe (nicht freigegeben)

Hier liegen abgeleitete Reach-Probes, die der Betreiber **noch nicht freigegeben** hat. Der Runner
(`reach_audit.py`, `load_probes`) liest nur die Dateien direkt in `project/reach-probes/`
(`iterdir()`, nicht rekursiv) und überspringt Verzeichnisse — ein Entwurf hier lässt den wöchentlichen
`Capability Reach Audit` daher nicht mit Exit 4 („unapproved-content probe") scheitern.

Die Dateien bleiben unverändert (byte-identisch zur Ableitung, nur verschoben), damit eine spätere
Freigabe nicht als Abschwächung gilt. Freigabe nur durch den Betreiber: Approval-Block füllen und die
Datei zurück nach `project/reach-probes/` verschieben (`git mv`).

| Entwurf | Abgeleitet für | Geparkt seit |
|---|---|---|
| `endpoint-sites-plan-read-model-answers.yml` | #2448 (REQ-053 GP-API-001) | 2026-11-22 |
