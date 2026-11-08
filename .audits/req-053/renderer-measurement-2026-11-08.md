# Renderer-Messung D-01 — 2026-11-08

REQ-053 WP 9.6 (#2746), GP-NFR-033/034. Erzeugt von `tests/e2e/_renderer_report.py` aus den Messwerten
von `tests/e2e/test_req053_renderer_profile.py`; nicht von Hand bearbeiten, neu erzeugen.

**Go/No-Go für WP 9.7 (D-01 wörtlich):** Go

**Lesart Platzhalter (3) aus #2759 (nur Mobile-Profil, CPU 4×):** Go

## Messwerte

| Fall | Profil | CPU | Viewport | gespeichert (Beete/Slots/Pflanzen) | sichtbar Fit / gezoomt | Geste | Frames | p95 ms | max ms | Budget ms | GP-NFR-033/034 |
|---|---|---|---|---|---|---|---|---|---|---|---|
| Klasse „large“ (250 Beete × 20 Pflanzen) | Desktop | 1× | 1920×937 | 250/5000/5000 | 500 / 588 | zoom_in | 50 | 83.4 | 116.6 | 16.0 | über Budget |
| Klasse „large“ (250 Beete × 20 Pflanzen) | Desktop | 1× | 1920×937 | 250/5000/5000 | 500 / 588 | zoom_out | 46 | 50.0 | 83.4 | 16.0 | über Budget |
| Klasse „large“ (250 Beete × 20 Pflanzen) | Desktop | 1× | 1920×937 | 250/5000/5000 | 500 / 588 | drag | 74 | 33.4 | 133.3 | 16.0 | über Budget |
| Klasse „large“ (250 Beete × 20 Pflanzen) | Mobile (CPU 4×) | 4× | 390×844 | 250/5000/5000 | 500 / 588 | zoom_in | 46 | 500.0 | 566.7 | 33.0 | über Budget |
| Klasse „large“ (250 Beete × 20 Pflanzen) | Mobile (CPU 4×) | 4× | 390×844 | 250/5000/5000 | 500 / 588 | zoom_out | 46 | 350.0 | 416.6 | 33.0 | über Budget |
| Klasse „large“ (250 Beete × 20 Pflanzen) | Mobile (CPU 4×) | 4× | 390×844 | 250/5000/5000 | 500 / 588 | drag | 83 | 166.6 | 583.3 | 33.0 | über Budget |
| Synthetisch, 3 000 sichtbare Objekte (30 Beete × 100 Pflanzen) | Desktop | 1× | 1920×937 | 30/3000/3000 | 3030 / 606 | zoom_in | 47 | 50.1 | 66.6 | 16.0 | über Budget |
| Synthetisch, 3 000 sichtbare Objekte (30 Beete × 100 Pflanzen) | Desktop | 1× | 1920×937 | 30/3000/3000 | 3030 / 606 | zoom_out | 49 | 16.8 | 50.0 | 16.0 | im Budget |
| Synthetisch, 3 000 sichtbare Objekte (30 Beete × 100 Pflanzen) | Desktop | 1× | 1920×937 | 30/3000/3000 | 3030 / 606 | drag | 72 | 33.3 | 83.3 | 16.0 | über Budget |
| Synthetisch, 3 000 sichtbare Objekte (30 Beete × 100 Pflanzen) | Mobile (CPU 4×) | 4× | 390×844 | 30/3000/3000 | 60 / 606 | zoom_in | 43 | 316.7 | 350.0 | 33.0 | über Budget |
| Synthetisch, 3 000 sichtbare Objekte (30 Beete × 100 Pflanzen) | Mobile (CPU 4×) | 4× | 390×844 | 30/3000/3000 | 60 / 606 | zoom_out | 44 | 283.3 | 316.7 | 33.0 | über Budget |
| Synthetisch, 3 000 sichtbare Objekte (30 Beete × 100 Pflanzen) | Mobile (CPU 4×) | 4× | 390×844 | 30/3000/3000 | 60 / 606 | drag | 87 | 216.6 | 633.3 | 33.0 | über Budget |

## Entscheidung

**D-01 wörtlich: Go**

- Schwelle gerissen: large/desktop: Drag-Frametime p95 33.4 ms > 16 ms (Grenze mit Bildwechsel-Toleranz 17.7 ms)
- Schwelle gerissen: large/mobile: Drag-Frametime p95 166.6 ms > 16 ms (Grenze mit Bildwechsel-Toleranz 17.7 ms)
- Schwelle gerissen: synthetic_3000/desktop: Drag-Frametime p95 33.3 ms > 16 ms (Grenze mit Bildwechsel-Toleranz 17.7 ms)
- Schwelle gerissen: synthetic_3000/mobile: Drag-Frametime p95 216.6 ms > 16 ms (Grenze mit Bildwechsel-Toleranz 17.7 ms)

**Platzhalter (3), nur Mobile: Go**

- Schwelle gerissen: large/mobile: Drag-Frametime p95 166.6 ms > 16 ms (Grenze mit Bildwechsel-Toleranz 17.7 ms)
- Schwelle gerissen: synthetic_3000/mobile: Drag-Frametime p95 216.6 ms > 16 ms (Grenze mit Bildwechsel-Toleranz 17.7 ms)

## Sichtbare Objekte

| Fall | Profil | Beete | Marker einzeln | Marker gebündelt | Cluster | SVG-Knoten | px/m |
|---|---|---|---|---|---|---|---|
| large (Fit) | desktop | 250 | 0 | 0 | 250 | 1252 | 18.7 |
| large (gezoomt) | desktop | 28 | 0 | 560 | 0 | 142 | 113.3 |
| large (Fit) | mobile | 250 | 0 | 0 | 250 | 1252 | 6.2 |
| large (gezoomt) | mobile | 28 | 0 | 560 | 0 | 114 | 37.4 |
| synthetic_3000 (Fit) | desktop | 30 | 0 | 3000 | 0 | 152 | 34.6 |
| synthetic_3000 (gezoomt) | desktop | 6 | 0 | 600 | 0 | 32 | 209.1 |
| synthetic_3000 (Fit) | mobile | 30 | 0 | 0 | 30 | 152 | 15.5 |
| synthetic_3000 (gezoomt) | mobile | 6 | 0 | 600 | 0 | 32 | 93.8 |

Hinweis: Auf dem Smartphone (390 × 844) kann der Plan „3 000 Objekte“ in der Gesamtansicht keine 3 000 Objekte zeigen — die Fit-Zoomstufe liegt dort weit unter der Marker-LOD-Schwelle (10 px Markerabstand), der Renderer zeichnet Beete und Cluster. Der Mobile-Fall misst diese Last, nicht die D-01-Last; die Objektzahl wird so berichtet, wie sie gezeichnet wurde.

## Methode

- Frametime: Abstand aufeinanderfolgender `requestAnimationFrame`-Rückrufe während der Geste (`tests/e2e/_inp_probe.py`), 95. Perzentil nach Rangverfahren. Ein leerlaufender 60-Hz-Browser liest 16,7 ms je Bild; eine Grenze gilt deshalb mit einer Toleranz von 10 % des gemessenen Leerlauf-Bildabstands als eingehalten (16,7 ms = kein Bild verloren).
- Drag: ein Beet nahe der Canvas-Mitte, 30 Zeigerbewegungen à 16 ms hin und zurück, Netto-Versatz klein; danach Rückgängig. Zoom: Strg + Mausrad, 10 Rasten hinein und 10 heraus im Abstand von 40 ms, ab der Fit-Ansicht (überquert die Marker-LOD-Schwelle).
- Sichtbare Objekte: was der SVG-Renderer nach Culling (20 % Rand) und LOD gezeichnet hat — Beete, Gartenobjekte, jeder Marker (einzeln oder gebündelt), jeder Cluster; die Grenze zählt nicht.
- Profile: Desktop = Fenster 1920 × 1080 ohne Drosselung (Budget 16 ms); Mobile = Viewport 390 × 844 im Planungsmodus, CPU über CDP `Emulation.setCPUThrottlingRate` 4× gedrosselt (Budget 33 ms).
- Beratend: eine Überschreitung ist eine Warnung im Testlauf, kein Fehler. Die Messung läuft im Selenium-Grid neben anderen Workern; Ausreißer sind möglich, eine knappe Entscheidung ist zu wiederholen.

## Quellen

- `test-reports/e2e/renderer/renderer-profile-large-desktop.json`
- `test-reports/e2e/renderer/renderer-profile-large-mobile.json`
- `test-reports/e2e/renderer/renderer-profile-synthetic_3000-desktop.json`
- `test-reports/e2e/renderer/renderer-profile-synthetic_3000-mobile.json`
