# Eval-Szenarien: check-pest-data

Drei Fixtures zur Verifikation, dass der Skill fachliche Fehler in
Schädlingsbeschreibungen findet und korrekte Einträge in Ruhe lässt. Jedes
Szenario nennt Eingabe-Prompt, Eingabedaten und das erwartete Verhalten.

## Szenario 1 — Honigtau-Fehler bei Zellsauger (erwartet: 🔴 Kritisch)

- **Prompt:** `/check-pest-data Tetranychus urticae`
- **Eingabe:** `fixtures/honeydew-on-spider-mite.yaml` — ein Spinnmilben-Eintrag,
  dessen `damage_symptoms_de` fälschlich „Honigtau und Rußtau" nennt.
- **Erwartet:** Ein 🔴-Befund unter Dimension C — Spinnmilben sind Zellsauger
  ohne Honigtau (kein Phloemsauger). Korrekturvorschlag: Honigtau entfernen,
  Sprenkelung/Gespinste/Bronzefärbung behalten. `pest_type: arachnid` wird
  korrekt **nicht** beanstandet.

## Szenario 2 — Invertierte Luftfeuchte-Ökologie (erwartet: 🔴 Kritisch)

- **Prompt:** `/check-pest-data spider_mite`
- **Eingabe:** `fixtures/inverted-humidity.yaml` — `optimal_humidity_min: 80`,
  `optimal_humidity_max: 95` für die Spinnmilbe plus Präventionstipp
  „Luftfeuchte niedrig halten".
- **Erwartet:** Ein 🔴-Befund unter Dimension B/F — trockene Luft fördert
  Spinnmilben; hohe RH ist nicht ihr Optimum, und „Luftfeuchte erhöhen" ist die
  korrekte Indoor-Präventionsmaßnahme. Widerspruch zwischen Optimum und Tipp wird
  benannt.

## Szenario 3 — Fachlich einwandfreier Eintrag (erwartet: kein Befund)

- **Prompt:** `/check-pest-data Trialeurodes vaporariorum`
- **Eingabe:** `fixtures/clean-whitefly.yaml` — Weiße Fliege, Honigtau/Rußtau
  korrekt (Phloemsauger), Gelbtafeln als Monitoring, `pest_type: insect`,
  Indoor/Gewächshaus-Einordnung stimmig.
- **Erwartet:** Keine 🔴/🟠-Befunde; Eintrag erscheint unter „Fachlich
  einwandfrei". Höchstens 🟡-Hinweise zu optionaler Verfeinerung.
