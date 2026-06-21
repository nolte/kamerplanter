# REQ-044 WP-3 — Referenz-Datensatz: reale GBIF-Coverage (Cold-Start)

**Stand:** 2026-06-21
**Zweck:** Ergebnis des **echten** ersten Akquise-Laufs der `PestDatasetAcquisitionService`-Pipeline gegen die Live-GBIF-Occurrence-API (öffentlich, ohne Credentials). Misst, wie viele **lizenz-saubere (CC0/CC-BY) und attributierte** Bilder pro Klasse für den Few-Shot-Prototyp-Index (frozen DINOv2) verfügbar sind. Dies ist das Eingangs-Material für den eigentlichen Index-Schreibvorgang (`/pest/reference` im Inferenz-Service).

**Pipeline:** `list_media(taxonKey)` → Lizenzfilter (nur CC0/CC-BY) → **CC-BY ohne Attribution verworfen** (CC-BY-Compliance) → Download → Quality-Gate (min. 256 px, Aspect ≤ 2,5) → EXIF-Strip → (Prototyp würde indiziert). Der Index selbst (DINOv2-Embeddings in pgvector) entsteht erst beim Lauf gegen den deployten Inferenz-Service.

## Coverage pro Klasse

Lauf mit `max_candidates=150` (Occurrence-Limit; ergibt mehr Bild-Kandidaten, da Occurrences mehrere Fotos haben), Ziel 12 akzeptierte Prototypen/Klasse.

| Klasse | Kategorie | Bild-Kandidaten | akzeptiert (sauber) | Haupt-Ablehnung | Ziel ≥12 |
|---|---|---|---|---|---|
| spider_mite | pest | 472 | 12 | — | ✅ |
| thrips_echinothrips | pest | 119 | 12 | — | ✅ |
| aphid | pest | 274 | 12 | Lizenz 43 | ✅ |
| mealybug | pest | 320 | 12 | Lizenz 45 | ✅ |
| ladybird | beneficial | 277 | 12 | Lizenz 81 | ✅ |
| lacewing | beneficial | 327 | 12 | Lizenz 43 | ✅ |
| hoverfly | beneficial | 290 | 12 | Lizenz 21 | ✅ |
| whitefly | pest | 242 | 9 | **Lizenz 166 (CC-BY-NC)** | ⚠️ |
| fungus_gnat | pest | 279 | 8 | **Lizenz 195 (CC-BY-NC)** | ⚠️ |
| thrips_frankliniella | pest | 180 | 6 | Lizenz 63 | ⚠️ |
| parasitoid_wasp | beneficial | 45 | 7 | Quality 22 (kleine Bilder) | ⚠️ |
| predatory_mite | beneficial | 161 | 5 | wenige Occurrences | ⚠️ |

**Summe:** 119 saubere Prototypen über 12 Klassen; **alle CC-BY-Einträge tragen Attribution** (82× CC-BY + 37× CC0). 7/12 Klassen erreichen das (konservative) Ziel sofort.

## Befunde

1. **Lizenz-Compliance gehärtet:** CC-BY-Bilder ohne ermittelbare Attribution (z. B. einige Flickr-via-GBIF-Records) werden verworfen — sonst Verstoß gegen die CC-BY-Namensnennungspflicht. CC0 braucht keine Attribution.
2. **Dünne Klassen** (bestätigt die Readiness-Prognose, Prep §3):
   - `fungus_gnat` (Trauermücken) und `whitefly` (Weiße Fliege): sehr viele iNaturalist-Bilder sind **CC-BY-NC** (nicht nutzbar) → wenig sauberer Bestand.
   - `predatory_mite` / `parasitoid_wasp`: insgesamt wenige Occurrences bzw. kleine Bilder (Quality-Gate).
   - `thrips_frankliniella`: moderat.
3. **Quality-Gate** greift v. a. bei Schlupfwespen (kleine Makro-Crops < 256 px).

## Empfohlene Maßnahmen für die dünnen Klassen

- `max_candidates` für betroffene Klassen weiter erhöhen (GBIF erlaubt bis 300/Seite, dann paginieren).
- **Wikimedia-Commons als 2. Quelle** zuschalten (Adapter existiert bereits für die Pflanzen-Pipeline) — gerade für Nützlings-Larven.
- TaxonKeys auf Genus/Familie erweitern (z. B. weitere *Bemisia*/*Sciaridae*-Arten).
- **HITL-Nutzerbilder** als primäre Quelle für die Schadbild-Lücke aufbauen (GBIF zeigt überwiegend die Insekten selbst, weniger Schadbilder wie Gespinste/Honigtau).

## Wichtige Einordnung

GBIF-Occurrence-Bilder zeigen meist **das Insekt**, nicht das **Schadbild**. Der Cold-Start-Index ist damit gut für die on-leaf-Wiedererkennung des Tiers, aber **schwach für reine Symptom-Erkennung**. Vor Produktivnutzung: kuratierte Schadbilder nachindizieren + Trefferquote an echten Nutzerfotos messen + WP-5-Kalibrierung (TS/Energy/Risk-Coverage); Abstention bleibt konstitutiv.

## Nächster Schritt (echter Index)

Mit erreichbarem Inferenz-Service:

```bash
python -m app.migrations.acquire_pest_dataset --manifest pest_reference_manifest.json
```

schreibt die DINOv2-Prototypen in den `pest_embeddings`-pgvector-Index und das Attributions-Manifest (CC-BY-Pflicht). Danach `GET /pest/status` → `index_count` pro Klasse prüfen.
