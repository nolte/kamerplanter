---
name: check-ui-crud
description: "Prueft Frontend-Implementierungen auf NFR-010-Konformitaet: Vollstaendige CRUD-Abdeckung (Create/Read/Update/Delete) fuer alle Entitaeten, Delete-Bestaetigungsdialog, Dirty-State-Warnung, Formularvalidierung, Listenansicht mit Pagination/Suche. Nutze diesen Skill nach Implementierung neuer Frontend-Seiten."
argument-hint: "[Entitaets-Name oder REQ-nnn, z.B. BotanicalFamily oder REQ-001]"
disable-model-invocation: true
---

# UI-CRUD-Check (NFR-010): $ARGUMENTS

## Schritt 1: Frontend-Dateien laden

Falls `$ARGUMENTS` ein REQ-Identifier:
- Lies die REQ-Datei `spec/req/REQ-{nnn}_*.md` — extrahiere alle Entitaets-Namen

Falls `$ARGUMENTS` ein Entitaets-Name:
- Suche zugehoerige Pages: Glob `src/frontend/src/pages/**/*$ARGUMENTS*.tsx`

Lade **parallel**:
1. Detail-/Liste-Pages fuer die Entitaet
2. Create/Edit-Dialoge (Glob `src/frontend/src/pages/**/*Dialog*.tsx` oder `*Form*.tsx`)
3. `spec/nfr/NFR-010_UI-Pflegemasken-Listenansichten.md` erste 80 Zeilen (CRUD-Anforderungen)
4. `spec/style-guides/FRONTEND.md` erste 50 Zeilen (Komponenten-Patterns)

## Schritt 2: CRUD-Operationen pruefen

Prüfe fuer jede Entitaet ob alle 4 Operationen vorhanden sind:

| Operation | Erwartetes UI-Element | Minimal-Anforderungen |
|-----------|----------------------|----------------------|
| **Create** | Dialog oder eigene Seite | Einleitungstext, Pflichtfelder*, Zod-Validierung, Success-Toast |
| **Read** | Detail-Seite oder Detail-Section | Alle Felder sichtbar (read-only) |
| **Update** | Edit-Formular | Dirty-State-Warnung bei Navigation weg, Pre-Fill mit bestehenden Werten |
| **Delete** | Button + Bestaetigungsdialog | Explizite Bestaetigung, Entitaets-Name im Dialog |

## Schritt 3: Create-Dialog-Qualitaet pruefen (NFR-010 §2.2)

```tsx
// ✅ Pflicht: Einleitungstext
<Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
  Legen Sie eine neue Botanische Familie an. ...
</Typography>

// ✅ Pflicht: Formularvalidierung mit Zod
const schema = z.object({
  name: z.string().min(1, "Name ist erforderlich"),
  ...
});

// ✅ Pflicht: Submit-Button deaktiviert bei Fehler
<Button disabled={!isValid || isSubmitting}>Erstellen</Button>

// ✅ Pflicht: Success-Toast
enqueueSnackbar("Erfolgreich erstellt", { variant: "success" });

// ✅ Pflicht: API-Fehler feldspezifisch anzeigen
// Fehler aus NFR-006 ErrorResponse.details auf Formularfelder mappen
```

## Schritt 4: Listenansicht-Qualitaet pruefen (NFR-010 §3)

```tsx
// ✅ Pflicht-Features:
// - Tabellarische Darstellung (MUI DataGrid oder Table)
// - Sortierung (mindestens nach Name/Datum)
// - Pagination (server-seitig bevorzugt)
// - Suchfeld / Filtermoeglichkeit
// - Click → Detail-Seite Navigation
// - Empty State (kein "leere Tabelle" ohne Hinweis)
// - Loading State (Skeleton oder CircularProgress)
```

## Schritt 5: Delete-Dialog-Qualitaet pruefen

```tsx
// ✅ KORREKT — Explizite Bestaetigung mit Entitaets-Name
<Dialog>
  <DialogTitle>Familie loeschen?</DialogTitle>
  <DialogContent>
    Moechten Sie die Familie "{entity.name}" wirklich loeschen?
    Diese Aktion kann nicht rueckgaengig gemacht werden.
  </DialogContent>
  <DialogActions>
    <Button onClick={onClose}>Abbrechen</Button>
    <Button color="error" onClick={handleDelete}>Loeschen</Button>
  </DialogActions>
</Dialog>

// ❌ FALSCH — window.confirm
if (confirm("Wirklich loeschen?")) deleteEntity(id);
```

## Schritt 6: Dirty-State-Warnung pruefen

```tsx
// ✅ Pflicht bei Edit-Formularen
const isDirty = form.formState.isDirty;

// Warnung bei Navigation weg (useBlocker oder beforeunload)
useEffect(() => {
  if (isDirty) {
    window.onbeforeunload = () => "Ungespeicherte Aenderungen vorhanden.";
  }
  return () => { window.onbeforeunload = null; };
}, [isDirty]);
```

## Schritt 7: REQ-021 Kompatibilitaet (Erfahrungsstufen)

Prüfe ob die Seite `ExpertiseFieldWrapper` / `ShowAllFieldsToggle` verwendet:
- Felder im Einsteiger-Modus ausgeblendet? → Muss ueber "Mehr anzeigen" erreichbar sein
- Auto-gefuellte Felder mit "Automatisch gesetzt"-Badge gekennzeichnet?

## Schritt 8: Report ausgeben

```markdown
# UI-CRUD-Review: {Entitaet/REQ}

## CRUD-Abdeckung
| Entitaet | Create | Read | Update | Delete |
|----------|--------|------|--------|--------|
{Zeilen pro Entitaet}

## Create-Dialog-Qualitaet
{Einleitungstext: ✅/❌ | Zod-Validierung: ✅/❌ | API-Fehler-Mapping: ✅/❌ | Success-Toast: ✅/❌}

## Listenansicht-Qualitaet
{Sortierung: ✅/❌ | Pagination: ✅/❌ | Suche: ✅/❌ | Empty/Loading State: ✅/❌}

## UX-Qualitaet
{Delete-Dialog: ✅/❌ | Dirty-State-Warnung: ✅/❌ | REQ-021-konform: ✅/❌}

## Fehlende Implementierungen (priorisiert)
{Nummerierte Liste}

## Bewertung
- ✅ NFR-010-konform / ❌ {N} Luecken identifiziert
```
