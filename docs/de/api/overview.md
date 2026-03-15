# API-Überblick

Alle API-Endpunkte folgen REST-Konventionen und geben JSON zurück.

!!! note "Platzhalter"
    Dieser Inhalt wird in einem folgenden Schritt ausgearbeitet.

## Basis-URL

```
http://localhost:8000/api/v1/
```

## Mandanten-Routing

Mandanten-spezifische Ressourcen:

```
/api/v1/t/{tenant_slug}/plants/
/api/v1/t/{tenant_slug}/planting-runs/
```

Globale Ressourcen (Arten, IPM-Daten):

```
/api/v1/species/
/api/v1/botanical-families/
```
