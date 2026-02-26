# UI-NFR Terminologie-Glossar

Dieses Glossar definiert die kanonischen Begriffe für wiederkehrende UI-Konzepte. Alle UI-NFR-Dokumente MÜSSEN die hier festgelegten Begriffe verwenden, um Konsistenz zu gewährleisten.

---

## Benachrichtigungen & Feedback

| Kanonischer Begriff | Definition | MUI-Komponente | Nicht verwenden |
|---|---|---|---|
| **Snackbar** | Kurze, zeitgesteuerte Benachrichtigung am unteren Bildschirmrand. Zeigt Erfolg, Info, Warnung oder Fehler an. | `Snackbar` + `Alert` | Toast, Notification, Banner |
| **Inline-Fehlermeldung** | Fehlermeldung direkt unterhalb eines Formularfeldes. | `FormHelperText` | Feldwarnung, Error-Text |
| **Bestätigungsdialog** | Modaler Dialog, der vor destruktiven Aktionen eine explizite Bestätigung verlangt. | `Dialog` | Confirm-Dialog, Warndialog, Popup |

## Ladezustände

| Kanonischer Begriff | Definition | MUI-Komponente | Nicht verwenden |
|---|---|---|---|
| **Skeleton** | Platzhalter-Animation, die die Struktur des geladenen Inhalts vorwegnimmt. Wird für initiales Laden von Seiten, Listen und Karten verwendet. | `Skeleton` | Skeleton-Screen, Skeleton-Loader, Shimmer |
| **Spinner** | Rotierender Indikator für kurze, fokussierte Ladeoperationen (z.B. Button-Ladezustand). | `CircularProgress` | Ladekreis, Loading-Wheel |
| **Fortschrittsanzeige** | Linearer Balken, der den Fortschritt einer längeren Operation (> 3s) darstellt. | `LinearProgress` | Progress-Bar, Ladebalken |
| **Button-Ladezustand** | Zustand eines Buttons während einer asynchronen Aktion: deaktiviert + Spinner. | `LoadingButton` (MUI Lab) | Loading-State, Submitting-State |

## Leerzustände

| Kanonischer Begriff | Definition | MUI-Komponente | Nicht verwenden |
|---|---|---|---|
| **Leerzustand** | Anzeige, wenn keine Daten vorhanden sind (erstmaliger Zustand). Enthält erklärenden Text und Call-to-Action. | Custom (`EmptyState`) | Empty State, Null-State, Blank-State |
| **Keine-Ergebnisse-Hinweis** | Anzeige, wenn eine Suche oder ein Filter keine Treffer liefert. Enthält den Suchbegriff und eine „Filter zurücksetzen"-Option. | Custom (`EmptyState` mit Variante) | No-Results, Kein-Treffer |

## Formularelemente

| Kanonischer Begriff | Definition | MUI-Komponente | Nicht verwenden |
|---|---|---|---|
| **Dropdown** | Auswahlfeld mit vorgegebenen Optionen (≤ 20 Optionen). | `Select` | Pulldown, Combobox (wenn nicht durchsuchbar) |
| **Autocomplete** | Durchsuchbares Auswahlfeld (> 20 Optionen) mit Filterfunktion. | `Autocomplete` | Combobox, Typeahead, Suchauswahl |
| **Pflichtfeld** | Formularfeld, das ausgefüllt werden muss. Gekennzeichnet durch `*` im Label. | `TextField` mit `required` | Mandatory, Required (im UI-Text) |
| **Hilfetext** | Erklärender Text unterhalb eines Formularfeldes. | `helperText`-Prop | Hinweistext, Tooltip-Text |

## Navigation

| Kanonischer Begriff | Definition | MUI-Komponente | Nicht verwenden |
|---|---|---|---|
| **Breadcrumb** | Navigationspfad, der die Seitenhierarchie abbildet. | `Breadcrumbs` | Brotkrumen, Pfadnavigation |
| **Seitennavigation** | Haupt-Navigationsmenü (Sidebar oder Topbar). | `Drawer` / `AppBar` | Hauptmenü, Menüleiste |

## Tabellen

| Kanonischer Begriff | Definition | MUI-Komponente | Nicht verwenden |
|---|---|---|---|
| **Sortierindikator** | Pfeil im Spaltenheader, der die aktuelle Sortierrichtung anzeigt. | `TableSortLabel` | Sortierpfeil, Sort-Icon |
| **Pagination** | Seitenumbruch-Navigation unterhalb einer Tabelle. | `TablePagination` | Paging, Seitenwechsel, Blättern |
| **Filter-Chip** | Visueller Indikator für einen aktiven Filter mit Löschen-Option. | `Chip` mit `onDelete` | Filter-Tag, Filter-Badge |

---

**Letzte Aktualisierung**: 2026-02-26
