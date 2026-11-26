import { deDE, enUS, type Localization } from '@mui/material/locale';
import { normalizeNameLanguage } from '@/utils/plantDisplay';

/**
 * MUI's own component texts per UI language (#3025 M14, audit L-03): the Autocomplete's
 * "Öffnen"/"Leeren"/"Keine Optionen", the TablePagination's "Zeilen pro Seite" and the
 * Pagination/Rating/Alert/Breadcrumbs labels. Without it they stay English in the German UI.
 *
 * German is the default and the fallback, as for the app's own strings.
 */
const MUI_LOCALES: Readonly<Record<string, Localization>> = { de: deDE, en: enUS };

export function muiLocaleFor(language: string | null | undefined): Localization {
  return MUI_LOCALES[normalizeNameLanguage(language)] ?? deDE;
}
