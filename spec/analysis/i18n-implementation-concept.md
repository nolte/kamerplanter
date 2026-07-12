# i18n Implementierungskonzept (N-Sprachen-Mehrsprachigkeit)

> Ziel-Architektur für konsistente, skalierbare N-Sprachen-Mehrsprachigkeit.
> Erstellt für Issue #568. Ist-Zustand: `spec/analysis/i18n-current-state-capture.md`.
> Anforderung: `spec/nfr/NFR-017_Skalierbare-Mehrsprachigkeit.md`. Rollout: `.audits/plans/07-i18n-nlanguage-rollout.md`.
>
> **Scope:** Dieses Dokument definiert das Ziel-Modell und begründet die Wahl. Die konkrete Migration
> (Reihenfolge, Call-Sites, Migrations-Versionen) steht im Rollout-Plan. Übersetzte Inhalte und die Wahl
> der Launch-Sprachen sind explizit **Non-Goals** (Issue #568).

## 1. Zielbild in einem Satz

Genau **ein** Locale-keyed Content-Modell (`LocalizedText`), genau **eine** Locale-Resolution pro Layer
mit **einer** Fallback-Kette, Enums als stabile Werte + Katalog-Labels, technische Fehler English-only /
nutzerseitige Meldungen über `error_code`-Katalog — sodass eine neue Sprache eine **additive Daten-/
Katalog-Operation** ist, ohne Schema-, Feld- oder Code-Zweig-Änderung.

## 2. Designprinzipien (aus den harten Constraints)

- **P-1 Kein per-Sprache-Attribut.** Modell skaliert auf 5+ Sprachen ohne per-Entität-Feldwachstum.
- **P-2 Technische Fehler English-only**, nutzerseitige Meldungen katalogisierbar.
- **P-3 Konsistenz:** eine Resolution, ein Content-Modell, eine Fallback-Kette.

Zusatz-Leitplanken aus dem Ist-Zustand:
- **Additiv & migrierbar:** kein Big-Bang. Loader/Resolver lesen im Übergang beide Formen.
- **DRY über den Stack:** ein Typ + ein Resolver pro Layer, nicht pro Modell/Call-Site dupliziert.
- **Offener Sprachcode-Raum:** BCP-47-`str`, kein geschlossenes `Literal["de","en"]`.

---

## 3. Content-Modell: `LocalizedText` (Locale-Map)

### 3.1 Kanonische Form

Lokalisierte, menschenlesbare Werte werden als **nach BCP-47-Sprachcode verschlüsselte Map** gespeichert —
exakt das heute schon vorhandene `GlossaryTerm.labels`-Muster, verallgemeinert:

```python
# common/i18n.py  (neu, Single Source of Truth)
type LocalizedText = dict[str, str]          # {"de": "...", "en": "...", "fr": "..."}
type LocalizedList = dict[str, list[str]]    # z.B. Aliase

DEFAULT_LOCALE = "de"

def resolve_text(text: LocalizedText, locale: str, *, fallback: str = DEFAULT_LOCALE) -> str:
    """Fallback-Kette: exakt → Basissprache → Default → erste vorhandene → ''."""
    if not text:
        return ""
    base = locale.split("-")[0]
    return (
        text.get(locale)
        or text.get(base)
        or text.get(fallback)
        or next(iter(text.values()), "")
    )
```

Seed-YAML (Zielform, ersetzt `common_name_de` / `common_name_en`):

```yaml
common_name:
  de: Gummibaum
  en: Rubber plant
  # fr: … ← reine additive Datenergänzung, KEINE Schemaänderung
```

JSON-Schema — **eine** wiederverwendbare Definition statt pro-Sprache-Properties:

```yaml
# schemas/_defs.schema.yaml
$defs:
  localized_text:
    type: object
    additionalProperties: { type: string }   # offener Sprachcode-Raum
    minProperties: 1
# Nutzung:  common_name: { $ref: "_defs.schema.yaml#/$defs/localized_text" }
```

### 3.2 Warum genau dieses Muster

| Kriterium | Locale-Map `{de,en,fr,…}` | Suffix-Felder `*_de`,`*_en` (Ist) |
|-----------|---------------------------|-----------------------------------|
| Neue Sprache | additive Datenzeile, **0** Schema-/Code-Änderung | neues Feld pro Entität überall |
| Schema | 1 `$ref` | N Properties pro lokalisiertem Feld |
| Fallback | ein Resolver | pro Call-Site `?:`-Logik |
| Konsistenz | erzwungen durch Typ | 68 % nur-DE, uneinheitlich |
| Vorhandensein | schon in glossary/starter_kit | dominanter Alt-Bestand |

### 3.3 Frontend-Pendant

```ts
// utils/i18n.ts
export type LocalizedText = Record<string, string>;
export const DEFAULT_LOCALE = 'de';
export function resolveText(t: LocalizedText | undefined, locale: string,
                            fallback = DEFAULT_LOCALE): string {
  if (!t) return '';
  const base = locale.split('-')[0];
  return t[locale] ?? t[base] ?? t[fallback] ?? Object.values(t)[0] ?? '';
}
```

`api/types.ts`: `name_de: string; name_en: string` → `name: LocalizedText`. Die 246 `_de`/`_en`-
Zugriffe und der Hook `useLocalizedField` werden auf `resolveText(rec.name, i18n.language)` umgestellt.

---

## 4. Locale-Resolution (P-3)

### 4.1 Backend — eine Dependency

```python
# common/locale.py (neu)
async def get_request_locale(request: Request, user: CurrentUser | None = ...) -> str:
    # Priorität: expliziter Param  >  user.locale  >  Accept-Language  >  DEFAULT_LOCALE
    if (q := request.query_params.get("locale") or request.query_params.get("language")):
        return normalize(q)
    if user and user.locale:
        return normalize(user.locale)
    if (al := request.headers.get("accept-language")):
        return negotiate(al, SUPPORTED_LOCALES) or DEFAULT_LOCALE
    return DEFAULT_LOCALE
```

Ersetzt die **72** verstreuten `language: str = "de"`-Parameter. `user.locale` wird damit erstmals
**tatsächlich angewendet** (heute nur Echo). Endpoints, die weiterhin einen expliziten Param brauchen
(z.B. Print „exportiere auf EN, obwohl UI DE"), behalten ihn — er hat nur die höchste Priorität in
derselben Kette.

### 4.2 Frontend — eine aktive Locale

`i18n.language` ist die **einzige** Quelle. Alle Entscheidungen (Text, Enum-Label, Datum/Zahl,
Backend-Content-Auswahl) leiten daraus ab. Die ~76 binären `=== 'de'`/`startsWith('en')`-Zweige und
45 Locale-Literale entfallen zugunsten von `resolveText(...)` (Content), `resolveEnumLabel(...)` (Enum)
und der zentralen `utils/formatting.ts` (`Intl.*` mit `i18n.language`).

### 4.3 Fallback-Kette (einheitlich pro Layer)

```
angeforderte Locale (z.B. de-AT)
  → Basissprache (de)
  → Default-Locale (de, UI-NFR-007 R-002)
  → erste vorhandene Locale / technischer Slug   (nie leerer Pflicht-String)
```

Beobachtbarkeit: FE Dev-Warnung (UI-NFR-007 R-009) + optionales BE-Metrik/Log-Event bei Miss.

---

## 5. Enum-Behandlung

- **Werte bleiben stabil & englisch** (`germination`, `vegetative`) — nie lokalisiert, nie Anzeigetext
  (UI-NFR-007 R-005, NFR-003). Kein `Literal`-Bruch nötig.
- **Labels** kommen aus dem i18n-Katalog `enums.<enumName>.<value>` — neue Sprache = neuer Katalog-Block,
  **keine** Änderung an `enums.py`/`types.ts`/Seeds.
- **Ein** zentraler FE-Helper `resolveEnumLabel(enumName, value)` statt 519 inline `t(\`enums.…\`)` —
  einheitliche Behandlung fehlender Labels (deterministischer Fallback statt roher Enum-Wert).

Enums sind damit bereits N-Sprachen-fähig; hier ist nur Konsolidierung (Helper), keine Modelländerung nötig.

---

## 6. Fehlermeldungen (P-2)

Der vorhandene `error_code`-Katalog (`common/exceptions.py`, 36 Codes) ist das Fundament:

- **Technisch** (Logs, 5xx, Diagnosen, `structlog`): **Englisch, nie lokalisiert.** `message`/`detail`
  bleiben englischer Entwickler-Kontext.
- **Nutzerseitig:** Response trägt `error_code`; die lokalisierte Meldung wird aus `errors.<error_code>`
  aufgelöst — clientseitig (i18n-Katalog) und/oder serverseitig (Locale-Resolution). Bereits vorbildlich:
  `AiDisabledError.message = "ai.disabled_for_tenant"`.
- **Deutsche Freitext-Literale** (Aquaponik REQ-026, Hardiness — ~10 Stellen) → `error_code` + Katalog-Key.
- Neue nutzerseitige Fehler **müssen** einen `error_code` + Katalog-Key vergeben.

Damit ist die lokalisierbare Meldungsmenge = der `error_code`-Namensraum (auditierbar, SSOT).

---

## 7. RAG- / Knowledge-Sprachstrategie

**Empfehlung: „eine kanonische Autorensprache pro Dokument, sprachmarkiert" + gesteuerte Antwortsprache**
— NICHT per-Sprache-Chunk-Duplikate im selben Vektorraum als Pflicht.

- **Autorenschicht:** jeder RAG-Chunk / Plant-Doc trägt `doc_language` (Chunks haben `language: de` schon;
  Plant-Docs bekommen Frontmatter-`language`). Weitere Sprachen sind **zusätzliche** sprachmarkierte
  Dokumente, kein Umbau.
- **Retrieval:** über die effektive Locale (R-112) mit Fallback auf die kanonische Wissenssprache. Das
  multilinguale Embedding-Modell (`multilingual-e5-large`) erlaubt Cross-Language-Retrieval, sodass eine
  Ziel-Locale ohne eigene Chunks trotzdem relevante DE-Quellen findet und das LLM in der Ziel-Locale
  antwortet — die heutige `doc_language="all"`-Praxis wird damit bewusst und dokumentiert, statt implizit.
- **Prompt-Sprache:** die hartkodierten DE/EN-Prompt-Dictionaries (`prompt_engine.py`,
  `diagnosis_analysis_engine.py`) werden zu **einem sprach-parametrisierten Template mit Default-Fallback**
  — Prompt-Text in einer Locale-Map/Template-Datei, nicht als `if language == "en"`-Zweig pro Codebasis.
- **FTS-Stemming:** `LANG_TO_TSCONFIG` wird um weitere Sprachen erweiterbar (Datentabelle statt hart);
  unbekannte Sprachen fallen sauber auf `simple`.
- **`Literal["de","en","all"]`** in KS-/Backend-Schemas → offener `str` mit Validierung gegen
  `SUPPORTED_LOCALES`.
- **Eval:** Benchmark-Set wird locale-parametrisierbar; EN-/weitere Benchmarks folgen als Datenarbeit
  (Non-Goal hier, aber der Mechanismus ist vorzusehen).
- **`language_mismatch_warning`:** entweder implementieren (Sprach-Detektion der Antwort) oder als tote
  Infrastruktur entfernen — der Rollout-Plan entscheidet.

**Warum nicht Pflicht-Duplikate pro Sprache im Store:** würde 61 Chunks + 210 Docs × N Sprachen erzwingen
(Pflege-Explosion) und widerspricht P-1 auf Content-Ebene. Cross-Language-Retrieval + gesteuerte
Antwortsprache liefert N-Sprachen-Abdeckung ohne N-fache Pflege; hochwertige native Übersetzungen bleiben
eine **optionale additive** Qualitätsstufe pro Sprache.

---

## 8. Alternativen erwogen

### A. Content-Modell

| Option | Beschreibung | Bewertung |
|--------|--------------|-----------|
| **A1 Locale-Map `dict[str,str]` inline am Dokument** ✅ **empfohlen** | Übersetzungen als Map am Entitätsdokument (ArangoDB-nativ, wie glossary) | Erfüllt P-1; kein Join; bereits im Code bewährt; Resolver trivial. **Gewählt.** |
| A2 Normalisierte Translation-Collection | separate `translations`-Collection (entity_key, field, locale, text) | Skaliert auch, aber Join/N+1 bei jeder Liste, mehr Komplexität, kein Vorbild im Code. Overkill für dokumentorientierte ArangoDB. |
| A3 Externer TMS / gettext-Kataloge für Stammdaten | PO-Files auch für Daten | Passt für UI-Strings (i18next hat das schon), aber nicht für redaktionelle Stammdaten mit Provenienz/Editier-UI. |

**Begründung A1:** dokumentorientierte DB + vorhandenes glossary/starter_kit-Muster + einfachster Resolver.
A2 bliebe als Option, falls je feingranulares Übersetzungs-Workflow-Tracking (pro Feld/Locale-Status)
gebraucht wird — dann additiv nachrüstbar, ohne A1 zu widersprechen.

### B. Locale-Resolution

| Option | Bewertung |
|--------|-----------|
| **B1 Eine Dependency, Prioritätskette (Param>User>Header>Default)** ✅ | konsolidiert 72 Stellen, wendet `user.locale` an. **Gewählt.** |
| B2 Status quo (Param je Endpoint, Default de) | verletzt P-3, `user.locale` bleibt ungenutzt. |
| B3 Nur `Accept-Language` | ignoriert gespeicherte Nutzerpräferenz + expliziten Export-Wunsch. |

### C. Fehlermeldungen

| Option | Bewertung |
|--------|-----------|
| **C1 `error_code`-Katalog trägt Lokalisierung, technisch EN** ✅ | nutzt vorhandenen Katalog, erfüllt P-2. **Gewählt.** |
| C2 Serverseitige Voll-Lokalisierung aller Messages (gettext) | doppelte Kataloge FE+BE, mehr Pflege, kein Mehrwert gegenüber Key-basiert. |

---

## 9. Nachweis der Skalierbarkeit (Definition-of-Done aus #568)

Hinzufügen einer 3./4./5. Sprache `fr`:

1. **Stammdaten:** `common_name.fr: …` als Datenzeile ergänzen — Schema unverändert (`$ref localized_text`
   akzeptiert jeden Sprachcode). **Kein** Diff an Domain-Modellen/DTOs.
2. **Enums:** Katalog-Block `enums.*` um `fr` ergänzen — **kein** Diff an `enums.py`/`types.ts`/Seeds.
3. **UI-Strings:** `i18n/locales/fr/translation.json` ergänzen — react-i18next lädt additiv.
4. **Fehler:** `errors.<code>`-Block um `fr` ergänzen — `error_code`-Menge unverändert.
5. **Locale-Resolution:** `fr` zu `SUPPORTED_LOCALES` — **eine** Konstante, kein Code-Zweig.
6. **RAG:** `fr`-Antwort via Prompt-Parameter + Cross-Language-Retrieval sofort; native `fr`-Chunks
   optional additiv.

→ **Keine** per-Entität-Schema-/Feld-Änderung, **kein** per-Sprache-Code-Zweig. P-1/P-2/P-3 erfüllt.

## 10. Offene Fragen (an den Rollout-Plan delegiert)

- Übergangsformat der Loader (Dual-Read `common_name` **und** `common_name_de`) — Dauer des Fensters.
- `SUPPORTED_LOCALES` als Env-Config vs. Konstante.
- `language_mismatch_warning`: implementieren oder entfernen.
- RTL-Einführungszeitpunkt (Theme + Emotion-RTL-Plugin) — erst bei erster RTL-Sprache oder proaktiv.
