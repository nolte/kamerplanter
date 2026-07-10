import { cleanup, screen, waitFor, fireEvent } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import { http, HttpResponse } from 'msw';
import i18n from 'i18next';
import { renderWithProviders } from '../helpers';
import { server } from '../mocks/server';
import type { PhaseDefinition, PhaseSequence } from '@/api/types';

const mockNavigate = vi.fn();
vi.mock('react-router-dom', async (orig) => {
  const actual = await orig<typeof import('react-router-dom')>();
  return { ...actual, useParams: () => ({ key: 'def-1' }), useNavigate: () => mockNavigate };
});

import PhaseDefinitionDetailPage from '@/pages/phasen/PhaseDefinitionDetailPage';

const DEF_URL = '/api/v1/phase-definitions/:key';
const SEQ_URL = '/api/v1/phase-definitions/:key/sequences';

function makeDefinition(overrides: Partial<PhaseDefinition> = {}): PhaseDefinition {
  return {
    key: 'def-1',
    name: 'vegetative',
    display_name: 'Vegetative',
    display_name_de: 'Vegetativ',
    description: 'Vegetative growth phase.',
    description_de: 'Vegetative Wachstumsphase.',
    typical_duration_days: 28,
    stress_tolerance: 'medium',
    watering_interval_days: 3,
    illustration: '',
    tags: ['indoor'],
    is_system: false,
    usage_count: 0,
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
    description: '',
    description_de: '',
    species_key: 'sp-1',
    cycle_type: 'annual',
    is_repeating: true,
    cycle_restart_entry_order: null,
    typical_lifespan_years: null,
    dormancy_required: false,
    vernalization_required: false,
    vernalization_min_days: null,
    photoperiod_type: 'day_neutral',
    critical_day_length_hours: null,
    is_system: false,
    tags: [],
    entries: [],
    created_at: '2024-01-01T00:00:00Z',
    updated_at: null,
    ...overrides,
  };
}

function useDefinition(def: PhaseDefinition, sequences: PhaseSequence[] = []) {
  server.use(
    http.get(DEF_URL, () => HttpResponse.json(def)),
    http.get(SEQ_URL, () => HttpResponse.json(sequences)),
  );
}

describe('PhaseDefinitionDetailPage', () => {
  beforeEach(() => {
    i18n.changeLanguage('de');
    mockNavigate.mockClear();
  });

  afterEach(() => {
    // Unmount before resetting the language: the file's afterEach runs before
    // testing-library's auto-cleanup (LIFO), so an i18n reset here would
    // otherwise re-render every still-mounted useTranslation() consumer
    // outside act(). Unmounting first makes the reset touch nothing.
    cleanup();
    i18n.changeLanguage('en');
  });

  it('renders the loaded definition detail', async () => {
    useDefinition(makeDefinition());
    renderWithProviders(<PhaseDefinitionDetailPage />, {
      route: '/phasen/definitionen/def-1',
    });

    expect(await screen.findByTestId('phase-definition-detail-page')).toBeInTheDocument();
    expect(screen.getByTestId('delete-definition-button')).toBeInTheDocument();
  });

  it('renders the sequences-using-definition table and its properties (EN, no watering, no tags)', async () => {
    await i18n.changeLanguage('en');
    useDefinition(
      makeDefinition({
        watering_interval_days: null,
        tags: [],
        illustration: 'phases/vegetative.svg',
      }),
      [makeSequence()],
    );
    renderWithProviders(<PhaseDefinitionDetailPage />, {
      route: '/phasen/definitionen/def-1',
    });

    expect(await screen.findByTestId('sequence-row-seq-1')).toBeInTheDocument();
    // Sequence display name (EN) rendered as a link
    expect(screen.getByText('Tomato Cycle')).toBeInTheDocument();
    // repeating icon has an accessible label
    expect(
      screen.getAllByLabelText(i18n.t('pages.phaseSequences.isRepeating')).length,
    ).toBeGreaterThan(0);
    // The illustration image hides itself on load error (onError handler).
    const img = screen.getByAltText('Vegetative') as HTMLImageElement;
    fireEvent.error(img);
    expect(img.style.display).toBe('none');
  });

  it('renders even when the used-in sequences request fails', async () => {
    server.use(
      http.get(DEF_URL, () => HttpResponse.json(makeDefinition())),
      http.get(SEQ_URL, () => new HttpResponse(null, { status: 500 })),
    );
    renderWithProviders(<PhaseDefinitionDetailPage />, {
      route: '/phasen/definitionen/def-1',
    });

    expect(await screen.findByTestId('phase-definition-detail-page')).toBeInTheDocument();
    expect(
      screen.getByText(i18n.t('pages.phaseSequences.noSequencesUsingDefinition')),
    ).toBeInTheDocument();
  });

  it('renders placeholder dashes for a sparse definition and a non-repeating sequence', async () => {
    useDefinition(
      makeDefinition({
        display_name: '',
        display_name_de: '',
        description: '',
        description_de: '',
        watering_interval_days: 5,
        tags: [],
        illustration: '',
      }),
      [makeSequence({ is_repeating: false, display_name: '', display_name_de: '' })],
    );
    renderWithProviders(<PhaseDefinitionDetailPage />, {
      route: '/phasen/definitionen/def-1',
    });

    // Title + sequence link fall back to the raw name.
    expect(await screen.findByTestId('phase-definition-detail-page')).toBeInTheDocument();
    expect(screen.getAllByText('vegetative').length).toBeGreaterThan(0);
    // Non-repeating sequence renders a dash in the repeating column.
    expect(screen.getByText('tomato-cycle')).toBeInTheDocument();
    // Empty display-name / description rows render an em dash.
    expect(screen.getAllByText('—').length).toBeGreaterThan(0);
  });

  it('opens and closes the edit dialog', async () => {
    useDefinition(makeDefinition());
    const user = userEvent.setup();
    renderWithProviders(<PhaseDefinitionDetailPage />, {
      route: '/phasen/definitionen/def-1',
    });

    await user.click(await screen.findByTestId('edit-definition-button'));
    expect(await screen.findByRole('dialog')).toBeInTheDocument();
    await user.keyboard('{Escape}');
    await waitFor(() => expect(screen.queryByRole('dialog')).not.toBeInTheDocument());
  });

  it('closes the delete confirmation on cancel without deleting', async () => {
    let deleteCalled = false;
    useDefinition(makeDefinition());
    server.use(
      http.delete(DEF_URL, () => {
        deleteCalled = true;
        return new HttpResponse(null, { status: 204 });
      }),
    );
    const user = userEvent.setup();
    renderWithProviders(<PhaseDefinitionDetailPage />, {
      route: '/phasen/definitionen/def-1',
    });

    await user.click(await screen.findByTestId('delete-definition-button'));
    await user.click(await screen.findByTestId('confirm-dialog-cancel'));

    await waitFor(() =>
      expect(screen.queryByTestId('confirm-dialog')).not.toBeInTheDocument(),
    );
    expect(deleteCalled).toBe(false);
  });

  it('navigates back to the list via the back button', async () => {
    useDefinition(makeDefinition());
    const user = userEvent.setup();
    renderWithProviders(<PhaseDefinitionDetailPage />, {
      route: '/phasen/definitionen/def-1',
    });

    await user.click(await screen.findByTestId('back-button'));
    expect(mockNavigate).toHaveBeenCalledWith('/phasen/definitionen');
  });

  it('deletes the definition and navigates back to the list', async () => {
    let deletedKey: string | null = null;
    useDefinition(makeDefinition());
    server.use(
      http.delete(DEF_URL, ({ params }) => {
        deletedKey = params.key as string;
        return new HttpResponse(null, { status: 204 });
      }),
    );
    const user = userEvent.setup();
    renderWithProviders(<PhaseDefinitionDetailPage />, {
      route: '/phasen/definitionen/def-1',
    });

    await user.click(await screen.findByTestId('delete-definition-button'));
    await user.click(await screen.findByTestId('confirm-dialog-confirm'));

    await waitFor(() => expect(deletedKey).toBe('def-1'));
    await waitFor(() =>
      expect(mockNavigate).toHaveBeenCalledWith('/phasen/definitionen'),
    );
  });

  it('shows the pending state on the confirm dialog while the delete is in flight', async () => {
    let resolveDelete: (() => void) | null = null;
    useDefinition(makeDefinition());
    server.use(
      http.delete(
        DEF_URL,
        () =>
          new Promise<Response>((resolve) => {
            resolveDelete = () => resolve(new HttpResponse(null, { status: 204 }));
          }),
      ),
    );
    const user = userEvent.setup();
    renderWithProviders(<PhaseDefinitionDetailPage />, {
      route: '/phasen/definitionen/def-1',
    });

    await user.click(await screen.findByTestId('delete-definition-button'));
    await user.click(await screen.findByTestId('confirm-dialog-confirm'));

    await waitFor(() =>
      expect(screen.getByTestId('confirm-dialog-confirm')).toHaveAttribute('aria-busy', 'true'),
    );
    expect(screen.getByTestId('confirm-dialog-live-region')).toHaveTextContent(
      i18n.t('common.processing'),
    );

    resolveDelete!();
    await waitFor(() => expect(mockNavigate).toHaveBeenCalledWith('/phasen/definitionen'));
  });

  it('surfaces an error and stays on the page when the delete fails', async () => {
    useDefinition(makeDefinition());
    server.use(http.delete(DEF_URL, () => new HttpResponse(null, { status: 500 })));
    const user = userEvent.setup();
    renderWithProviders(<PhaseDefinitionDetailPage />, {
      route: '/phasen/definitionen/def-1',
    });

    await user.click(await screen.findByTestId('delete-definition-button'));
    await user.click(await screen.findByTestId('confirm-dialog-confirm'));

    expect(await screen.findByText(i18n.t('errors.server'))).toBeInTheDocument();
    expect(mockNavigate).not.toHaveBeenCalledWith('/phasen/definitionen');
  });

  it('disables delete for an in-use definition', async () => {
    useDefinition(makeDefinition({ usage_count: 5 }));
    renderWithProviders(<PhaseDefinitionDetailPage />, {
      route: '/phasen/definitionen/def-1',
    });

    expect(await screen.findByTestId('delete-definition-button')).toBeDisabled();
    expect(screen.getByTestId('edit-definition-button')).not.toBeDisabled();
  });

  it('disables edit and delete for a system definition', async () => {
    useDefinition(makeDefinition({ is_system: true }));
    renderWithProviders(<PhaseDefinitionDetailPage />, {
      route: '/phasen/definitionen/def-1',
    });

    expect(await screen.findByTestId('delete-definition-button')).toBeDisabled();
    expect(screen.getByTestId('edit-definition-button')).toBeDisabled();
  });

  it('renders an error state with retry when the definition cannot be loaded', async () => {
    let calls = 0;
    server.use(
      http.get(DEF_URL, () => {
        calls += 1;
        if (calls === 1) return new HttpResponse(null, { status: 404 });
        return HttpResponse.json(makeDefinition());
      }),
      http.get(SEQ_URL, () => HttpResponse.json([])),
    );
    const user = userEvent.setup();
    renderWithProviders(<PhaseDefinitionDetailPage />, {
      route: '/phasen/definitionen/def-1',
    });

    expect((await screen.findAllByText(i18n.t('errors.notFound'))).length).toBeGreaterThan(0);
    await user.click(screen.getByRole('button', { name: i18n.t('common.retry') }));
    expect(await screen.findByTestId('phase-definition-detail-page')).toBeInTheDocument();
  });
});
