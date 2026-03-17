# GDD-Berechnung

Wachstumsgradtage (GDD — Growing Degree Days) messen die akkumulierte Wärme, die eine Pflanze seit der Aussaat erfahren hat. Sie erlauben zuverlässigere Vorhersagen über Erntezeit und Phasenübergänge als reine Kalenderzeit, weil Pflanzen auf Wärme reagieren — nicht auf Kalendertage.

---

## Voraussetzungen

- Eine angelegte Pflanzinstanz mit Aussaatdatum
- Tagestemperaturen (manuell erfasst oder über Sensor)
- Bekannte Basistemperatur der Pflanzenart (in den Stammdaten hinterlegbar)

---

## Die GDD-Formel

Kamerplanter verwendet die klassische Tagesmittel-Methode:

```
GDD_Tag = max(0, (T_max + T_min) / 2 - T_base)
```

| Parameter | Bedeutung | Typischer Wert |
|-----------|-----------|----------------|
| `T_max` | Tageshöchsttemperatur (°C) | gemessen oder Tagesdurchschnitt |
| `T_min` | Tagestiefsttemperatur (°C) | gemessen oder Tagesdurchschnitt |
| `T_base` | Basistemperatur der Pflanze (°C) | 10 °C (viele Gemüse), 0 °C (Weizen) |

Die akkumulierten GDD seit Aussaat ergeben sich aus der Summe aller Tageswerte:

```
GDD_akkumuliert = Σ GDD_Tag  (von Tag 1 bis heute)
```

!!! note "Negativwerte werden ignoriert"
    Liegt die Tagesmitteltemperatur unter der Basistemperatur, ergibt sich 0 — nicht ein negativer Wert. Die Pflanze akkumuliert an kalten Tagen keine Wärme.

---

## Basistemperaturen häufiger Pflanzen

| Pflanzenart | T_base (°C) | Hinweis |
|-------------|-------------|---------|
| Tomate | 10 | Fruchtreife ~1000–1400 GDD |
| Paprika / Chili | 10 | Reife ~1200–1600 GDD |
| Gurke | 10 | Ernte ~600–800 GDD |
| Salat / Kopfsalat | 4 | Schnell, ~500 GDD |
| Mais | 10 | Reife ~1300–1600 GDD |
| Cannabis (Kurztagspflanzen) | 10 | Blütezeit variiert stark nach Sorte |
| Basilikum | 10 | Schnitt nach ~300 GDD |
| Karotte | 4 | Ernte nach ~1000–1200 GDD |

!!! tip "Basistemperatur in den Stammdaten pflegen"
    Tragen Sie die Basistemperatur einer Art direkt in den Stammdaten unter dem Reiter "Wachstumsanforderungen" ein. Kamerplanter verwendet diesen Wert automatisch bei der GDD-Berechnung für alle Pflanzen dieser Art.

---

## Beispielrechnung

**Szenario:** Tomate, T_base = 10 °C, 5 Tage nach Aussaat

| Tag | T_max (°C) | T_min (°C) | Tagesmittel | GDD_Tag | GDD kumuliert |
|-----|-----------|-----------|-------------|---------|---------------|
| 1 | 22 | 14 | 18,0 | 8,0 | 8,0 |
| 2 | 25 | 16 | 20,5 | 10,5 | 18,5 |
| 3 | 18 | 8 | 13,0 | 3,0 | 21,5 |
| 4 | 11 | 6 | 8,5 | 0,0 | 21,5 |
| 5 | 24 | 15 | 19,5 | 9,5 | 31,0 |

An Tag 4 lag das Tagesmittel (8,5 °C) unter der Basistemperatur (10 °C), daher wurden keine GDD akkumuliert.

---

## GDD und Phasenübergänge in Kamerplanter

Kamerplanter kann GDD-basierte Phasenübergangsregeln auswerten. Wenn eine Pflanze eine definierte GDD-Schwelle erreicht, wird automatisch ein Übergangshinweis ausgelöst.

### Konfiguration einer GDD-Übergangsregel

1. Öffnen Sie die Stammdaten der gewünschten Pflanzenart.
2. Navigieren Sie zu **Lebenszyklus > Übergangskriterien**.
3. Wählen Sie für den gewünschten Phasenübergang den Typ **GDD-basiert**.
4. Tragen Sie den Schwellenwert in GDD ein.

!!! example "Beispiel: Tomate Vegetativ → Blüte"
    Tragen Sie 400 GDD als Schwellenwert für den Übergang von der vegetativen Phase in die Blütephase ein. Sobald die Pflanze diesen Wert erreicht hat, erscheint ein Übergangshinweis im Dashboard.

---

## GDD vs. Kalendertage

| Kriterium | Kalendertage | GDD |
|-----------|-------------|-----|
| Einfachheit | Sehr einfach | Erfordert Temperaturdaten |
| Genauigkeit bei Wärme-/Kältephasen | Gering | Hoch |
| Vergleichbarkeit zwischen Jahren | Eingeschränkt | Gut vergleichbar |
| Nützlich für | Grobe Planung | Ernte- und Phasenprognose |

!!! tip "Kombination empfohlen"
    Für genaue Erntezeitplanung empfiehlt sich die Kombination: Kalenderzeit als grober Rahmen, GDD als Feinindikator für Reife.

---

## Temperaturbegrenzte GDD (optionale Methode)

Manche Pflanzen akkumulieren auch bei sehr hohen Temperaturen keine zusätzliche Reife — das Wachstum verlangsamt sich über einer Maximaltemperatur. Die erweiterte Formel:

```
T_eff = min(T_max_cap, max(T_base, Tagesmittel))
GDD_Tag = T_eff - T_base
```

| Parameter | Bedeutung |
|-----------|-----------|
| `T_max_cap` | Obere Temperaturbegrenzung (z. B. 30 °C) |
| `T_eff` | Effektive Temperatur nach Kappung |

!!! note "Vereinfachte Methode in Kamerplanter"
    Kamerplanter verwendet standardmäßig die einfache Tagesmittelmethode ohne obere Temperaturbegrenzung. Die erweiterte Methode steht für zukünftige Versionen auf der Roadmap.

---

## Hintergrund: Warum GDD besser als Kalenderzeit sind

Pflanzen sind keine Kalender. Ihre Entwicklung wird durch aufgenommene Wärmeenergie gesteuert. Ein warmes Frühjahr kann die Entwicklung einer Tomate um 2–3 Wochen gegenüber einem kalten Jahr beschleunigen. Auf GDD-Basis sind solche Jahrgänge direkt vergleichbar.

!!! example "Praxisbeispiel aus dem Freiland"
    In einem warmen Jahr (April-Durchschnitt 16 °C) erreicht eine Tomate die Blütephase schon nach 4 Wochen. Im kühlen Folgejahr (April-Durchschnitt 12 °C) dauert es 7 Wochen. In GDD ausgedrückt sind beide Ereignisse auf ~400 GDD vergleichbar.

---

## Haeufige Fragen

??? question "Welche Basistemperatur soll ich für Cannabis verwenden?"
    Die meisten Cannabis-Sorten verwenden T_base = 10 °C. Manche Indoor-Züchter setzen 15 °C, da die Pflanzen nie unter dieser Temperatur kultiviert werden. Konsistenz ist wichtiger als der Absolutwert — verwenden Sie für alle Pflanzen einer Art denselben Wert.

??? question "Muss ich täglich Temperaturen erfassen?"
    Für Indoor-Anbau mit konstanter Temperatur reicht ein Tagesdurchschnitt. Für Außenanlagen empfiehlt sich die Min/Max-Methode mit einem Thermometer. Zukünftig kann Kamerplanter Wetterdaten automatisch über die DWD-/Open-Meteo-Integration beziehen (REQ-005).

??? question "GDD-Wert ist unrealistisch hoch, was ist falsch?"
    Prüfen Sie, ob die Basistemperatur in den Stammdaten korrekt eingetragen ist. Eine versehentlich auf 0 °C gesetzte Basistemperatur summiert jede Umgebungswärme auf.

---

## Siehe auch

- [Phasensteuerung](../user-guide/growth-phases.md)
- [VPD-Optimierung](vpd-optimization.md)
- [Stammdatenverwaltung](../user-guide/plant-management.md)
