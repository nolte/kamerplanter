import { screen, waitFor, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import { http, HttpResponse } from 'msw';
import i18n from 'i18next';
import { renderWithProviders } from '../helpers';
import { server } from '../mocks/server';
import type { PhaseSequence } from '@/api/types';

const mockNavigate = vi.fn();
vi.mock('react-router-dom', async (orig) => {
  const actual = await orig<typeof import('react-router-dom')>();
  return { ...actual, useNavigate: () => mockNavigate };
});

import PhaseSequenceListPage from '@/pages/phasen/PhaseSequenceListPage';

const LIST_URL = '/api/v1/phase-sequences';
const DELETE_URL = '/api/v1/phase-sequences/:key';
const CREATE_URL = '/api/v1/phase-sequences';

function makeSequence(overrides: Partial<PhaseSequence> = {}): PhaseSequence {
  return {
    key: 'seq-1',
    name: 'tomato-cycle',
    display_name: 'Tomato Cycle',
    display_name_de: 'Tomaten-Zyklus',
    description: 'Full annual tomato cycle.',
    description_de: 'Voller Jahreszyklus fuer Tomaten.',
    species_key: 'sp-1',
    cycle_type: 'annual',
    is_repeating: false,
    cycle_restart_entry_order: null,
    typical_lifespan_years: null,
    dormancy_required: false,
    vernalization_required: false,
    vernalization_min_days: null,
    photoperiod_type: 'day_neutral',
    critical_day_length_hours: null,
    is_system: false,
    tags: ['indoor'],
    entries: [],
    created_at: '2024-01-01T00:00:00Z',
    updated_at: null,
    ...overrides,
  };
}

function useSequences(rows: PhaseSequence[]) {
  server.use(http.get(LIST_URL, () => HttpResponse.json(rows)));
}

describe('PhaseSequenceListPage', () => {
  beforeEach(() => {
    i18n.changeLanguage('de');
    mockNavigate.mockClear();
  });

  afterEach(() => {
    i18n.changeLanguage('en');
  });

  it('renders the loaded sequence row', async () => {
    useSequences([makeSequence()]);
    renderWithProviders(<PhaseSequenceListPage />);

    expect(await screen.findByText('Tomaten-Zyklus')).toBeInTheDocument();
    expect(screen.getByTestId('create-sequence-button')).toBeInTheDocument();
  });

  it('renders repeating + duration columns and falls back to name (EN locale)', async () => {
    await i18n.changeLanguage('en');
    useSequences([
      makeSequence({
        key: 'seq-2',
        display_name: '',
        display_name_de: '',
        is_repeating: true,
        cycle_type: 'perennial',
        entries: [
          { effective_duration_days: 10 } as PhaseSequence['entries'][number],
          { effective_duration_days: 5 } as PhaseSequence['entries'][number],
        ],
      }),
    ]);
    renderWithProviders(<PhaseSequenceListPage />);

    // display_name empty -> falls back to raw name
    expect(await screen.findByText('tomato-cycle')).toBeInTheDocument();
    // is_repeating chip + total duration column (10 + 5 = 15 days)
    const repeatingLabel = i18n.t('pages.phaseSequences.isRepeating');
    expect(screen.getAllByText(repeatingLabel).length).toBeGreaterThan(0);
    expect(
      screen.getByText(i18n.t('pages.phaseSequences.totalDurationDays', { count: 15 })),
    ).toBeInTheDocument();
  });

  it('filters and sorts through the table toolbar', async () => {
    useSequences([
      makeSequence({ key: 'a', name: 'alpha', display_name_de: 'Alpha', is_repeating: true, entries: [{ effective_duration_days: 3 } as PhaseSequence['entries'][number]] }),
      makeSequence({ key: 'b', name: 'beta', display_name_de: 'Beta', cycle_type: 'perennial', entries: [{ effective_duration_days: 20 } as PhaseSequence['entries'][number]] }),
    ]);
    const user = userEvent.setup();
    renderWithProviders(<PhaseSequenceListPage />);

    await screen.findByText('Alpha');
    const searchBox = within(screen.getByTestId('table-search-input')).getByRole('textbox');
    // Search (exercises the columns' searchValue accessors + filtering).
    await user.type(searchBox, 'beta');
    await waitFor(
      () => expect(screen.queryByText('Alpha')).not.toBeInTheDocument(),
      { timeout: 3000 },
    );
    expect(screen.getByText('Beta')).toBeInTheDocument();

    await user.clear(searchBox);
    await waitFor(() => expect(screen.getByText('Alpha')).toBeInTheDocument(), {
      timeout: 3000,
    });

    // Sort by each sortable column header (exercises the columns' sortFn).
    const esc = (s: string) => s.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
    for (const label of [
      i18n.t('common.name'),
      i18n.t('pages.phaseSequences.cycleType'),
      i18n.t('pages.phaseSequences.totalDuration'),
    ]) {
      const header = screen.getByRole('columnheader', { name: new RegExp(esc(label)) });
      await user.click(within(header).getByRole('button'));
    }
    expect(screen.getByText('Alpha')).toBeInTheDocument();
  });

  it('renders the mobile card view on a narrow viewport', async () => {
    const original = window.matchMedia;
    window.matchMedia = ((query: string) => ({
      matches: true,
      media: query,
      onchange: null,
      addListener: () => {},
      removeListener: () => {},
      addEventListener: () => {},
      removeEventListener: () => {},
      dispatchEvent: () => false,
    })) as unknown as typeof window.matchMedia;
    try {
      useSequences([makeSequence({ is_repeating: true, entries: [{ effective_duration_days: 7 } as PhaseSequence['entries'][number]] })]);
      renderWithProviders(<PhaseSequenceListPage />);

      expect(await screen.findByTestId('data-table-cards')).toBeInTheDocument();
      expect(screen.getByText('Tomaten-Zyklus')).toBeInTheDocument();
    } finally {
      window.matchMedia = original;
    }
  });

  it('navigates to the sequence detail on row click', async () => {
    useSequences([makeSequence()]);
    const user = userEvent.setup();
    renderWithProviders(<PhaseSequenceListPage />);

    await user.click(await screen.findByText('Tomaten-Zyklus'));
    expect(mockNavigate).toHaveBeenCalledWith('/phasen/ablaeufe/seq-1');
  });

  it('creates a new sequence through the create dialog', async () => {
    let created = false;
    useSequences([makeSequence()]);
    server.use(
      http.post(CREATE_URL, async () => {
        created = true;
        return HttpResponse.json(makeSequence({ key: 'seq-new', name: 'new-seq' }));
      }),
    );
    const user = userEvent.setup();
    renderWithProviders(<PhaseSequenceListPage />);

    await user.click(await screen.findByTestId('create-sequence-button'));
    const dialog = await screen.findByRole('dialog');
    await user.type(
      within(dialog).getByLabelText(i18n.t('common.name'), { exact: false }),
      'My Sequence',
    );
    await user.click(within(dialog).getByTestId('form-submit-button'));

    await waitFor(() => expect(created).toBe(true));
    expect(
      await screen.findByText(i18n.t('pages.phaseSequences.sequenceCreated')),
    ).toBeInTheDocument();
  });

  it('surfaces an error when creating a sequence fails', async () => {
    useSequences([makeSequence()]);
    server.use(http.post(CREATE_URL, () => new HttpResponse(null, { status: 500 })));
    const user = userEvent.setup();
    renderWithProviders(<PhaseSequenceListPage />);

    await user.click(await screen.findByTestId('create-sequence-button'));
    const dialog = await screen.findByRole('dialog');
    await user.type(
      within(dialog).getByLabelText(i18n.t('common.name'), { exact: false }),
      'Broken',
    );
    await user.click(within(dialog).getByTestId('form-submit-button'));

    expect(await screen.findByText(i18n.t('errors.server'))).toBeInTheDocument();
  });

  it('deletes a sequence through the confirm dialog', async () => {
    let deletedKey: string | null = null;
    useSequences([makeSequence()]);
    server.use(
      http.delete(DELETE_URL, ({ params }) => {
        deletedKey = params.key as string;
        return new HttpResponse(null, { status: 204 });
      }),
    );
    const user = userEvent.setup();
    renderWithProviders(<PhaseSequenceListPage />);

    await screen.findByText('Tomaten-Zyklus');
    await user.click(screen.getByRole('button', { name: i18n.t('common.delete') }));

    await user.click(await screen.findByTestId('confirm-dialog-confirm'));

    await waitFor(() => expect(deletedKey).toBe('seq-1'));
    await waitFor(() =>
      expect(screen.queryByTestId('confirm-dialog')).not.toBeInTheDocument(),
    );
    expect(
      await screen.findByText(i18n.t('pages.phaseSequences.sequenceDeleted')),
    ).toBeInTheDocument();
  });

  it('shows the pending state on the confirm dialog while the delete is in flight', async () => {
    let resolveDelete: (() => void) | null = null;
    useSequences([makeSequence()]);
    server.use(
      http.delete(
        DELETE_URL,
        () =>
          new Promise<Response>((resolve) => {
            resolveDelete = () => resolve(new HttpResponse(null, { status: 204 }));
          }),
      ),
    );
    const user = userEvent.setup();
    renderWithProviders(<PhaseSequenceListPage />);

    await screen.findByText('Tomaten-Zyklus');
    await user.click(screen.getByRole('button', { name: i18n.t('common.delete') }));
    await user.click(await screen.findByTestId('confirm-dialog-confirm'));

    // Pending: confirm button announces busy + live region carries processing text.
    await waitFor(() =>
      expect(screen.getByTestId('confirm-dialog-confirm')).toHaveAttribute(
        'aria-busy',
        'true',
      ),
    );
    expect(screen.getByTestId('confirm-dialog-live-region')).toHaveTextContent(
      i18n.t('common.processing'),
    );

    resolveDelete!();
    await waitFor(() =>
      expect(screen.queryByTestId('confirm-dialog')).not.toBeInTheDocument(),
    );
  });

  it('surfaces an error when the delete request fails', async () => {
    useSequences([makeSequence()]);
    server.use(
      http.delete(DELETE_URL, () => new HttpResponse(null, { status: 500 })),
    );
    const user = userEvent.setup();
    renderWithProviders(<PhaseSequenceListPage />);

    await screen.findByText('Tomaten-Zyklus');
    await user.click(screen.getByRole('button', { name: i18n.t('common.delete') }));
    await user.click(await screen.findByTestId('confirm-dialog-confirm'));

    expect(await screen.findByText(i18n.t('errors.server'))).toBeInTheDocument();
  });

  it('renders an error state with retry when the list request fails', async () => {
    let calls = 0;
    server.use(
      http.get(LIST_URL, () => {
        calls += 1;
        if (calls === 1) return new HttpResponse(null, { status: 500 });
        return HttpResponse.json([makeSequence()]);
      }),
    );
    const user = userEvent.setup();
    renderWithProviders(<PhaseSequenceListPage />);

    expect((await screen.findAllByText(i18n.t('errors.server'))).length).toBeGreaterThan(0);
    await user.click(screen.getByRole('button', { name: i18n.t('common.retry') }));
    expect(await screen.findByText('Tomaten-Zyklus')).toBeInTheDocument();
  });

  it('opens the create dialog from the empty-state action', async () => {
    useSequences([]);
    const user = userEvent.setup();
    renderWithProviders(<PhaseSequenceListPage />);

    await user.click(
      await screen.findByRole('button', {
        name: i18n.t('pages.phaseSequences.createSequence'),
      }),
    );
    expect(
      await screen.findByRole('heading', {
        name: i18n.t('pages.phaseSequences.createSequence'),
      }),
    ).toBeInTheDocument();
  });

  it('hides the delete action for system-owned sequences', async () => {
    useSequences([makeSequence({ is_system: true })]);
    renderWithProviders(<PhaseSequenceListPage />);

    await screen.findByText('Tomaten-Zyklus');
    expect(
      screen.queryByRole('button', { name: i18n.t('common.delete') }),
    ).not.toBeInTheDocument();
  });
});
