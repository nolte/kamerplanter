# Renderer-Messung D-01 — 2026-11-08

REQ-053 WP 9.6 (#2746), GP-NFR-033/034. Erzeugt von `tests/e2e/_renderer_report.py` aus den Messwerten
von `tests/e2e/test_req053_renderer_profile.py`; nicht von Hand bearbeiten, neu erzeugen.

**Go/No-Go für WP 9.7 (D-01 wörtlich):** Go

**Lesart Platzhalter (3) aus #2759 (nur Mobile-Profil, CPU 4×, Drag gegen das Telefon-Budget 33 ms aus GP-NFR-033):** Go

## Messwerte

| Fall | Profil | CPU | Viewport | gespeichert (Beete/Slots/Pflanzen) | sichtbar Fit / gezoomt | Geste | Frames im Fenster / erfasst | p95 ms | max ms | Budget ms | GP-NFR-033/034 |
|---|---|---|---|---|---|---|---|---|---|---|---|
| Klasse „large“ (250 Beete × 20 Pflanzen) | Desktop | 1× | 1920×937 (Canvas 1034×656) | 250/5000/5000 | 500 / 588 | zoom_in | 33 / 46 | 66.7 | 83.3 | 16.0 | über Budget |
| Klasse „large“ (250 Beete × 20 Pflanzen) | Desktop | 1× | 1920×937 (Canvas 1034×656) | 250/5000/5000 | 500 / 588 | zoom_out | 34 / 47 | 50.0 | 66.6 | 16.0 | über Budget |
| Klasse „large“ (250 Beete × 20 Pflanzen) | Desktop | 1× | 1920×937 (Canvas 1034×656) | 250/5000/5000 | 500 / 588 | drag | 59 / 74 | 50.1 | 116.6 | 16.0 | über Budget |
| Klasse „large“ (250 Beete × 20 Pflanzen) | Mobile (CPU 4×) | 4× | 390×844 (Canvas 341×216) | 250/5000/5000 | 500 / 588 | zoom_in | 28 / 44 | 416.7 | 450.0 | 33.0 | über Budget |
| Klasse „large“ (250 Beete × 20 Pflanzen) | Mobile (CPU 4×) | 4× | 390×844 (Canvas 341×216) | 250/5000/5000 | 500 / 588 | zoom_out | 29 / 46 | 316.7 | 349.9 | 33.0 | über Budget |
| Klasse „large“ (250 Beete × 20 Pflanzen) | Mobile (CPU 4×) | 4× | 390×844 (Canvas 341×216) | 250/5000/5000 | 500 / 588 | drag | 37 / 59 | 666.7 | 816.6 | 33.0 | über Budget |
| Synthetisch, 3 000 sichtbare Objekte (30 Beete × 100 Pflanzen) | Desktop | 1× | 1920×937 (Canvas 845×656) | 30/3000/3000 | 3030 / 606 | zoom_in | 31 / 43 | 50.1 | 83.4 | 16.0 | über Budget |
| Synthetisch, 3 000 sichtbare Objekte (30 Beete × 100 Pflanzen) | Desktop | 1× | 1920×937 (Canvas 845×656) | 30/3000/3000 | 3030 / 606 | zoom_out | 34 / 49 | 33.4 | 33.4 | 16.0 | über Budget |
| Synthetisch, 3 000 sichtbare Objekte (30 Beete × 100 Pflanzen) | Desktop | 1× | 1920×937 (Canvas 845×656) | 30/3000/3000 | 3030 / 606 | drag | 57 / 71 | 33.4 | 116.6 | 16.0 | über Budget |
| Synthetisch, 3 000 sichtbare Objekte (30 Beete × 100 Pflanzen) | Mobile (CPU 4×) | 4× | 390×844 (Canvas 341×265) | 30/3000/3000 | 60 / 606 | zoom_in | 29 / 44 | 383.3 | 416.6 | 33.0 | über Budget |
| Synthetisch, 3 000 sichtbare Objekte (30 Beete × 100 Pflanzen) | Mobile (CPU 4×) | 4× | 390×844 (Canvas 341×265) | 30/3000/3000 | 60 / 606 | zoom_out | 30 / 46 | 333.3 | 333.4 | 33.0 | über Budget |
| Synthetisch, 3 000 sichtbare Objekte (30 Beete × 100 Pflanzen) | Mobile (CPU 4×) | 4× | 390×844 (Canvas 341×265) | 30/3000/3000 | 60 / 606 | drag | 62 / 88 | 183.3 | 566.7 | 33.0 | über Budget |

## Entscheidung

**D-01 wörtlich (Drag gegen 16 ms, alle Profile): Go**

- Schwelle gerissen: large/desktop: Drag-Frametime p95 50.1 ms > 16 ms (Grenze mit Bildwechsel-Toleranz 17.7 ms)
- Schwelle gerissen: large/mobile: Drag-Frametime p95 666.7 ms > 16 ms (Grenze mit Bildwechsel-Toleranz 17.7 ms)
- Schwelle gerissen: synthetic_3000/desktop: Drag-Frametime p95 33.4 ms > 16 ms (Grenze mit Bildwechsel-Toleranz 17.7 ms)
- Schwelle gerissen: synthetic_3000/mobile: Drag-Frametime p95 183.3 ms > 16 ms (Grenze mit Bildwechsel-Toleranz 17.7 ms)

**Platzhalter (3), nur Mobile (Drag gegen 33 ms): Go**

- Schwelle gerissen: large/mobile: Drag-Frametime p95 666.7 ms > 33 ms (Grenze mit Bildwechsel-Toleranz 34.7 ms)
- Schwelle gerissen: synthetic_3000/mobile: Drag-Frametime p95 183.3 ms > 33 ms (Grenze mit Bildwechsel-Toleranz 34.7 ms)

## Sichtbare Objekte

| Fall | Profil | Beete | Marker einzeln | Marker gebündelt | Cluster | SVG-Knoten | px/m |
|---|---|---|---|---|---|---|---|
| large (Fit) | desktop | 250 | 0 | 0 | 250 | 1252 | 18.7 |
| large (gezoomt) | desktop | 28 | 0 | 560 | 0 | 142 | 113.3 |
| large (Fit) | mobile | 250 | 0 | 0 | 250 | 1252 | 6.2 |
| large (gezoomt) | mobile | 28 | 0 | 560 | 0 | 114 | 37.4 |
| synthetic_3000 (Fit) | desktop | 30 | 0 | 3000 | 0 | 152 | 34.5 |
| synthetic_3000 (gezoomt) | desktop | 6 | 0 | 600 | 0 | 32 | 208.5 |
| synthetic_3000 (Fit) | mobile | 30 | 0 | 0 | 30 | 152 | 13.9 |
| synthetic_3000 (gezoomt) | mobile | 6 | 0 | 600 | 0 | 32 | 84.1 |

Hinweis: Auf dem Smartphone (390 × 844) kann der Plan „3 000 Objekte“ in der Gesamtansicht keine 3 000 Objekte zeigen — die Fit-Zoomstufe liegt dort weit unter der Marker-LOD-Schwelle (10 px Markerabstand), der Renderer zeichnet Beete und Cluster. Der Mobile-Fall misst diese Last, nicht die D-01-Last; die Objektzahl wird so berichtet, wie sie gezeichnet wurde.

## Methode

- Frametime: Abstand aufeinanderfolgender `requestAnimationFrame`-Rückrufe während der Geste (`tests/e2e/_inp_probe.py`), 95. Perzentil nach Rangverfahren. Ein leerlaufender 60-Hz-Browser liest 16,7 ms je Bild; eine Grenze gilt deshalb mit einer Toleranz von 10 % des gemessenen Leerlauf-Bildabstands als eingehalten (16,7 ms = kein Bild verloren).
- Fenster einer Geste: die Seite stempelt jedes Zeiger- und Mausrad-Ereignis; gewertet werden nur Bilder, die nach dem ersten Ereignis enden, bis einschließlich des ersten Bildes nach dem letzten Ereignis. Bilder davor (WebDriver-Rundlauf) und danach (Warten auf den Effekt) sind erfasst, aber nicht gewertet.
- Drag: ein Beet nahe der Canvas-Mitte, 30 Zeigerbewegungen à 16 ms hin und zurück, Netto-Versatz 2 px; danach Rückgängig. Zoom: Strg + Mausrad, 10 Rasten hinein und 10 heraus im Abstand von 40 ms, ab der Fit-Ansicht (überquert die Marker-LOD-Schwelle).
- Sichtbare Objekte: was der SVG-Renderer nach Culling (20 % Rand) und LOD gezeichnet hat — Beete, Gartenobjekte, jeder Marker (einzeln oder gebündelt), jeder Cluster; die Grenze zählt nicht.
- Profile: Desktop = Fenster 1920 × 1080 (gesetzt; Viewport und Canvas-Größe stehen im Datensatz) ohne Drosselung (Budget 16 ms); Mobile = Viewport 390 × 844 im Planungsmodus, CPU über CDP `Emulation.setCPUThrottlingRate` 4× gedrosselt (Budget 33 ms).
- Beratend: eine Überschreitung ist eine Warnung im Testlauf, kein Fehler. Die Messung läuft im Selenium-Grid neben anderen Workern; Ausreißer sind möglich, eine knappe Entscheidung ist zu wiederholen.

## Quellen

- `test-reports/e2e/renderer/renderer-profile-large-desktop.json`
- `test-reports/e2e/renderer/renderer-profile-large-mobile.json`
- `test-reports/e2e/renderer/renderer-profile-synthetic_3000-desktop.json`
- `test-reports/e2e/renderer/renderer-profile-synthetic_3000-mobile.json`
