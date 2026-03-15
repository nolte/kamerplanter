# Wachstumsphasen

Kamerplanter führt jede Pflanze durch definierte Wachstumsphasen: Keimung, Sämling, Vegetativ, Blüte, Ernte. Jede Phase hat eigene VPD-Ziele, Photoperioden-Einstellungen und NPK-Profile.

!!! note "Platzhalter"
    Dieser Inhalt wird in einem folgenden Schritt ausgearbeitet.

## Phasen-Überblick

```mermaid
stateDiagram-v2
    [*] --> Keimung
    Keimung --> Sämling : Keimblatt sichtbar
    Sämling --> Vegetativ : Erstes echtes Blatt
    Vegetativ --> Blüte : Photoperiode-Wechsel
    Blüte --> Ernte : Reife erreicht
    Ernte --> [*]
```

## Siehe auch

- [Stammdaten](plant-management.md)
- [Dünge-Logik](fertilization.md)
