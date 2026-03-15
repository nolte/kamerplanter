# GDD-Berechnung

Wachstumsgradtage (GDD — Growing Degree Days) messen die akkumulierte Wärme, die eine Pflanze seit der Aussaat erfahren hat. Sie erlauben zuverlässigere Vorhersagen über Erntezeit und Phasenübergänge als reine Kalenderzeit.

!!! note "Platzhalter"
    Dieser Inhalt wird in einem folgenden Schritt ausgearbeitet.

## Formel

```
GDD = max(0, (T_max + T_min) / 2 - T_base)
```

- `T_max` — Tageshöchsttemperatur (°C)
- `T_min` — Tagestiefsttemperatur (°C)
- `T_base` — Basistemperatur der Pflanze (°C)
