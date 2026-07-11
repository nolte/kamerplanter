import { screen, waitFor, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import { http, HttpResponse } from 'msw';
import i18n from 'i18next';
import { useSearchParams } from 'react-router-dom';
import { renderWithProviders } from '../helpers';
import { server } from '../mocks/server';

const mockNavigate = vi.fn();
vi.mock('react-router-dom', async (orig) => {
  const actual = await orig<typeof import('react-router-dom')>();
  return { ...actual, useNavigate: () => mockNavigate };
});

import OverwinteringListPage from '@/pages/ueberwinterung/OverwinteringListPage';

/** Renders the page plus a probe that mirrors the current URL query string. */
function PageWithUrlProbe() {
  const [params] = useSearchParams();
  return (
    <>
      <div data-testid="url-search">{params.toString()}</div>
      <OverwinteringListPage />
    </>
  );
}

const listUrls = [
  '/api/v1/overwintering-profiles',
  '/api/v1/t/:tenant/overwintering-profiles',
];

const deleteUrls = [
  '/api/v1/overwintering-profiles/:key',
  '/api/v1/t/:tenant/overwintering-profiles/:key',
];

function useProfiles(rows: Record<string, unknown>[]) {
  server.use(...listUrls.map((u) => http.get(u, () => HttpResponse.json(rows))));
}

function useDeleteResponse(status: number) {
  server.use(
    ...deleteUrls.map((u) =>
      http.delete(u, () => new HttpResponse(null, { status })),
    ),
  );
}

function enableMobileViewport() {
  vi.stubGlobal(
    'matchMedia',
    vi.fn().mockReturnValue({
      matches: true,
      addEventListener: vi.fn(),
      removeEventListener: vi.fn(),
      addListener: vi.fn(),
      removeListener: vi.fn(),
    } as unknown as MediaQueryList),
  );
}

const profile = {
  key: 'ow-1',
  plant_key: 'plant-1',
  planting_run_key: null,
  hardiness_zone_min: '7a',
  hardiness_rating: 'frost_free',
  winter_action: 'move_indoors',
  winter_action_month: 10,
  spring_action: 'move_outdoors',
  spring_action_month: 5,
  winter_quarter_key: null,
  winter_quarter_temp_min: 5,
  winter_quarter_temp_max: 12,
  winter_quarter_light: 'bright',
  winter_watering: 'minimal',
  storage_medium: null,
  storage_check_interval_days: null,
  tuber_status: null,
  notes: null,
  auto_generated: false,
  created_at: '2024-01-01T00:00:00Z',
  updated_at: null,
};

const runProfile = {
  ...profile,
  key: 'ow-2',
  plant_key: null,
  planting_run_key: 'run-77',
  hardiness_rating: 'needs_protection',
  winter_action: 'mulch',
  winter_action_month: 11,
  spring_action: null,
  spring_action_month: null,
  storage_medium: null,
  auto_generated: true,
};

const unlinkedProfile = {
  ...profile,
  key: 'ow-3',
  plant_key: null,
  planting_run_key: null,
  hardiness_rating: 'hardy',
  winter_action: 'none',
  winter_action_month: 12,
  auto_generated: false,
};

describe('OverwinteringListPage', () => {
  beforeEach(() => {
    i18n.changeLanguage('de');
    mockNavigate.mockClear();
  });

  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it('renders the page title', async () => {
    useProfiles([]);
    renderWithProviders(<OverwinteringListPage />);
    await waitFor(() => {
      expect(screen.getByText(i18n.t('pages.overwintering.title'))).toBeTruthy();
    });
  });

  it('loads a profile and shows its hardiness chip and subject name', async () => {
    useProfiles([profile]);
    renderWithProviders(<OverwinteringListPage />);

    await waitFor(() => {
      expect(screen.getByTestId('hardiness-chip-ow-1')).toBeTruthy();
    });
    // plant-1 resolves to the mocked plant name "Big Red (TOM-001)"
    expect(screen.getByText(/Big Red/)).toBeTruthy();
    expect(
      screen.getByText(i18n.t('enums.hardinessRating.frost_free')),
    ).toBeTruthy();
  });

  it('shows the empty state with a create action', async () => {
    useProfiles([]);
    renderWithProviders(<OverwinteringListPage />);
    await waitFor(() => {
      expect(screen.getByTestId('empty-state')).toBeTruthy();
    });
  });

  it('opens the create dialog when the create button is clicked', async () => {
    useProfiles([]);
    const user = userEvent.setup();
    renderWithProviders(<OverwinteringListPage />);

    const createButton = await screen.findByTestId('create-button');
    await user.click(createButton);

    expect(await screen.findByTestId('overwintering-dialog')).toBeTruthy();
    expect(screen.getByRole('dialog')).toBeTruthy();
  });

  it('renders the auto-generated chip and the planting-run subject fallback', async () => {
    useProfiles([runProfile]);
    renderWithProviders(<OverwinteringListPage />);

    await waitFor(() => {
      expect(screen.getByTestId('hardiness-chip-ow-2')).toBeTruthy();
    });
    // No plant_key → subjectLabel falls back to the planting_run_key.
    expect(screen.getAllByText('run-77').length).toBeGreaterThan(0);
    // auto_generated → the "Auto" chip is rendered.
    expect(
      screen.getAllByText(i18n.t('pages.overwintering.auto')).length,
    ).toBeGreaterThan(0);
  });

  it('renders an em dash when the profile has neither a plant nor a planting run', async () => {
    useProfiles([unlinkedProfile]);
    renderWithProviders(<OverwinteringListPage />);

    await waitFor(() => {
      expect(screen.getByTestId('hardiness-chip-ow-3')).toBeTruthy();
    });
    expect(screen.getAllByText('—').length).toBeGreaterThan(0);
  });

  it('opens the edit dialog when a row is clicked', async () => {
    useProfiles([profile]);
    const user = userEvent.setup();
    renderWithProviders(<OverwinteringListPage />);

    await user.click(await screen.findByText(/Big Red/));

    expect(await screen.findByTestId('overwintering-dialog')).toBeTruthy();
    expect(
      screen.getByText(i18n.t('pages.overwintering.edit')),
    ).toBeTruthy();
  });

  it('deletes a profile through the confirm dialog', async () => {
    useProfiles([profile]);
    useDeleteResponse(204);
    const user = userEvent.setup();
    renderWithProviders(<OverwinteringListPage />);

    await user.click(await screen.findByTestId('delete-ow-1'));

    const confirm = await screen.findByTestId('confirm-dialog-confirm');
    await user.click(confirm);

    await waitFor(() =>
      expect(screen.queryByTestId('confirm-dialog')).toBeNull(),
    );
  });

  it('surfaces an error when the delete request fails', async () => {
    useProfiles([profile]);
    useDeleteResponse(500);
    const user = userEvent.setup();
    renderWithProviders(<OverwinteringListPage />);

    await user.click(await screen.findByTestId('delete-ow-1'));
    await user.click(await screen.findByTestId('confirm-dialog-confirm'));

    // Failure still closes the confirm dialog (finally clears deleteTarget)
    // and reports the error via a notification.
    await waitFor(() =>
      expect(screen.queryByTestId('confirm-dialog')).toBeNull(),
    );
    expect(await screen.findByText(i18n.t('errors.server'))).toBeTruthy();
  });

  it('cancels the delete confirmation without calling the API', async () => {
    useProfiles([profile]);
    const user = userEvent.setup();
    renderWithProviders(<OverwinteringListPage />);

    await user.click(await screen.findByTestId('delete-ow-1'));
    await user.click(await screen.findByTestId('confirm-dialog-cancel'));

    await waitFor(() =>
      expect(screen.queryByTestId('confirm-dialog')).toBeNull(),
    );
  });

  it('jumps to the plant-instance detail page for a plant-bound profile', async () => {
    useProfiles([profile]);
    const user = userEvent.setup();
    renderWithProviders(<OverwinteringListPage />);

    const jump = await screen.findByTestId('goto-ow-1');
    await user.click(jump);

    expect(mockNavigate).toHaveBeenCalledWith(
      '/pflanzen/plant-instances/plant-1',
    );
  });

  it('jumps to the planting-run detail page for a run-bound profile', async () => {
    useProfiles([runProfile]);
    const user = userEvent.setup();
    renderWithProviders(<OverwinteringListPage />);

    const jump = await screen.findByTestId('goto-ow-2');
    await user.click(jump);

    expect(mockNavigate).toHaveBeenCalledWith(
      '/durchlaeufe/planting-runs/run-77',
    );
  });

  it('does not open the edit dialog when the jump icon is clicked', async () => {
    useProfiles([profile]);
    const user = userEvent.setup();
    renderWithProviders(<OverwinteringListPage />);

    await user.click(await screen.findByTestId('goto-ow-1'));

    // stopPropagation must prevent the row-click edit dialog from opening.
    expect(screen.queryByTestId('overwintering-dialog')).toBeNull();
    expect(mockNavigate).toHaveBeenCalledTimes(1);
  });

  it('hides the jump icon for a profile with neither plant nor run', async () => {
    useProfiles([unlinkedProfile]);
    renderWithProviders(<OverwinteringListPage />);

    await waitFor(() => {
      expect(screen.getByTestId('hardiness-chip-ow-3')).toBeTruthy();
    });
    expect(screen.queryByTestId('goto-ow-3')).toBeNull();
  });

  it('jumps via the mobile card action for a run-bound profile', async () => {
    enableMobileViewport();
    useProfiles([runProfile]);
    const user = userEvent.setup();
    renderWithProviders(<OverwinteringListPage />);

    const jump = await screen.findByTestId('goto-mobile-ow-2');
    await user.click(jump);

    expect(mockNavigate).toHaveBeenCalledWith(
      '/durchlaeufe/planting-runs/run-77',
    );
  });

  it('renders mobile cards and deletes via the mobile action', async () => {
    enableMobileViewport();
    useProfiles([runProfile]);
    useDeleteResponse(204);
    const user = userEvent.setup();
    renderWithProviders(<OverwinteringListPage />);

    // Mobile card layout renders the auto chip and the mobile delete button.
    const mobileDelete = await screen.findByTestId('delete-mobile-ow-2');
    expect(
      screen.getAllByText(i18n.t('pages.overwintering.auto')).length,
    ).toBeGreaterThan(0);

    await user.click(mobileDelete);
    await user.click(await screen.findByTestId('confirm-dialog-confirm'));

    await waitFor(() =>
      expect(screen.queryByTestId('confirm-dialog')).toBeNull(),
    );
  });
});

describe('OverwinteringListPage — faceted filters', () => {
  beforeEach(() => {
    i18n.changeLanguage('de');
    mockNavigate.mockClear();
  });

  afterEach(() => {
    vi.unstubAllGlobals();
  });

  // profile (ow-1): plant, frost_free, move_indoors, month 10, manual → "Big Red"
  // runProfile (ow-2): run-77, needs_protection, mulch, month 11, auto
  // unlinkedProfile (ow-3): neither, hardy, none, month 12, manual → "—"
  const allProfiles = [profile, runProfile, unlinkedProfile];

  /** Opens a multi-select facet and toggles a single option by its label. */
  async function pickOption(
    user: ReturnType<typeof userEvent.setup>,
    filterId: string,
    optionLabel: string | RegExp,
  ) {
    const control = screen.getByTestId(`column-filter-${filterId}`);
    const trigger = within(control).getByRole('combobox');
    await user.click(trigger);
    const listbox = await screen.findByRole('listbox');
    await user.click(
      within(listbox).getByRole('option', {
        name: typeof optionLabel === 'string' ? new RegExp(optionLabel) : optionLabel,
      }),
    );
    // Close the menu so subsequent queries are unambiguous.
    await user.keyboard('{Escape}');
  }

  it('filters by winter-hardiness rating (traffic light)', async () => {
    useProfiles(allProfiles);
    const user = userEvent.setup();
    renderWithProviders(<OverwinteringListPage />);

    await waitFor(() => expect(screen.getByTestId('hardiness-chip-ow-1')).toBeTruthy());

    await pickOption(user, 'hardiness', 'Schutz nötig');

    // Only the needs_protection run profile (ow-2) survives.
    await waitFor(() => expect(screen.queryByTestId('hardiness-chip-ow-1')).toBeNull());
    expect(screen.getByTestId('hardiness-chip-ow-2')).toBeTruthy();
    expect(screen.queryByTestId('hardiness-chip-ow-3')).toBeNull();
  });

  it('filters by winter action', async () => {
    useProfiles(allProfiles);
    const user = userEvent.setup();
    renderWithProviders(<OverwinteringListPage />);

    await waitFor(() => expect(screen.getByTestId('hardiness-chip-ow-2')).toBeTruthy());

    await pickOption(user, 'winter_action', 'Mulchen');

    await waitFor(() => expect(screen.queryByTestId('hardiness-chip-ow-1')).toBeNull());
    expect(screen.getByTestId('hardiness-chip-ow-2')).toBeTruthy();
    expect(screen.queryByTestId('hardiness-chip-ow-3')).toBeNull();
  });

  it('filters by winter-action month (data-derived options)', async () => {
    useProfiles(allProfiles);
    const user = userEvent.setup();
    renderWithProviders(<OverwinteringListPage />);

    await waitFor(() => expect(screen.getByTestId('hardiness-chip-ow-1')).toBeTruthy());

    // ow-1's action month is October.
    await pickOption(user, 'month', 'Oktober');

    await waitFor(() => expect(screen.queryByTestId('hardiness-chip-ow-2')).toBeNull());
    expect(screen.getByTestId('hardiness-chip-ow-1')).toBeTruthy();
    expect(screen.queryByTestId('hardiness-chip-ow-3')).toBeNull();
  });

  it('filters by origin (auto vs. manual)', async () => {
    useProfiles(allProfiles);
    const user = userEvent.setup();
    renderWithProviders(<OverwinteringListPage />);

    await waitFor(() => expect(screen.getByTestId('hardiness-chip-ow-1')).toBeTruthy());

    // Only the auto-generated run profile (ow-2) is automatic.
    await pickOption(user, 'origin', i18n.t('pages.overwintering.auto'));

    await waitFor(() => expect(screen.queryByTestId('hardiness-chip-ow-1')).toBeNull());
    expect(screen.getByTestId('hardiness-chip-ow-2')).toBeTruthy();
    expect(screen.queryByTestId('hardiness-chip-ow-3')).toBeNull();
  });

  it('filters by subject type (plant vs. planting run)', async () => {
    useProfiles(allProfiles);
    const user = userEvent.setup();
    renderWithProviders(<OverwinteringListPage />);

    await waitFor(() => expect(screen.getByTestId('hardiness-chip-ow-2')).toBeTruthy());

    await pickOption(user, 'subject_type', i18n.t('pages.overwintering.subjectRun'));

    // Only the run-bound profile (ow-2) remains; plant (ow-1) and unlinked (ow-3) drop.
    await waitFor(() => expect(screen.queryByTestId('hardiness-chip-ow-1')).toBeNull());
    expect(screen.getByTestId('hardiness-chip-ow-2')).toBeTruthy();
    expect(screen.queryByTestId('hardiness-chip-ow-3')).toBeNull();
  });

  it('filters by subject type "unassigned" to surface profiles with neither a plant nor a run', async () => {
    useProfiles(allProfiles);
    const user = userEvent.setup();
    renderWithProviders(<OverwinteringListPage />);

    await waitFor(() => expect(screen.getByTestId('hardiness-chip-ow-1')).toBeTruthy());

    await pickOption(user, 'subject_type', i18n.t('pages.overwintering.subjectNone'));

    // Only the unlinked profile (ow-3) remains; plant (ow-1) and run (ow-2) drop.
    await waitFor(() => expect(screen.queryByTestId('hardiness-chip-ow-1')).toBeNull());
    expect(screen.queryByTestId('hardiness-chip-ow-2')).toBeNull();
    expect(screen.getByTestId('hardiness-chip-ow-3')).toBeTruthy();
  });

  it('combines multiple facets with AND', async () => {
    useProfiles(allProfiles);
    const user = userEvent.setup();
    renderWithProviders(<OverwinteringListPage />);

    await waitFor(() => expect(screen.getByTestId('hardiness-chip-ow-1')).toBeTruthy());

    // origin=manual → {ow-1, ow-3}; subject=plant → {ow-1}; AND → {ow-1}.
    await pickOption(user, 'origin', i18n.t('pages.overwintering.manual'));
    await pickOption(user, 'subject_type', i18n.t('pages.overwintering.subjectPlant'));

    await waitFor(() => expect(screen.queryByTestId('hardiness-chip-ow-3')).toBeNull());
    expect(screen.getByTestId('hardiness-chip-ow-1')).toBeTruthy();
    expect(screen.queryByTestId('hardiness-chip-ow-2')).toBeNull();
  });

  it('stacks a facet with the DataTable free-text search (AND)', async () => {
    useProfiles(allProfiles);
    // Deep-link: origin=manual (ow-1, ow-3) AND search q=Big → only ow-1 ("Big Red").
    renderWithProviders(<PageWithUrlProbe />, {
      route: '/?origin=manual&q=Big',
    });

    await waitFor(() => expect(screen.getByTestId('hardiness-chip-ow-1')).toBeTruthy());
    // ow-3 is manual but its subject is "—" (no "Big"), so the search excludes it.
    expect(screen.queryByTestId('hardiness-chip-ow-3')).toBeNull();
    expect(screen.queryByTestId('hardiness-chip-ow-2')).toBeNull();
  });

  it('shows an honest empty state when facets exclude every row', async () => {
    useProfiles(allProfiles);
    // hardy is only ow-3 (subject none); subject=plant removes it → zero matches.
    renderWithProviders(<OverwinteringListPage />, {
      route: '/?hardiness=hardy&subject_type=plant',
    });

    await waitFor(() =>
      expect(screen.getByTestId('no-column-filter-results')).toBeTruthy(),
    );
    expect(screen.queryByTestId('hardiness-chip-ow-1')).toBeNull();
  });

  it('clears an individual facet by unchecking its option', async () => {
    useProfiles(allProfiles);
    const user = userEvent.setup();
    renderWithProviders(<OverwinteringListPage />, { route: '/?origin=auto' });

    // Rehydrated: only the auto profile (ow-2) is visible.
    await waitFor(() => expect(screen.getByTestId('hardiness-chip-ow-2')).toBeTruthy());
    expect(screen.queryByTestId('hardiness-chip-ow-1')).toBeNull();

    // Unchecking the single selected option restores all rows.
    await pickOption(user, 'origin', i18n.t('pages.overwintering.auto'));

    await waitFor(() => expect(screen.getByTestId('hardiness-chip-ow-1')).toBeTruthy());
    expect(screen.getByTestId('hardiness-chip-ow-3')).toBeTruthy();
  });

  it('clears all facets at once via the clear button', async () => {
    useProfiles(allProfiles);
    const user = userEvent.setup();
    renderWithProviders(<PageWithUrlProbe />, {
      route: '/?hardiness=needs_protection&origin=auto',
    });

    await waitFor(() => expect(screen.getByTestId('hardiness-chip-ow-2')).toBeTruthy());
    expect(screen.queryByTestId('hardiness-chip-ow-1')).toBeNull();

    await user.click(screen.getByTestId('clear-column-filters-button'));

    await waitFor(() => expect(screen.getByTestId('hardiness-chip-ow-1')).toBeTruthy());
    const params = new URLSearchParams(
      screen.getByTestId('url-search').textContent ?? '',
    );
    expect(params.get('hardiness')).toBeNull();
    expect(params.get('origin')).toBeNull();
  });

  it('rehydrates facet state from the URL on initial load', async () => {
    useProfiles(allProfiles);
    renderWithProviders(<OverwinteringListPage />, {
      route: '/?hardiness=needs_protection',
    });

    // Only the needs_protection profile (ow-2) is shown straight from the URL.
    await waitFor(() => expect(screen.getByTestId('hardiness-chip-ow-2')).toBeTruthy());
    expect(screen.queryByTestId('hardiness-chip-ow-1')).toBeNull();
    expect(screen.queryByTestId('hardiness-chip-ow-3')).toBeNull();
  });

  it('serialises an active facet into a URL query param', async () => {
    useProfiles(allProfiles);
    const user = userEvent.setup();
    renderWithProviders(<PageWithUrlProbe />);

    await waitFor(() => expect(screen.getByTestId('hardiness-chip-ow-1')).toBeTruthy());

    await pickOption(user, 'winter_action', 'Mulchen');

    await waitFor(() => {
      const params = new URLSearchParams(
        screen.getByTestId('url-search').textContent ?? '',
      );
      expect(params.get('winter_action')).toBe('mulch');
    });
  });
});
