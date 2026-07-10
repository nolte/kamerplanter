import { screen, waitFor, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import { http, HttpResponse } from 'msw';
import i18n from 'i18next';
import { renderWithProviders } from '../helpers';
import { server } from '../mocks/server';
import type { PhaseSequence, PhaseSequenceEntry } from '@/api/types';

const mockNavigate = vi.fn();
vi.mock('react-router-dom', async (orig) => {
  const actual = await orig<typeof import('react-router-dom')>();
  return { ...actual, useParams: () => ({ key: 'seq-1' }), useNavigate: () => mockNavigate };
});

import PhaseSequenceDetailPage from '@/pages/phasen/PhaseSequenceDetailPage';

const SEQ_URL = '/api/v1/phase-sequences/:key';
const SPECIES_URL = '/api/v1/phase-sequences/:key/species';
const ENTRY_DELETE_URL = '/api/v1/phase-sequences/:seqKey/entries/:entryKey';
const REORDER_URL = '/api/v1/phase-sequences/:seqKey/entries/reorder';
const UPDATE_URL = '/api/v1/phase-sequences/:key';

function makeEntry(overrides: Partial<PhaseSequenceEntry> = {}): PhaseSequenceEntry {
  return {
    key: 'entry-1',
    phase_sequence_key: 'seq-1',
    phase_definition_key: 'def-1',
    sequence_order: 1,
    override_duration_days: null,
    effective_duration_days: 14,
    is_terminal: false,
    allows_harvest: false,
    is_recurring: false,
    phase_definition: {
      key: 'def-1',
      name: 'vegetative',
      display_name: 'Vegetative',
      display_name_de: 'Vegetativ',
    } as PhaseSequenceEntry['phase_definition'],
    created_at: '2024-01-01T00:00:00Z',
    updated_at: null,
    ...overrides,
  };
}

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
    tags: [],
    entries: [makeEntry()],
    created_at: '2024-01-01T00:00:00Z',
    updated_at: null,
    ...overrides,
  };
}

type LinkedSpecies = { key: string; scientific_name: string; common_names: string[] };

function useSequence(seq: PhaseSequence, species: LinkedSpecies[] = []) {
  server.use(
    http.get(SEQ_URL, () => HttpResponse.json(seq)),
    http.get(SPECIES_URL, () => HttpResponse.json(species)),
  );
}

describe('PhaseSequenceDetailPage', () => {
  beforeEach(() => {
    i18n.changeLanguage('de');
    mockNavigate.mockClear();
  });

  afterEach(() => {
    i18n.changeLanguage('en');
  });

  it('renders the loaded sequence detail with its entry', async () => {
    useSequence(makeSequence());
    renderWithProviders(<PhaseSequenceDetailPage />, {
      route: '/phasen/ablaeufe/seq-1',
    });

    expect(await screen.findByTestId('phase-sequence-detail-page')).toBeInTheDocument();
    expect(screen.getByTestId('entry-row-entry-1')).toBeInTheDocument();
  });

  it('renders repeating chip, terminal/harvest columns, override indicator and recurring chip', async () => {
    useSequence(
      makeSequence({
        is_repeating: true,
        entries: [
          makeEntry({
            key: 'e1',
            sequence_order: 1,
            is_terminal: true,
            allows_harvest: true,
            is_recurring: true,
            override_duration_days: 20,
            effective_duration_days: 20,
          }),
        ],
      }),
    );
    renderWithProviders(<PhaseSequenceDetailPage />, {
      route: '/phasen/ablaeufe/seq-1',
    });

    await screen.findByTestId('entry-row-e1');
    expect(screen.getByLabelText(i18n.t('pages.phaseSequences.isTerminal'))).toBeInTheDocument();
    expect(screen.getByLabelText(i18n.t('pages.phaseSequences.allowsHarvest'))).toBeInTheDocument();
    expect(screen.getByText(i18n.t('pages.phaseSequences.isRecurring'))).toBeInTheDocument();
    expect(
      screen.getByText(`(${i18n.t('pages.phaseSequences.overrideIndicator')})`),
    ).toBeInTheDocument();
  });

  it('renders the empty-entries placeholder', async () => {
    useSequence(makeSequence({ entries: [] }));
    renderWithProviders(<PhaseSequenceDetailPage />, {
      route: '/phasen/ablaeufe/seq-1',
    });

    expect(
      await screen.findByText(i18n.t('pages.phaseSequences.noDefinitions')),
    ).toBeInTheDocument();
  });

  it('shows the linked species card and toggles show-all', async () => {
    const species: LinkedSpecies[] = Array.from({ length: 7 }, (_, i) => ({
      key: `sp-${i}`,
      scientific_name: `Species ${i}`,
      common_names: i % 2 === 0 ? [`Common ${i}`] : [],
    }));
    useSequence(makeSequence(), species);
    const user = userEvent.setup();
    renderWithProviders(<PhaseSequenceDetailPage />, {
      route: '/phasen/ablaeufe/seq-1',
    });

    await screen.findByTestId('phase-sequence-detail-page');
    // Only first 5 shown initially.
    expect(screen.getByText('Species 0 (Common 0)')).toBeInTheDocument();
    expect(screen.queryByText('Species 6 (Common 6)')).not.toBeInTheDocument();

    await user.click(screen.getByRole('button', { name: i18n.t('common.showAll', { count: 7 }) }));
    expect(await screen.findByText('Species 6 (Common 6)')).toBeInTheDocument();

    await user.click(screen.getByRole('button', { name: i18n.t('common.showLess') }));
    await waitFor(() =>
      expect(screen.queryByText('Species 6 (Common 6)')).not.toBeInTheDocument(),
    );
  });

  it('navigates back to the list via the back button', async () => {
    useSequence(makeSequence());
    const user = userEvent.setup();
    renderWithProviders(<PhaseSequenceDetailPage />, {
      route: '/phasen/ablaeufe/seq-1',
    });

    await user.click(await screen.findByTestId('back-button'));
    expect(mockNavigate).toHaveBeenCalledWith('/phasen/ablaeufe');
  });

  it('opens the edit-sequence dialog and saves changes', async () => {
    let updated = false;
    useSequence(makeSequence());
    server.use(
      http.put(UPDATE_URL, () => {
        updated = true;
        return HttpResponse.json(makeSequence({ name: 'renamed' }));
      }),
    );
    const user = userEvent.setup();
    renderWithProviders(<PhaseSequenceDetailPage />, {
      route: '/phasen/ablaeufe/seq-1',
    });

    await user.click(await screen.findByTestId('edit-sequence-button'));
    const dialog = await screen.findByRole('dialog');
    const nameField = within(dialog).getByLabelText(i18n.t('common.name'), { exact: false });
    await user.clear(nameField);
    await user.type(nameField, 'Renamed Cycle');
    await user.click(within(dialog).getByTestId('form-submit-button'));

    await waitFor(() => expect(updated).toBe(true));
    expect(
      await screen.findByText(i18n.t('pages.phaseSequences.sequenceUpdated')),
    ).toBeInTheDocument();
  });

  it('surfaces an error when the sequence update fails', async () => {
    useSequence(makeSequence());
    server.use(http.put(UPDATE_URL, () => new HttpResponse(null, { status: 500 })));
    const user = userEvent.setup();
    renderWithProviders(<PhaseSequenceDetailPage />, {
      route: '/phasen/ablaeufe/seq-1',
    });

    await user.click(await screen.findByTestId('edit-sequence-button'));
    const dialog = await screen.findByRole('dialog');
    const nameField = within(dialog).getByLabelText(i18n.t('common.name'), { exact: false });
    await user.clear(nameField);
    await user.type(nameField, 'Broken');
    await user.click(within(dialog).getByTestId('form-submit-button'));

    expect(await screen.findByText(i18n.t('errors.server'))).toBeInTheDocument();
  });

  it('opens the add-entry dialog', async () => {
    useSequence(makeSequence());
    const user = userEvent.setup();
    renderWithProviders(<PhaseSequenceDetailPage />, {
      route: '/phasen/ablaeufe/seq-1',
    });

    await user.click(await screen.findByTestId('add-entry-button'));
    // Two dialogs may exist in the DOM (entry dialog is always mounted); at least one open.
    expect((await screen.findAllByRole('dialog')).length).toBeGreaterThan(0);
  });

  it('reorders an entry down', async () => {
    let reordered = false;
    const seq = makeSequence({
      entries: [
        makeEntry({ key: 'e1', sequence_order: 1 }),
        makeEntry({ key: 'e2', sequence_order: 2 }),
      ],
    });
    let getCalls = 0;
    server.use(
      http.get(SEQ_URL, () => {
        getCalls += 1;
        return HttpResponse.json(seq);
      }),
      http.get(SPECIES_URL, () => HttpResponse.json([])),
      http.post(REORDER_URL, () => {
        reordered = true;
        return HttpResponse.json(seq.entries);
      }),
    );
    const user = userEvent.setup();
    renderWithProviders(<PhaseSequenceDetailPage />, {
      route: '/phasen/ablaeufe/seq-1',
    });

    await screen.findByTestId('entry-row-e1');
    const moveDownButtons = screen.getAllByRole('button', {
      name: i18n.t('pages.phaseSequences.moveDown'),
    });
    await user.click(moveDownButtons[0]);

    await waitFor(() => expect(reordered).toBe(true));
    await waitFor(() => expect(getCalls).toBeGreaterThan(1));
  });

  it('surfaces an error when reordering fails', async () => {
    const seq = makeSequence({
      entries: [
        makeEntry({ key: 'e1', sequence_order: 1 }),
        makeEntry({ key: 'e2', sequence_order: 2 }),
      ],
    });
    useSequence(seq);
    server.use(http.post(REORDER_URL, () => new HttpResponse(null, { status: 500 })));
    const user = userEvent.setup();
    renderWithProviders(<PhaseSequenceDetailPage />, {
      route: '/phasen/ablaeufe/seq-1',
    });

    await screen.findByTestId('entry-row-e1');
    await user.click(
      screen.getAllByRole('button', { name: i18n.t('pages.phaseSequences.moveDown') })[0],
    );

    expect(await screen.findByText(i18n.t('errors.server'))).toBeInTheDocument();
  });

  it('deletes a sequence entry through the confirm dialog', async () => {
    let deletedEntryKey: string | null = null;
    useSequence(makeSequence());
    server.use(
      http.delete(ENTRY_DELETE_URL, ({ params }) => {
        deletedEntryKey = params.entryKey as string;
        return new HttpResponse(null, { status: 204 });
      }),
    );
    const user = userEvent.setup();
    renderWithProviders(<PhaseSequenceDetailPage />, {
      route: '/phasen/ablaeufe/seq-1',
    });

    await screen.findByTestId('entry-row-entry-1');
    await user.click(
      screen.getByRole('button', { name: i18n.t('pages.phaseSequences.removeEntry') }),
    );
    await user.click(await screen.findByTestId('confirm-dialog-confirm'));

    await waitFor(() => expect(deletedEntryKey).toBe('entry-1'));
    await waitFor(() =>
      expect(screen.queryByTestId('confirm-dialog')).not.toBeInTheDocument(),
    );
  });

  it('shows the pending state while an entry delete is in flight', async () => {
    let resolveDelete: (() => void) | null = null;
    useSequence(makeSequence());
    server.use(
      http.delete(
        ENTRY_DELETE_URL,
        () =>
          new Promise<Response>((resolve) => {
            resolveDelete = () => resolve(new HttpResponse(null, { status: 204 }));
          }),
      ),
    );
    const user = userEvent.setup();
    renderWithProviders(<PhaseSequenceDetailPage />, {
      route: '/phasen/ablaeufe/seq-1',
    });

    await screen.findByTestId('entry-row-entry-1');
    await user.click(
      screen.getByRole('button', { name: i18n.t('pages.phaseSequences.removeEntry') }),
    );
    await user.click(await screen.findByTestId('confirm-dialog-confirm'));

    await waitFor(() =>
      expect(screen.getByTestId('confirm-dialog-confirm')).toHaveAttribute('aria-busy', 'true'),
    );
    expect(screen.getByTestId('confirm-dialog-live-region')).toHaveTextContent(
      i18n.t('common.processing'),
    );

    resolveDelete!();
    await waitFor(() =>
      expect(screen.queryByTestId('confirm-dialog')).not.toBeInTheDocument(),
    );
  });

  it('surfaces an error when deleting a sequence entry fails', async () => {
    useSequence(makeSequence());
    server.use(
      http.delete(ENTRY_DELETE_URL, () => new HttpResponse(null, { status: 500 })),
    );
    const user = userEvent.setup();
    renderWithProviders(<PhaseSequenceDetailPage />, {
      route: '/phasen/ablaeufe/seq-1',
    });

    await screen.findByTestId('entry-row-entry-1');
    await user.click(
      screen.getByRole('button', { name: i18n.t('pages.phaseSequences.removeEntry') }),
    );
    await user.click(await screen.findByTestId('confirm-dialog-confirm'));

    expect(await screen.findByText(i18n.t('errors.server'))).toBeInTheDocument();
  });

  it('hides the edit button and disables entry actions for a system sequence', async () => {
    useSequence(makeSequence({ is_system: true }));
    renderWithProviders(<PhaseSequenceDetailPage />, {
      route: '/phasen/ablaeufe/seq-1',
    });

    await screen.findByTestId('entry-row-entry-1');
    // UI-NFR-018 R-011: edit button hidden entirely for read-only data.
    expect(screen.queryByTestId('edit-sequence-button')).not.toBeInTheDocument();
    expect(screen.getByTestId('add-entry-button')).toBeDisabled();
    expect(
      screen.getByRole('button', { name: i18n.t('pages.phaseSequences.removeEntry') }),
    ).toBeDisabled();
  });

  it('renders even when the linked-species request fails', async () => {
    server.use(
      http.get(SEQ_URL, () => HttpResponse.json(makeSequence())),
      http.get(SPECIES_URL, () => new HttpResponse(null, { status: 500 })),
    );
    renderWithProviders(<PhaseSequenceDetailPage />, {
      route: '/phasen/ablaeufe/seq-1',
    });

    expect(await screen.findByTestId('phase-sequence-detail-page')).toBeInTheDocument();
    expect(screen.getByTestId('entry-row-entry-1')).toBeInTheDocument();
  });

  it('opens the edit-entry dialog from the row action', async () => {
    useSequence(makeSequence());
    const user = userEvent.setup();
    renderWithProviders(<PhaseSequenceDetailPage />, {
      route: '/phasen/ablaeufe/seq-1',
    });

    await screen.findByTestId('entry-row-entry-1');
    await user.click(screen.getByRole('button', { name: i18n.t('common.edit') }));
    expect((await screen.findAllByRole('dialog')).length).toBeGreaterThan(0);
  });

  it('moves an entry up', async () => {
    let reordered = false;
    const seq = makeSequence({
      entries: [
        makeEntry({ key: 'e1', sequence_order: 1 }),
        makeEntry({ key: 'e2', sequence_order: 2 }),
      ],
    });
    server.use(
      http.get(SEQ_URL, () => HttpResponse.json(seq)),
      http.get(SPECIES_URL, () => HttpResponse.json([])),
      http.post(REORDER_URL, () => {
        reordered = true;
        return HttpResponse.json(seq.entries);
      }),
    );
    const user = userEvent.setup();
    renderWithProviders(<PhaseSequenceDetailPage />, {
      route: '/phasen/ablaeufe/seq-1',
    });

    await screen.findByTestId('entry-row-e2');
    const moveUpButtons = screen.getAllByRole('button', {
      name: i18n.t('pages.phaseSequences.moveUp'),
    });
    // First entry's move-up is disabled; use the second entry's.
    await user.click(moveUpButtons[1]);
    await waitFor(() => expect(reordered).toBe(true));
  });

  it('closes the add-entry dialog without saving', async () => {
    useSequence(makeSequence());
    const user = userEvent.setup();
    renderWithProviders(<PhaseSequenceDetailPage />, {
      route: '/phasen/ablaeufe/seq-1',
    });

    await user.click(await screen.findByTestId('add-entry-button'));
    await screen.findAllByRole('dialog');
    await user.keyboard('{Escape}');
    // The always-mounted entry dialog closes; page remains.
    expect(screen.getByTestId('phase-sequence-detail-page')).toBeInTheDocument();
  });

  it('cancels an entry deletion', async () => {
    let deleteCalled = false;
    useSequence(makeSequence());
    server.use(
      http.delete(ENTRY_DELETE_URL, () => {
        deleteCalled = true;
        return new HttpResponse(null, { status: 204 });
      }),
    );
    const user = userEvent.setup();
    renderWithProviders(<PhaseSequenceDetailPage />, {
      route: '/phasen/ablaeufe/seq-1',
    });

    await screen.findByTestId('entry-row-entry-1');
    await user.click(
      screen.getByRole('button', { name: i18n.t('pages.phaseSequences.removeEntry') }),
    );
    await user.click(await screen.findByTestId('confirm-dialog-cancel'));

    await waitFor(() =>
      expect(screen.queryByTestId('confirm-dialog')).not.toBeInTheDocument(),
    );
    expect(deleteCalled).toBe(false);
  });

  it('navigates back from the error state', async () => {
    server.use(
      http.get(SEQ_URL, () => new HttpResponse(null, { status: 404 })),
      http.get(SPECIES_URL, () => HttpResponse.json([])),
    );
    const user = userEvent.setup();
    renderWithProviders(<PhaseSequenceDetailPage />, {
      route: '/phasen/ablaeufe/seq-1',
    });

    await user.click(await screen.findByTestId('back-button'));
    expect(mockNavigate).toHaveBeenCalledWith('/phasen/ablaeufe');
  });

  it('renders an error state with retry when the sequence cannot be loaded', async () => {
    let calls = 0;
    server.use(
      http.get(SEQ_URL, () => {
        calls += 1;
        if (calls === 1) return new HttpResponse(null, { status: 404 });
        return HttpResponse.json(makeSequence());
      }),
      http.get(SPECIES_URL, () => HttpResponse.json([])),
    );
    const user = userEvent.setup();
    renderWithProviders(<PhaseSequenceDetailPage />, {
      route: '/phasen/ablaeufe/seq-1',
    });

    expect((await screen.findAllByText(i18n.t('errors.notFound'))).length).toBeGreaterThan(0);
    await user.click(screen.getByRole('button', { name: i18n.t('common.retry') }));
    expect(await screen.findByTestId('phase-sequence-detail-page')).toBeInTheDocument();
  });
});
