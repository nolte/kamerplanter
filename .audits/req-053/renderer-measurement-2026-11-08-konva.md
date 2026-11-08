# Renderer-Messung D-01 — 2026-11-08

REQ-053 WP 9.6 (#2746), GP-NFR-033/034. Erzeugt von `tests/e2e/_renderer_report.py` aus den Messwerten
von `tests/e2e/test_req053_renderer_profile.py`; nicht von Hand bearbeiten, neu erzeugen.

> **WP 9.7 (#2747), Wiederholung mit Konva** (Lauf `konva-9-7`, Branch `feat/req-053-konva-renderer`, nach den
> Optimierungen dieses WP: Verschieben ohne Editor-Render pro Zeigerbewegung, Mausrad-Zoom als CSS-Transform mit
> einem Render nach der Geste, Gestenursprung beim Drücken fixiert). Vergleich mit der SVG-Messung
> `renderer-measurement-2026-11-08.md` (WP 9.6), p95 Drag: large Desktop 50,1 → 16,8 ms, 3 030 Desktop 33,4 → 16,8 ms,
> large Mobile 666,7 → 16,8 ms, 3 030 Mobile 183,3 → 33,4 ms; p95 Zoom: Desktop 33,4–66,7 → 16,7–16,8 ms, Mobile
> 316,7–416,7 → 16,7–16,8 ms. Alle zwölf Werte liegen im Budget von GP-NFR-033/034 (16 ms Desktop, 33 ms Telefon, je
> mit Bildwechsel-Toleranz). Die Zeile „D-01 wörtlich“ unten hält auch das Telefon gegen 16 ms und meldet deshalb den
> 3 030-Mobile-Drag (33,4 ms); maßgeblich für die Abnahme ist GP-NFR-033 mit 33 ms auf dem Telefon.
> Nicht im Fenster: Der Zoom rendert den Plan einmal nach der Geste (120 ms nach dem letzten Mausrad-Ereignis); dieses
> eine Bild liegt außerhalb des gewerteten Fensters. Die „max ms“ des Drags sind das Bild des Drückens (Auswahl,
> Eigenschaften-Blatt) bzw. des Loslassens (Übernahme ins Modell) - INP auf dem Telefon bis 912 ms (beratend).

**Go/No-Go für WP 9.7 (D-01 wörtlich):** Go

**Lesart Platzhalter (3) aus #2759 (nur Mobile-Profil, CPU 4×, Drag gegen das Telefon-Budget 33 ms aus GP-NFR-033):** No-Go

## Messwerte

| Fall | Profil | Renderer | CPU | Viewport | gespeichert (Beete/Slots/Pflanzen) | sichtbar Fit / gezoomt | Geste | Frames im Fenster / erfasst | p95 ms | max ms | Budget ms | GP-NFR-033/034 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Klasse „large“ (250 Beete × 20 Pflanzen) | Desktop | konva | 1× | 1920×937 (Canvas 1034×656) | 250/5000/5000 | 500 / 588 | zoom_in | 37 / 49 | 16.7 | 16.7 | 16.0 | im Budget |
| Klasse „large“ (250 Beete × 20 Pflanzen) | Desktop | konva | 1× | 1920×937 (Canvas 1034×656) | 250/5000/5000 | 500 / 588 | zoom_out | 37 / 54 | 16.7 | 16.7 | 16.0 | im Budget |
| Klasse „large“ (250 Beete × 20 Pflanzen) | Desktop | konva | 1× | 1920×937 (Canvas 1034×656) | 250/5000/5000 | 500 / 588 | drag | 63 / 82 | 16.8 | 150.0 | 16.0 | im Budget |
| Klasse „large“ (250 Beete × 20 Pflanzen) | Mobile (CPU 4×) | konva | 4× | 390×844 (Canvas 341×216) | 250/5000/5000 | 500 / 588 | zoom_in | 44 / 74 | 16.8 | 33.3 | 33.0 | im Budget |
| Klasse „large“ (250 Beete × 20 Pflanzen) | Mobile (CPU 4×) | konva | 4× | 390×844 (Canvas 341×216) | 250/5000/5000 | 500 / 588 | zoom_out | 43 / 73 | 16.8 | 33.4 | 33.0 | im Budget |
| Klasse „large“ (250 Beete × 20 Pflanzen) | Mobile (CPU 4×) | konva | 4× | 390×844 (Canvas 341×216) | 250/5000/5000 | 500 / 588 | drag | 64 / 98 | 16.8 | 899.9 | 33.0 | im Budget |
| Synthetisch, 3 000 sichtbare Objekte (30 Beete × 100 Pflanzen) | Desktop | konva | 1× | 1920×937 (Canvas 845×656) | 30/3000/3000 | 3030 / 606 | zoom_in | 37 / 50 | 16.8 | 16.8 | 16.0 | im Budget |
| Synthetisch, 3 000 sichtbare Objekte (30 Beete × 100 Pflanzen) | Desktop | konva | 1× | 1920×937 (Canvas 845×656) | 30/3000/3000 | 3030 / 606 | zoom_out | 37 / 49 | 16.8 | 16.8 | 16.0 | im Budget |
| Synthetisch, 3 000 sichtbare Objekte (30 Beete × 100 Pflanzen) | Desktop | konva | 1× | 1920×937 (Canvas 845×656) | 30/3000/3000 | 3030 / 606 | drag | 62 / 78 | 16.8 | 83.3 | 16.0 | im Budget |
| Synthetisch, 3 000 sichtbare Objekte (30 Beete × 100 Pflanzen) | Mobile (CPU 4×) | konva | 4× | 390×844 (Canvas 341×265) | 30/3000/3000 | 60 / 606 | zoom_in | 42 / 56 | 16.7 | 16.8 | 33.0 | im Budget |
| Synthetisch, 3 000 sichtbare Objekte (30 Beete × 100 Pflanzen) | Mobile (CPU 4×) | konva | 4× | 390×844 (Canvas 341×265) | 30/3000/3000 | 60 / 606 | zoom_out | 36 / 48 | 16.7 | 16.8 | 33.0 | im Budget |
| Synthetisch, 3 000 sichtbare Objekte (30 Beete × 100 Pflanzen) | Mobile (CPU 4×) | konva | 4× | 390×844 (Canvas 341×265) | 30/3000/3000 | 60 / 606 | drag | 62 / 85 | 33.4 | 416.6 | 33.0 | im Budget |

## Entscheidung

**D-01 wörtlich (Drag gegen 16 ms, alle Profile): Go**

- Schwelle gerissen: synthetic_3000/mobile: Drag-Frametime p95 33.4 ms > 16 ms (Grenze mit Bildwechsel-Toleranz 17.7 ms)

**Platzhalter (3), nur Mobile (Drag gegen 33 ms): No-Go**

- Keine Schwelle gerissen, alle Fälle gemessen.

## Sichtbare Objekte

| Fall | Profil | Renderer | Beete | Marker einzeln | Marker gebündelt | Cluster | SVG-Knoten (Konva: nur Overlay) | px/m |
|---|---|---|---|---|---|---|---|---|
| large (Fit) | desktop | konva | 250 | 0 | 0 | 250 | 1002 | 18.7 |
| large (gezoomt) | desktop | konva | 28 | 0 | 560 | 0 | 58 | 113.3 |
| large (Fit) | mobile | konva | 250 | 0 | 0 | 250 | 1002 | 6.2 |
| large (gezoomt) | mobile | konva | 28 | 0 | 560 | 0 | 58 | 37.4 |
| synthetic_3000 (Fit) | desktop | konva | 30 | 0 | 3000 | 0 | 62 | 34.5 |
| synthetic_3000 (gezoomt) | desktop | konva | 6 | 0 | 600 | 0 | 14 | 208.5 |
| synthetic_3000 (Fit) | mobile | konva | 30 | 0 | 0 | 30 | 122 | 13.9 |
| synthetic_3000 (gezoomt) | mobile | konva | 6 | 0 | 600 | 0 | 14 | 84.1 |

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
