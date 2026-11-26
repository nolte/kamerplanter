import { act, render, screen } from '@testing-library/react';
import { afterEach, describe, expect, it } from 'vitest';
import Autocomplete from '@mui/material/Autocomplete';
import TablePagination from '@mui/material/TablePagination';
import TextField from '@mui/material/TextField';
import { deDE, enUS } from '@mui/material/locale';
import i18n from '@/i18n/i18n';
import { ThemeContextProvider } from '@/theme/ThemeContext';
import { muiLocaleFor } from '@/theme/muiLocale';

/**
 * #3025 M14 (audit L-03) — MUI's own texts ("Open", "Clear", "No options", "Rows per page")
 * follow the UI language, including a switch at runtime, because `ThemeContextProvider`
 * merges `deDE`/`enUS` into the theme and re-renders on `languageChanged`.
 */

function Probe() {
  return (
    <>
      <Autocomplete
        options={['Basilikum']}
        value="Basilikum"
        renderInput={(params) => <TextField {...params} label="Art" />}
      />
      <TablePagination component="div" count={30} page={0} rowsPerPage={10} onPageChange={() => {}} />
    </>
  );
}

describe('MUI component locale follows the UI language (L-03)', () => {
  const initial = i18n.language;

  afterEach(async () => {
    await act(async () => {
      await i18n.changeLanguage(initial);
    });
  });

  it('maps the UI language to the MUI locale, German by default', () => {
    expect(muiLocaleFor('de')).toBe(deDE);
    expect(muiLocaleFor('de-AT')).toBe(deDE);
    expect(muiLocaleFor('en')).toBe(enUS);
    expect(muiLocaleFor('en-GB')).toBe(enUS);
    expect(muiLocaleFor('fr')).toBe(deDE);
    expect(muiLocaleFor(undefined)).toBe(deDE);
  });

  it('renders German MUI texts and switches to English at runtime', async () => {
    await act(async () => {
      await i18n.changeLanguage('de');
    });
    render(
      <ThemeContextProvider>
        <Probe />
      </ThemeContextProvider>,
    );

    expect(screen.getByRole('button', { name: 'Öffnen' })).toBeInTheDocument();
    expect(screen.getByText('Zeilen pro Seite:')).toBeInTheDocument();

    await act(async () => {
      await i18n.changeLanguage('en');
    });

    expect(screen.getByRole('button', { name: 'Open' })).toBeInTheDocument();
    expect(screen.getByText('Rows per page:')).toBeInTheDocument();
    expect(screen.queryByRole('button', { name: 'Öffnen' })).toBeNull();
  });
});
