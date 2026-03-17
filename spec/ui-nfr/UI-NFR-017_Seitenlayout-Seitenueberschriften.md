---

ID: UI-NFR-017
Titel: Seitenlayout & Seitenueberschriften
Kategorie: UI-Verhalten Unterkategorie: Seitenlayout, Page-Header, Titel, Detail-Seiten, Listen-Seiten
Technologie: React, TypeScript, MUI, Flutter
Status: Entwurf
Prioritaet: Hoch
Version: 1.0
Autor: Business Analyst - Agrotech
Datum: 2026-03-17
Tags: [seitenlayout, page-header, seitentitel, detail-page, list-page, page-title, chips, actions, tabs]
Abhaengigkeiten: [UI-NFR-001, UI-NFR-006, UI-NFR-010]
Betroffene Module: [Frontend, Mobile]
---

# UI-NFR-017: Seitenlayout & Seitenueberschriften

> **Motivation:** Ohne verbindliche Vorgaben fuer Seitenueberschriften entstehen inkonsistente Header-Bereiche: Titel und Chips auf unterschiedlichen Hoehen, uneinheitliche Abstande, mal Favoriten-Icon neben dem Titel, mal darunter, mal gar nicht. Das wirkt lieblos und unprofessionell. Dieses Dokument definiert verbindliche Patterns fuer alle Seitentypen.

## 1. Business Case

### 1.1 User Story

**Als** Endanwender
**moechte ich** auf jeder Seite sofort erkennen wo ich bin und welche Aktionen verfuegbar sind
**um** mich sicher und effizient in der Anwendung zu bewegen.

**Als** Endanwender
**moechte ich** dass alle Seiten die gleiche visuelle Struktur haben
**um** die Anwendung als zusammenhaengendes Produkt wahrzunehmen.

**Als** Frontend-Entwickler
**moechte ich** klare, wiederverwendbare Patterns fuer Seiten-Header
**um** neue Seiten schnell und konsistent umzusetzen.

### 1.2 Geschaeftliche Motivation

1. **Wiedererkennung** -- Konsistente Header vermitteln Professionalitaet und erleichtern die Orientierung
2. **Entwicklungsgeschwindigkeit** -- Definierte Patterns vermeiden Einzelfall-Entscheidungen bei jeder neuen Seite
3. **Barrierefreiheit** -- Einheitliche Heading-Hierarchie verbessert die Navigation mit Screenreadern
4. **Wartbarkeit** -- Aenderungen am Header-Layout wirken sich ueber eine zentrale Komponente auf alle Seiten aus

---

## 2. PageTitle-Komponente

### 2.1 Grundregeln

| # | Regel | Stufe |
|---|-------|-------|
| R-001 | Jede Seite MUSS genau eine `PageTitle`-Komponente enthalten, die den `document.title` und die sichtbare H1-Ueberschrift setzt. | MUSS |
| R-002 | `PageTitle` MUSS als `<Typography variant="h4" component="h1">` gerendert werden. Es DARF kein weiteres `<h1>` auf der Seite existieren. | MUSS |
| R-003 | `PageTitle` MUSS ein optionales `sx`-Prop akzeptieren, um den Default-Margin (`mb: 3`) im Kontext von Inline-Headern ueberschreiben zu koennen. | MUSS |
| R-004 | Der Default-Margin von `PageTitle` (`mb: 3` = 24px) DARF NUR ueberschrieben werden, wenn der Titel in einem Flex-Container mit anderen Elementen (Icons, Chips) auf der gleichen Zeile steht. | MUSS |

### 2.2 Implementierung

```tsx
// components/layout/PageTitle.tsx
interface PageTitleProps {
  title: string;
  sx?: SxProps<Theme>;
}

export default function PageTitle({ title, sx }: PageTitleProps) {
  useEffect(() => {
    document.title = `${title} — Kamerplanter`;
    return () => { document.title = 'Kamerplanter'; };
  }, [title]);

  return (
    <Typography variant="h4" component="h1"
      sx={{ mb: 3, ...sx as object }}
      data-testid="page-title"
    >
      {title}
    </Typography>
  );
}
```

---

## 3. Page-Header-Patterns

Die Anwendung kennt vier verbindliche Header-Patterns. Jede Seite MUSS eines dieser Patterns verwenden.

### 3.1 Pattern A: Solo-Titel

Fuer einfache Seiten ohne Meta-Informationen oder Aktionen im Header.

| # | Regel | Stufe |
|---|-------|-------|
| R-005 | Pattern A SOLL nur fuer Dashboard-Seiten und einfache Uebersichtsseiten ohne Entity-Kontext verwendet werden. | SOLL |

```
┌──────────────────────────────────────────────────────────────┐
│                                                              │
│  Pflanzen-Pflege                                             │
│                                                              │
│  [Seiteninhalt...]                                          │
└──────────────────────────────────────────────────────────────┘
```

```tsx
<PageTitle title={t('pages.pflege.title')} />
```

### 3.2 Pattern B: Titel + Aktionen

Fuer Listen-Seiten und einfache Detail-Seiten. Titel links, Aktions-Buttons rechts.

| # | Regel | Stufe |
|---|-------|-------|
| R-006 | Pattern B MUSS einen aeusseren Flex-Container mit `justifyContent: 'space-between'` und `alignItems: 'flex-start'` verwenden. | MUSS |
| R-007 | Der Titel DARF in Pattern B seinen Default-Margin behalten (`mb: 3`), da er nicht inline mit kleinen Elementen steht. | SOLL |
| R-008 | Aktions-Buttons MUESSEN rechtsbuendig stehen und vertikal am oberen Rand des Titels ausgerichtet sein (`alignItems: 'flex-start'`). | MUSS |
| R-009 | Destruktive Aktionen (Loeschen) MUESSEN `variant="outlined" color="error"` verwenden. | MUSS |

```
┌──────────────────────────────────────────────────────────────┐
│                                                              │
│  Standort: Mein Garten                        [🗑 Loeschen] │
│                                                              │
│  [Tabs / Seiteninhalt...]                                   │
└──────────────────────────────────────────────────────────────┘
```

```tsx
<Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', mb: 2 }}>
  <PageTitle title={site.name} />
  <Button variant="outlined" color="error" startIcon={<DeleteIcon />}>
    {t('common.delete')}
  </Button>
</Box>
```

### 3.3 Pattern C: Titel mit Meta-Zeile + Aktionen

Fuer Detail-Seiten mit Status-Chips, Tags, Hersteller-Angaben oder Favoriten-Icon. **Dies ist das Standard-Pattern fuer die meisten Detail-Seiten.**

| # | Regel | Stufe |
|---|-------|-------|
| R-010 | Pattern C MUSS den Titel und die Meta-Zeile als **zwei separate Zeilen** darstellen -- NIEMALS Titel und Chips in derselben Flex-Row. | MUSS |
| R-011 | **Zeile 1 (Titel-Zeile):** Enthaelt den Seitentitel (`PageTitle` mit `sx={{ mb: 0 }}`) und optional ein Favoriten-Icon (`IconButton`). Vertikale Ausrichtung: `alignItems: 'center'`. | MUSS |
| R-012 | **Zeile 2 (Meta-Zeile):** Enthaelt Chips, Badges, Hersteller-/Autor-Text und sonstige Meta-Informationen. Abstand zur Titel-Zeile: `mt: 0.5` (4px). Vertikale Ausrichtung: `alignItems: 'center'`. | MUSS |
| R-013 | Die Aktions-Buttons (Loeschen etc.) MUESSEN auf gleicher Hoehe mit der Titel-Zeile stehen, rechtsbuendig. | MUSS |
| R-014 | Der aeussere Container MUSS `alignItems: 'flex-start'` verwenden, damit die Aktions-Buttons nicht vertikal zentriert zwischen beiden Zeilen haengen. | MUSS |
| R-015 | Chips in der Meta-Zeile MUESSEN `size="small"` verwenden. | MUSS |
| R-016 | Der Hersteller-/Autor-Name in der Meta-Zeile MUSS als `Typography variant="body2" color="text.secondary"` dargestellt werden. | MUSS |

```
┌──────────────────────────────────────────────────────────────┐
│                                                              │
│  Big Bud  ☆                                   [🗑 Loeschen] │
│  [Tanksicher] [Booster]  Advanced Nutrients                  │
│                                                              │
│  [Details]  [Bestand]  [Bearbeiten]                         │
│  [Tab-Inhalt...]                                            │
└──────────────────────────────────────────────────────────────┘
```

```tsx
<Box sx={{
  display: 'flex',
  justifyContent: 'space-between',
  alignItems: 'flex-start',
  mb: 2,
  flexWrap: 'wrap',
  gap: 1,
}}>
  {/* Linke Seite: Titel + Meta */}
  <Box>
    {/* Zeile 1: Titel + Favorit */}
    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
      <PageTitle title={entity.name} sx={{ mb: 0 }} />
      <IconButton onClick={toggleFavorite} sx={{ color: isFav ? 'warning.main' : 'action.disabled' }}>
        {isFav ? <StarIcon /> : <StarBorderIcon />}
      </IconButton>
    </Box>
    {/* Zeile 2: Meta-Chips */}
    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, flexWrap: 'wrap', mt: 0.5 }}>
      <Chip label="Tanksicher" size="small" color="info" />
      <Chip label="Booster" size="small" variant="outlined" />
      <Typography variant="body2" color="text.secondary">Advanced Nutrients</Typography>
    </Box>
  </Box>
  {/* Rechte Seite: Aktionen */}
  <Button variant="outlined" color="error" startIcon={<DeleteIcon />}>
    {t('common.delete')}
  </Button>
</Box>
```

### 3.4 Pattern D: Listen-Seite mit Filter + Erstellen

Fuer Listen-/Uebersichtsseiten mit Such-/Filter-UI und Erstellen-Button.

| # | Regel | Stufe |
|---|-------|-------|
| R-017 | Pattern D MUSS den Titel links und den Erstellen-Button rechts positionieren. | MUSS |
| R-018 | Filter-/Such-UI SOLL unter dem Titel-Bereich stehen, nicht inline mit dem Titel. | SOLL |
| R-019 | Der Erstellen-Button MUSS `variant="contained"` und ein `startIcon={<AddIcon />}` verwenden. | MUSS |
| R-020 | Bei vorhandenen Filter-Buttons (z.B. Favoriten, Typ-Filter) SOLLEN diese als `IconButton` neben dem Erstellen-Button stehen. | SOLL |

```
┌──────────────────────────────────────────────────────────────┐
│                                                              │
│  Duengemittel                            [⭐] [+ Erstellen] │
│                                                              │
│  [Filter-Leiste / Suche...]                                 │
│  [Tabelle / Karten...]                                      │
└──────────────────────────────────────────────────────────────┘
```

```tsx
<Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', mb: 2, gap: 1 }}>
  <PageTitle title={t('pages.fertilizers.title')} />
  <Box sx={{ display: 'flex', gap: 1, alignItems: 'center' }}>
    <IconButton onClick={toggleFavFilter}>
      {favOnly ? <StarIcon color="warning" /> : <StarBorderIcon />}
    </IconButton>
    <Button variant="contained" startIcon={<AddIcon />} onClick={() => setCreateOpen(true)}>
      {t('common.create')}
    </Button>
  </Box>
</Box>
```

---

## 4. Vertikale Ausrichtung

| # | Regel | Stufe |
|---|-------|-------|
| R-021 | Elemente innerhalb einer Zeile (Titel-Zeile oder Meta-Zeile) MUESSEN mit `alignItems: 'center'` vertikal zentriert sein. | MUSS |
| R-022 | Der Favoriten-IconButton MUSS auf der **Baseline des Titels** stehen, nicht ueber oder unter dem Text. Dies wird durch `alignItems: 'center'` auf dem gemeinsamen Flex-Container erreicht. | MUSS |
| R-023 | Chips und Text in der Meta-Zeile MUESSEN alle auf gleicher vertikaler Hoehe stehen. Gemischte Groessen (`size="small"` Chips + `variant="body2"` Text) erfordern `alignItems: 'center'`. | MUSS |
| R-024 | Titel und Meta-Chips DUERFEN NICHT in derselben Flex-Row stehen, da der Groessenunterschied zwischen `h4`-Text (34px) und `small`-Chips (24px) eine saubere vertikale Ausrichtung verhindert. | MUSS |

---

## 5. Abstands-Regeln

| # | Regel | Stufe |
|---|-------|-------|
| R-025 | Der aeussere Header-Container MUSS `mb: 2` (16px) nach unten haben, bevor Tabs oder Seiteninhalt beginnen. | MUSS |
| R-026 | Zwischen Titel-Zeile und Meta-Zeile (Pattern C): `mt: 0.5` (4px). | MUSS |
| R-027 | Zwischen Header und Tabs: kein zusaetzlicher Abstand -- die Tabs haben eigenes `mb: 2`. | SOLL |
| R-028 | `gap: 1` (8px) zwischen Elementen innerhalb einer Zeile (Chips untereinander, Icon neben Titel). | MUSS |
| R-029 | `gap: 1` zwischen der linken Seite (Titel+Meta) und der rechten Seite (Aktionen) bei `flexWrap: 'wrap'`. | MUSS |

---

## 6. Favoriten-Icon

| # | Regel | Stufe |
|---|-------|-------|
| R-030 | Das Favoriten-Icon MUSS als `IconButton` neben dem Titel stehen (in der Titel-Zeile, Pattern C), NICHT in der Meta-Zeile. | MUSS |
| R-031 | Favorisiert: `StarIcon` mit `color: 'warning.main'`. Nicht favorisiert: `StarBorderIcon` mit `color: 'action.disabled'`. | MUSS |
| R-032 | Das Favoriten-Icon MUSS `aria-label` fuer Barrierefreiheit haben (z.B. `t('common.addFavorite')` / `t('common.removeFavorite')`). | MUSS |
| R-033 | Das Favoriten-Icon SOLL nur auf Detail-Seiten erscheinen, NICHT auf Listen-Seiten-Titeln (dort ggf. als Filter-Toggle). | SOLL |

---

## 7. Tabs unter dem Header

| # | Regel | Stufe |
|---|-------|-------|
| R-034 | Tabs MUESSEN direkt unter dem Header-Bereich stehen, ohne zusaetzlichen Abstand. | MUSS |
| R-035 | Tabs MUESSEN `sx={{ mb: 2 }}` verwenden, um Abstand zum Tab-Inhalt zu schaffen. | MUSS |
| R-036 | Tab-Labels MUESSEN als i18n-Schluessel verwaltet werden. | MUSS |
| R-037 | Tabs mit Zaehler (z.B. "Bestand (3)") SOLLEN `Badge` innerhalb des Tab-Labels verwenden. | SOLL |

---

## 8. Responsive Verhalten

| # | Regel | Stufe |
|---|-------|-------|
| R-038 | Auf kleinen Bildschirmen (xs) MUSS der Header `flexWrap: 'wrap'` verwenden, sodass Titel und Aktionen untereinander umbrechen. | MUSS |
| R-039 | Chips in der Meta-Zeile MUESSEN mit `flexWrap: 'wrap'` umbrechen koennen. | MUSS |
| R-040 | Der Loeschen-Button SOLL auf kleinen Bildschirmen als Icon-only (`IconButton`) dargestellt werden. | KANN |

---

## 9. Wireframe-Uebersicht: Alle vier Patterns

```
Pattern A: Solo                    Pattern B: Titel + Aktionen
┌────────────────────────┐         ┌────────────────────────────────────┐
│                        │         │                                    │
│  Dashboard-Titel       │         │  Entity-Name            [Aktion]  │
│                        │         │                                    │
│  [Inhalt...]           │         │  [Inhalt / Tabs...]               │
└────────────────────────┘         └────────────────────────────────────┘

Pattern C: Titel + Meta + Aktionen Pattern D: Liste + Filter + Erstellen
┌────────────────────────────────┐ ┌────────────────────────────────────┐
│                                │ │                                    │
│  Entity-Name  ☆      [Aktion] │ │  Listen-Titel        [⭐][+ Neu]  │
│  [Chip] [Chip]  Hersteller    │ │                                    │
│                                │ │  [Filter / Suche...]              │
│  [Tab1]  [Tab2]  [Tab3]       │ │  [Tabelle / Karten...]            │
│  [Tab-Inhalt...]              │ │                                    │
└────────────────────────────────┘ └────────────────────────────────────┘
```

---

## 10. Akzeptanzkriterien

### Definition of Done

- [ ] `PageTitle`-Komponente akzeptiert optionales `sx`-Prop
- [ ] Alle Detail-Seiten mit Chips/Meta verwenden Pattern C (zweizeilig)
- [ ] Kein `h4`-Titel steht in derselben Flex-Row wie `small`-Chips
- [ ] Favoriten-Icon steht immer in der Titel-Zeile, nie in der Meta-Zeile
- [ ] Alle Abstande entsprechen den Regeln aus Abschnitt 5
- [ ] Responsive: Header bricht auf `xs` sauber um
- [ ] Visueller Review: Titel, Chips und Icons stehen auf korrekter vertikaler Hoehe

### Pruefmatrix Detail-Seiten

| Seite | Pattern | Favorit | Chips | Tabs | Aktion |
|-------|---------|---------|-------|------|--------|
| FertilizerDetailPage | C | Ja | Type, TankSafe, Organic + Brand | 3 | Loeschen |
| NutrientPlanDetailPage | C | Ja | Template, CycleRestart | 3+ | Loeschen |
| PlantInstanceDetailPage | C | Nein | Phase, Species | 5+ | Remove, Transition |
| SpeciesDetailPage | C | Ja | Family | 3+ | Loeschen |
| SiteDetailPage | B | Nein | -- | 2+ | Loeschen |
| TankDetailPage | B | Nein | -- | 4+ | Loeschen |
| PlantingRunDetailPage | C | Nein | Status, RunType | 4+ | Loeschen |
| HarvestBatchDetailPage | B/C | Nein | Quality Grade | 2+ | -- |
| WorkflowDetailPage | B | Nein | System-Chip | 2+ | Loeschen |

---

## 11. Risiken bei Nicht-Einhaltung

| Risiko | Auswirkung | Eintrittswahrscheinlichkeit |
|--------|-----------|---------------------------|
| Inkonsistente Header-Layouts | Unprofessioneller Eindruck, Nutzer-Verwirrung | Hoch (ohne Vorgaben) |
| Titel und Chips auf unterschiedlichen Hoehen | "Liebloser" Eindruck, visuelles Chaos | Hoch (bereits aufgetreten) |
| Fehlende `aria-label` auf Favoriten-Icons | WCAG-Verletzung | Mittel |
| Unterschiedliche Margin/Padding zwischen Seiten | Inkonsistente Whitespace-Verteilung | Hoch (ohne zentrale Komponente) |

---

**Dokumenten-Ende**

**Version**: 1.0
**Status**: Entwurf
**Letzte Aktualisierung**: 2026-03-17
**Review**: Pending
**Genehmigung**: Pending
