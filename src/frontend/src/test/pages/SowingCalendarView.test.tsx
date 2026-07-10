import { cleanup, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import i18n from 'i18next';
import { renderWithProviders } from '../helpers';
import SowingCalendarView from '@/pages/kalender/SowingCalendarView';
import type { SowingCalendarEntry, SowingBar, FrostConfig } from '@/api/types';

// SowingCalendarView is a rendered UI unit driven entirely through props. It is
// exercised in isolation (no store slice needed) with realistic data anchored to
// the current year so the "today week" indicator is deterministic.

const Y = new Date().getFullYear();

function bar(overrides: Partial<SowingBar> = {}): SowingBar {
  return {
    phase: 'growth',
    color: '',
    start_date: `${Y}-04-01`,
    end_date: `${Y}-06-30`,
    label: 'Growth',
    ...overrides,
  };
}

function entry(overrides: Partial<SowingCalendarEntry> = {}): SowingCalendarEntry {
  return {
    species_key: 'sp-x',
    species_name: 'Speciesus',
    common_name: 'Common',
    link_species_key: 'sp-x',
    plant_category: 'outdoor_vegetable',
    bars: [bar()],
    ...overrides,
  };
}

const frost: FrostConfig = {
  last_frost_date: `${Y}-05-01`,
  first_frost_date: `${Y}-10-15`,
  eisheilige_date: `${Y}-05-15`,
};

/** A varied dataset touching several categories, phases and the favorite sort. */
function richEntries(): SowingCalendarEntry[] {
  return [
    entry({
      species_key: 'sp-tomato',
      species_name: 'Solanum lycopersicum',
      common_name: 'Tomato',
      plant_category: 'outdoor_vegetable',
      bars: [
        bar({ phase: 'indoor_sowing', start_date: `${Y}-03-01`, end_date: `${Y}-03-31` }),
        bar({ phase: 'outdoor_planting', start_date: `${Y}-05-16`, end_date: `${Y}-06-15` }),
        bar({ phase: 'harvest', color: '#123456', start_date: `${Y}-08-01`, end_date: `${Y}-09-30` }),
      ],
    }),
    entry({
      species_key: 'sp-basil',
      species_name: 'Ocimum basilicum',
      common_name: 'Basil',
      plant_category: 'herb',
      bars: [bar({ phase: 'outdoor_planting', start_date: `${Y}-05-16`, end_date: `${Y}-07-31` })],
    }),
    // common_name empty -> falls back to species_name; indoor category -> isIndoor true.
    entry({
      species_key: 'sp-ficus',
      species_name: 'Ficus',
      common_name: '',
      plant_category: 'indoor_houseplant',
      bars: [bar({ phase: 'germination', start_date: `${Y}-01-10`, end_date: `${Y}-02-10` })],
    }),
    // No category -> isIndoor derived from bars (no indoor_sowing / outdoor_planting bar).
    entry({
      species_key: 'sp-wild',
      species_name: 'Wildus',
      common_name: 'Wild',
      plant_category: null,
      bars: [bar({ phase: 'flowering', start_date: `${Y}-06-01`, end_date: `${Y}-07-15` })],
    }),
  ];
}

describe('SowingCalendarView', () => {
  beforeEach(() => {
    i18n.changeLanguage('en');
  });
  afterEach(() => {
    // Unmount before resetting the language: the file's afterEach runs before
    // testing-library's auto-cleanup (LIFO), so an i18n reset here would
    // otherwise re-render every still-mounted useTranslation() consumer
    // outside act(). Unmounting first makes the reset touch nothing.
    cleanup();
    i18n.changeLanguage('en');
  });

  it('shows an empty state when there are no entries', () => {
    renderWithProviders(
      <SowingCalendarView
        entries={[]}
        frostConfig={frost}
        year={Y}
        favorites={new Set()}
        onToggleFavorite={vi.fn()}
        showFavoritesOnly={false}
      />,
    );
    expect(
      screen.getByText(i18n.t('pages.calendar.sowingCalendar.noData')),
    ).toBeInTheDocument();
  });

  it('renders frost chips, species rows and the favorite-first sort order', () => {
    renderWithProviders(
      <SowingCalendarView
        entries={richEntries()}
        frostConfig={frost}
        year={Y}
        favorites={new Set(['sp-basil'])}
        onToggleFavorite={vi.fn()}
        showFavoritesOnly={false}
      />,
    );

    // Frost info chips derived from frostConfig ("Ice Saints" also appears in the
    // always-mounted legend, so match at least one occurrence).
    expect(screen.getByText(new RegExp(i18n.t('pages.calendar.sowingCalendar.lastFrost')))).toBeInTheDocument();
    expect(screen.getAllByText(new RegExp(i18n.t('pages.calendar.sowingCalendar.eisheilige'))).length).toBeGreaterThan(0);

    // Every species row renders; common_name falls back to species_name for Ficus.
    expect(screen.getByText('Tomato')).toBeInTheDocument();
    expect(screen.getByText('Basil')).toBeInTheDocument();
    expect(screen.getByText('Ficus')).toBeInTheDocument();
    expect(screen.getByText('Wild')).toBeInTheDocument();

    // Favorite (Basil) is sorted before the alphabetically-first non-favorite (Ficus).
    const names = screen.getAllByText(/Tomato|Basil|Ficus|Wild/).map((n) => n.textContent);
    expect(names.indexOf('Basil')).toBeLessThan(names.indexOf('Ficus'));
  });

  it('toggles the collapsible phase legend', async () => {
    const user = userEvent.setup();
    renderWithProviders(
      <SowingCalendarView
        entries={richEntries()}
        frostConfig={frost}
        year={Y}
        favorites={new Set()}
        onToggleFavorite={vi.fn()}
        showFavoritesOnly={false}
      />,
    );

    const legendToggle = screen.getByRole('button', {
      name: new RegExp(i18n.t('pages.calendar.sowingCalendar.legend')),
    });
    expect(legendToggle).toHaveAttribute('aria-expanded', 'false');
    await user.click(legendToggle);
    expect(legendToggle).toHaveAttribute('aria-expanded', 'true');
    // A phase that is present in the data appears in the legend.
    expect(
      screen.getByText(i18n.t('pages.calendar.sowingCalendar.indoorSowing')),
    ).toBeInTheDocument();
  });

  it('filters rows by plant category and clears the filter again', async () => {
    const user = userEvent.setup();
    renderWithProviders(
      <SowingCalendarView
        entries={richEntries()}
        frostConfig={frost}
        year={Y}
        favorites={new Set()}
        onToggleFavorite={vi.fn()}
        showFavoritesOnly={false}
      />,
    );

    // Three distinct categories -> the category filter chips are shown.
    const vegChip = screen.getByText(i18n.t('enums.plantCategory.outdoor_vegetable'));
    await user.click(vegChip);
    // Only the vegetable row (Tomato) remains.
    expect(screen.getByText('Tomato')).toBeInTheDocument();
    expect(screen.queryByText('Basil')).toBeNull();
    expect(screen.queryByText('Ficus')).toBeNull();

    // The "clear" chip resets the category filter and restores every row.
    await user.click(screen.getByTestId('sowing-category-filter-clear'));
    expect(screen.getByText('Basil')).toBeInTheDocument();
    expect(screen.getByText('Ficus')).toBeInTheDocument();
  });

  it('re-selecting the same category chip removes it from the filter', async () => {
    const user = userEvent.setup();
    renderWithProviders(
      <SowingCalendarView
        entries={richEntries()}
        frostConfig={frost}
        year={Y}
        favorites={new Set()}
        onToggleFavorite={vi.fn()}
        showFavoritesOnly={false}
      />,
    );

    const vegChip = screen.getByText(i18n.t('enums.plantCategory.outdoor_vegetable'));
    await user.click(vegChip);
    expect(screen.queryByText('Basil')).toBeNull();
    // Toggling the same category off restores the full list.
    await user.click(screen.getByText(i18n.t('enums.plantCategory.outdoor_vegetable')));
    expect(screen.getByText('Basil')).toBeInTheDocument();
  });

  it('restricts the list to favorites when showFavoritesOnly is set', () => {
    renderWithProviders(
      <SowingCalendarView
        entries={richEntries()}
        frostConfig={frost}
        year={Y}
        favorites={new Set(['sp-basil'])}
        onToggleFavorite={vi.fn()}
        showFavoritesOnly
      />,
    );
    expect(screen.getByText('Basil')).toBeInTheDocument();
    expect(screen.queryByText('Tomato')).toBeNull();
  });

  it('invokes onToggleFavorite for the clicked species row', async () => {
    const onToggleFavorite = vi.fn();
    const user = userEvent.setup();
    renderWithProviders(
      <SowingCalendarView
        entries={richEntries()}
        frostConfig={frost}
        year={Y}
        favorites={new Set(['sp-basil'])}
        onToggleFavorite={onToggleFavorite}
        showFavoritesOnly={false}
      />,
    );

    // Rows are favorite-first, so the first star button belongs to Basil.
    const starButtons = screen.getAllByLabelText(
      i18n.t('pages.calendar.sowingCalendar.toggleFavorite'),
    );
    await user.click(starButtons[0]);
    expect(onToggleFavorite).toHaveBeenCalledWith('sp-basil');
  });

  it('renders without frost information and without category chips for a single category', () => {
    const singleCategory: SowingCalendarEntry[] = [
      entry({ species_key: 'sp-1', common_name: 'Alpha', plant_category: 'herb' }),
      entry({ species_key: 'sp-2', common_name: 'Beta', plant_category: 'herb' }),
    ];
    renderWithProviders(
      <SowingCalendarView
        entries={singleCategory}
        frostConfig={null}
        year={Y - 1}
        favorites={new Set()}
        onToggleFavorite={vi.fn()}
        showFavoritesOnly={false}
      />,
    );

    // frostConfig null -> no frost chips.
    expect(screen.queryByText(new RegExp(i18n.t('pages.calendar.sowingCalendar.lastFrost')))).toBeNull();
    // A single used category -> the category filter group is not rendered.
    expect(
      screen.queryByRole('group', { name: i18n.t('pages.calendar.sowingCalendar.filterByCategory') }),
    ).toBeNull();
    expect(screen.getByText('Alpha')).toBeInTheDocument();
  });
});
