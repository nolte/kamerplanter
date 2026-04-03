# VPD-Optimierung

Das Dampfdruckdefizit (VPD — Vapor Pressure Deficit) beschreibt den Unterschied zwischen dem aktuellen Wasserdampfdruck in der Luft und dem maximalen Dampfdruck, den die Luft bei gegebener Temperatur aufnehmen könnte. Es ist der entscheidende Parameter für die Transpirationsrate der Pflanze — und damit für Nährstoffaufnahme, Kühlleistung und Pilzrisiko.

---

## Voraussetzungen

- Thermometer und Hygrometer (Temperatur + relative Luftfeuchtigkeit)
- Bekannte Wachstumsphase der Pflanze
- Lüftungs- oder Klimasteuerung zur Anpassung

---

## Was ist VPD und warum ist es wichtig?

Wenn die Luft trocken ist (hohes VPD), zieht sie aktiv Wasser aus den Blättern — die Stomata öffnen sich weit, Nährstoffe strömen nach, die Pflanze wächst schnell. Ist die Luft zu trocken, schließen die Stomata als Schutz — Wachstum stoppt.

Ist die Luft zu feucht (niedriges VPD), verdunstet kaum Wasser — Nährstofftransport stockt, Pilze gedeihen.

**Optimales VPD = Balance zwischen Wachstum und Schutz.**

---

## Formel (Tetens-Näherung)

Der gesättigte Dampfdruck bei einer bestimmten Temperatur (eSat) ergibt sich aus:

```
eSat(T) = 0,6108 × exp(17,27 × T / (T + 237,3))  [kPa]
```

Der tatsächliche Dampfdruck der Luft:

```
e_aktuell = (rF / 100) × eSat(T_luft)
```

Das VPD berechnet sich aus der Differenz, bezogen auf die Blatttemperatur:

```
VPD = eSat(T_blatt) - e_aktuell
```

In der Praxis wird oft `T_blatt ≈ T_luft - 2 °C` angenommen (Blatt kühlt durch Transpiration).

!!! note "Vereinfachte Berechnung"
    Für den Alltag gilt: VPD ≈ eSat(T_luft) × (1 - rF/100). Diese Näherung funktioniert gut bei Temperaturen zwischen 18 und 30 °C.

---

## Zielwerte nach Wachstumsphase

Kamerplanter verwendet folgende Zielkorridore, die im Backend als Systemkonstanten definiert sind:

| Phase | VPD-Zielbereich (kPa) | Luftfeuchte (Richtwert) | Temperatur (Richtwert) |
|-------|-----------------------|------------------------|------------------------|
| Keimung | 0,4 – 0,8 | 70 – 80 % | 22 – 26 °C |
| Sämling | 0,4 – 0,8 | 65 – 75 % | 22 – 26 °C |
| Vegetativ | 0,8 – 1,2 | 55 – 70 % | 22 – 28 °C |
| Blüte | 1,0 – 1,5 | 40 – 55 % | 22 – 28 °C |
| Reife / Spätblüte | 1,2 – 1,6 | 35 – 50 % | 20 – 26 °C |
| Ausspülung (Flushing) | 0,8 – 1,2 | 55 – 65 % | 20 – 24 °C |

!!! danger "Hohe Luftfeuchte in der Blüte"
    Über 60 % relative Luftfeuchte in der Blütephase begünstigt Botrytis (Grauschimmel) stark. Halten Sie die Luftfeuchte konsequent unter 55 % — besonders in der letzten Blütewoche.

---

## VPD-Werte berechnen — Praxisbeispiel

**Szenario:** Growraum, Vegetativphase, 25 °C Lufttemperatur, 65 % rF

```
eSat(25) = 0,6108 × exp(17,27 × 25 / (25 + 237,3))
         = 0,6108 × exp(1,646)
         = 0,6108 × 5,186
         = 3,168 kPa

e_aktuell = 0,65 × 3,168 = 2,059 kPa

VPD = 3,168 - 2,059 = 1,109 kPa  ✓ (Ziel: 0,8–1,2 kPa)
```

!!! tip "VPD-Rechner"
    In der Praxis reichen einfache VPD-Tabellen oder Apps. Kamerplanter zeigt das berechnete VPD auf der Pflanzendetailseite, sobald Sensordaten vorhanden sind.

---

## VPD-Tabelle (Temperatur × Luftfeuchte)

VPD-Werte in kPa bei verschiedenen Kombinationen aus Temperatur und relativer Luftfeuchte:

| rF \ T | 18 °C | 20 °C | 22 °C | 24 °C | 26 °C | 28 °C | 30 °C |
|--------|-------|-------|-------|-------|-------|-------|-------|
| 40 % | 1,24 | 1,42 | 1,62 | 1,84 | 2,08 | 2,35 | 2,55 |
| 50 % | 1,03 | 1,18 | 1,35 | 1,54 | 1,74 | 1,96 | 2,13 |
| 55 % | 0,93 | 1,07 | 1,22 | 1,38 | 1,56 | 1,76 | 1,91 |
| 60 % | 0,82 | 0,95 | 1,08 | 1,23 | 1,39 | 1,57 | 1,70 |
| 65 % | 0,72 | 0,83 | 0,95 | 1,08 | 1,22 | 1,37 | 1,49 |
| 70 % | 0,62 | 0,71 | 0,81 | 0,92 | 1,04 | 1,18 | 1,28 |
| 75 % | 0,52 | 0,59 | 0,68 | 0,77 | 0,87 | 0,98 | 1,06 |
| 80 % | 0,41 | 0,47 | 0,54 | 0,62 | 0,70 | 0,79 | 0,85 |

*Werte gerundet. Berechnet mit Tetens-Näherung, T_blatt = T_luft.*

---

## Häufige VPD-Probleme und Lösungen

### VPD zu niedrig (Pflanze transpiriert kaum)

**Symptome:** Schlechtes Wachstum, Nährstoffmangel trotz guter Düngung, Schimmelflecken, weiche / dünne Blätter.

**Ursachen und Lösungen:**

| Ursache | Lösung |
|---------|--------|
| Zu hohe Luftfeuchtigkeit | Lüftung erhöhen, Entfeuchter einsetzen |
| Zu niedrige Temperatur | Heizung, Tagtemperatur auf 22–26 °C anheben |
| Überfüllter Grow-Raum | Pflanzdichte reduzieren, Luftzirkulation verbessern |

### VPD zu hoch (Pflanze schließt Stomata)

**Symptome:** Welke Blätter trotz ausreichender Bewässerung, Hitzestress, Blattränder bräunen, gestocktes Wachstum.

**Ursachen und Lösungen:**

| Ursache | Lösung |
|---------|--------|
| Zu trockene Luft | Befeuchter, nasse Tücher, Wasserreservoirs |
| Zu hohe Temperatur | Kühlung, Lüftung, Beleuchtungszeit prüfen |
| Zu intensive Beleuchtung | Lichtintensität reduzieren oder Abstand erhöhen |

---

## VPD und Bewässerungsfrequenz

VPD beeinflusst direkt, wie schnell die Pflanze Wasser aufnimmt. Bei hohem VPD (>1,5 kPa) kann die Transpirationsrate stark ansteigen — Substrate trocknen schneller aus.

**Faustregeln:**
- VPD < 0,8 kPa: Bewässerungsintervall verlängern
- VPD 0,8–1,5 kPa: Normale Bewässerungsfrequenz
- VPD > 1,5 kPa: Bewässerungsfrequenz erhöhen, Hitzestress beobachten

!!! tip "Substrat als Puffer nutzen"
    Coco- und Rockwool-Substrate trocknen bei hohem VPD besonders schnell aus. Soil-Substrate puffern besser. Passen Sie die Bewässerungsfrequenz entsprechend an oder setzen Sie auf automatische Bewässerung via Gießplan.

---

## VPD in Kamerplanter konfigurieren

Kamerplanter erlaubt, phasenbezogene VPD-Zielwerte pro Anforderungsprofil anzupassen:

1. Navigieren Sie zu **Stammdaten > [Art] > Lebenszyklus > [Phase] > Anforderungsprofil**.
2. Passen Sie `vpd_target_kpa` und die Min/Max-Grenzen an.
3. Kamerplanter vergleicht bei vorhandenen Sensordaten den gemessenen Wert mit dem Zielkorridor und zeigt Warnungen im Dashboard.

!!! example "Angepasste VPD-Ziele für empfindliche Sorten"
    Tropische Pflanzen wie Chili oder Basilikum reagieren empfindlicher auf hohes VPD. Setzen Sie den Vegetativ-Zielkorridor enger auf 0,7–1,0 kPa für diese Arten.

---

## Haeufige Fragen

??? question "Muss ich VPD täglich berechnen?"
    Nein. Wenn Sie einmal optimale Temperatur-Luftfeuchte-Kombinationen für Ihre Wachstumsphase kennen (z. B. 25 °C / 60 % für Vegetativ), können Sie diese als Richtwerte am Controller einstellen. Kamerplanter unterstützt Sie mit Warnungen, wenn Sensordaten vom Zielkorridor abweichen.

??? question "Blatttemperatur vs. Lufttemperatur — was messe ich?"
    Standard-Hygrometer messen Lufttemperatur und -feuchte. Das ist für die Praxis ausreichend. Die Blatttemperatur liegt typisch 1–3 °C unter der Lufttemperatur. Für höchste Genauigkeit kann ein Infrarot-Thermometer direkt auf das Blatt gerichtet werden.

??? question "Nachts anderes VPD als tagsüber?"
    Ja. Nachts sinkt die Temperatur, was bei gleicher Feuchte das VPD senkt. Ein leicht niedrigeres Nacht-VPD (0,6–0,8 kPa) ist normal und unbedenklich, solange die absolute Luftfeuchte nicht zu hoch steigt.

---

## Siehe auch

- [Phasensteuerung](../user-guide/growth-phases.md)
- [GDD-Berechnung](gdd-calculation.md)
- [Umgebungssteuerung](../user-guide/actuator-control.md)
- [Sensorik](../user-guide/sensors.md)
