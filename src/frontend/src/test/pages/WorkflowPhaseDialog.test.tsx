import { cleanup, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import { http, HttpResponse } from 'msw';
import i18n from 'i18next';
import { renderWithProviders } from '../helpers';
import { server } from '../mocks/server';
import type { WorkflowPhase, WorkflowPhaseSuggestion } from '@/api/types';
import WorkflowPhaseDialog from '@/pages/aufgaben/WorkflowPhaseDialog';

const SPECIES_URL = '/api/v1/species';
const SUGGESTIONS_URL = '/api/v1/t/test-tenant/tasks/phases/suggestions';
const LIFECYCLE_URL = '/api/v1/species/:key/lifecycle';
const GROWTH_PHASES_URL = '/api/v1/growth-phases';
const CREATE_PHASE_URL = '/api/v1/t/test-tenant/tasks/workflows/:key/phases';
const UPDATE_PHASE_URL = '/api/v1/t/test-tenant/tasks/phases/:key';

function makePhase(overrides: Partial<WorkflowPhase> = {}): WorkflowPhase {
  return {
    key: 'p1',
    workflow_template_key: 'wf-1',
    name: 'Vegetative',
    description: 'A veg phase',
    phase_order: 1,
    duration_days: 14,
    stress_tolerance: 'low',
    trigger_phase: 'vegetative',
    created_at: '2024-01-01T00:00:00Z',
    updated_at: null,
    ...overrides,
  };
}

function makeSuggestion(overrides: Partial<WorkflowPhaseSuggestion> = {}): WorkflowPhaseSuggestion {
  return {
    name: 'Bloom Boost',
    duration_days: 21,
    stress_tolerance: 'medium',
    trigger_phase: 'flowering',
    used_by_species: ['Cannabis sativa'],
    usage_count: 3,
    ...overrides,
  };
}

const speciesResponse = {
  items: [
    { key: 'sp-1', scientific_name: 'Solanum lycopersicum', common_names: ['Tomato'] },
    { key: 'sp-2', scientific_name: 'Ocimum basilicum', common_names: [] },
  ],
  total: 2,
  offset: 0,
  limit: 500,
};

const growthPhases = [
  {
    key: 'gp-2',
    name: 'flowering',
    display_name: 'Flowering',
    description: 'Bloom time',
    lifecycle_key: 'lc-1',
    typical_duration_days: 60,
    sequence_order: 2,
    is_terminal: true,
    allows_harvest: true,
    stress_tolerance: 'low',
    watering_interval_days: null,
    created_at: null,
    updated_at: null,
  },
  {
    key: 'gp-1',
    name: 'vegetative',
    display_name: 'Vegetative',
    description: '',
    lifecycle_key: 'lc-1',
    typical_duration_days: 30,
    sequence_order: 1,
    is_terminal: false,
    allows_harvest: false,
    stress_tolerance: 'medium',
    watering_interval_days: null,
    created_at: null,
    updated_at: null,
  },
  {
    // No display_name and falsy stress_tolerance -> exercises the `||` fallbacks
    // in both the chip label and fillFromGrowthPhase.
    key: 'gp-3',
    name: 'harvest',
    display_name: '',
    description: '',
    lifecycle_key: 'lc-1',
    typical_duration_days: 0,
    sequence_order: 3,
    is_terminal: true,
    allows_harvest: true,
    stress_tolerance: '',
    watering_interval_days: null,
    created_at: null,
    updated_at: null,
  },
];

interface Seed {
  suggestions?: WorkflowPhaseSuggestion[];
  speciesError?: boolean;
  suggestionsError?: boolean;
  growthError?: boolean;
  createStatus?: number;
  updateStatus?: number;
}

function seed(state: Seed = {}) {
  const {
    suggestions = [],
    speciesError = false,
    suggestionsError = false,
    growthError = false,
    createStatus = 201,
    updateStatus = 200,
  } = state;

  server.use(
    http.get(SPECIES_URL, () =>
      speciesError
        ? HttpResponse.json({ error_id: 'e', error_code: 'X', message: 'boom', details: [] }, { status: 500 })
        : HttpResponse.json(speciesResponse),
    ),
    http.get(SUGGESTIONS_URL, () =>
      suggestionsError
        ? HttpResponse.json({ error_id: 'e', error_code: 'X', message: 'boom', details: [] }, { status: 500 })
        : HttpResponse.json(suggestions),
    ),
    http.get(LIFECYCLE_URL, ({ params }) =>
      HttpResponse.json({ key: `lc-${params.key}`, species_key: params.key }),
    ),
    http.get(GROWTH_PHASES_URL, () =>
      growthError
        ? HttpResponse.json({ error_id: 'e', error_code: 'X', message: 'boom', details: [] }, { status: 500 })
        : HttpResponse.json(growthPhases),
    ),
    http.post(CREATE_PHASE_URL, async ({ request }) =>
      createStatus < 400
        ? HttpResponse.json({ ...makePhase(), ...(await request.json() as object) }, { status: createStatus })
        : HttpResponse.json({ error_id: 'e', error_code: 'INTERNAL_ERROR', message: 'boom', details: [] }, { status: createStatus }),
    ),
    http.put(UPDATE_PHASE_URL, async ({ request }) =>
      updateStatus < 400
        ? HttpResponse.json({ ...makePhase(), ...(await request.json() as object) })
        : HttpResponse.json({ error_id: 'e', error_code: 'INTERNAL_ERROR', message: 'boom', details: [] }, { status: updateStatus }),
    ),
  );
}

function renderDialog(props: {
  phase?: WorkflowPhase;
  open?: boolean;
  onClose?: () => void;
  onSaved?: () => void;
} = {}) {
  const onClose = props.onClose ?? vi.fn();
  const onSaved = props.onSaved ?? vi.fn();
  renderWithProviders(
    <WorkflowPhaseDialog
      open={props.open ?? true}
      onClose={onClose}
      workflowKey="wf-1"
      phase={props.phase}
      onSaved={onSaved}
    />,
  );
  return { onClose, onSaved };
}

describe('WorkflowPhaseDialog', () => {
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

  it('creates a phase from manual input', async () => {
    let body: Record<string, unknown> | null = null;
    seed({ suggestions: [] });
    server.use(
      http.post(CREATE_PHASE_URL, async ({ request }) => {
        body = (await request.json()) as Record<string, unknown>;
        return HttpResponse.json(makePhase(), { status: 201 });
      }),
    );
    const user = userEvent.setup();
    const { onSaved } = renderDialog();

    expect(await screen.findByTestId('workflow-phase-dialog')).toBeInTheDocument();
    // Empty suggestions -> the "no suggestions" hint is shown.
    expect(screen.getByText(i18n.t('pages.tasks.noSuggestions'))).toBeInTheDocument();

    await user.type(screen.getByTestId('form-field-name').querySelector('input')!, 'My Phase');
    await user.type(
      screen.getByTestId('form-field-duration_days').querySelector('input')!,
      '10',
    );
    await user.click(screen.getByTestId('form-submit-button'));

    await waitFor(() => expect(onSaved).toHaveBeenCalled());
    expect(body!.name).toBe('My Phase');
    expect(body!.duration_days).toBe(10);
  });

  it('fills the form from an existing-phase suggestion and submits it', async () => {
    let body: Record<string, unknown> | null = null;
    seed({ suggestions: [makeSuggestion(), makeSuggestion({ name: 'No Species', used_by_species: [] })] });
    server.use(
      http.post(CREATE_PHASE_URL, async ({ request }) => {
        body = (await request.json()) as Record<string, unknown>;
        return HttpResponse.json(makePhase(), { status: 201 });
      }),
    );
    const user = userEvent.setup();
    const { onSaved } = renderDialog();

    await screen.findByTestId('workflow-phase-dialog');
    // Suggestion with species chips + one without (undefined secondary branch).
    await user.click(await screen.findByText('Bloom Boost'));
    // Name field is now populated from the suggestion.
    await waitFor(() =>
      expect(screen.getByTestId('form-field-name').querySelector('input')).toHaveValue('Bloom Boost'),
    );

    await user.click(screen.getByTestId('form-submit-button'));
    await waitFor(() => expect(onSaved).toHaveBeenCalled());
    expect(body!.name).toBe('Bloom Boost');
    expect(body!.duration_days).toBe(21);
  });

  it('loads growth phases for a selected species and fills from a chip', async () => {
    let body: Record<string, unknown> | null = null;
    seed({ suggestions: [] });
    server.use(
      http.post(CREATE_PHASE_URL, async ({ request }) => {
        body = (await request.json()) as Record<string, unknown>;
        return HttpResponse.json(makePhase(), { status: 201 });
      }),
    );
    const user = userEvent.setup();
    const { onSaved } = renderDialog();

    await screen.findByTestId('workflow-phase-dialog');
    // Open the species autocomplete and pick a species.
    const speciesInput = screen.getByLabelText(i18n.t('pages.tasks.selectSpecies'), { exact: false });
    await user.click(speciesInput);
    await user.click(await screen.findByRole('option', { name: /Solanum lycopersicum/ }));

    // Growth-phase chips appear (sorted by sequence_order -> Vegetative first).
    const chip = await screen.findByRole('button', { name: 'Vegetative' });
    await user.click(chip);

    await waitFor(() =>
      expect(screen.getByTestId('form-field-name').querySelector('input')).toHaveValue('Vegetative'),
    );
    await user.click(screen.getByTestId('form-submit-button'));
    await waitFor(() => expect(onSaved).toHaveBeenCalled());
    expect(body!.trigger_phase).toBe('vegetative');
  });

  it('edits an existing phase and saves via update', async () => {
    let updated = false;
    let updateKey: string | null = null;
    seed();
    server.use(
      http.put(UPDATE_PHASE_URL, ({ params }) => {
        updated = true;
        updateKey = params.key as string;
        return HttpResponse.json(makePhase());
      }),
    );
    const user = userEvent.setup();
    const { onSaved } = renderDialog({ phase: makePhase() });

    await screen.findByTestId('workflow-phase-dialog');
    // Edit-mode title + prefilled name; no species/suggestion section.
    expect(screen.getByText(i18n.t('pages.tasks.editPhase'))).toBeInTheDocument();
    expect(screen.queryByText(i18n.t('pages.tasks.loadFromSpecies'))).not.toBeInTheDocument();

    const nameInput = screen.getByTestId('form-field-name').querySelector('input')!;
    expect(nameInput).toHaveValue('Vegetative');
    await user.type(nameInput, ' Plus');
    await user.click(screen.getByTestId('form-submit-button'));

    await waitFor(() => expect(updated).toBe(true));
    expect(updateKey).toBe('p1');
    expect(onSaved).toHaveBeenCalled();
  });

  it('fills from a chip without a display_name and falsy stress tolerance', async () => {
    let body: Record<string, unknown> | null = null;
    seed({ suggestions: [] });
    server.use(
      http.post(CREATE_PHASE_URL, async ({ request }) => {
        body = (await request.json()) as Record<string, unknown>;
        return HttpResponse.json(makePhase(), { status: 201 });
      }),
    );
    const user = userEvent.setup();
    const { onSaved } = renderDialog();

    await screen.findByTestId('workflow-phase-dialog');
    const speciesInput = screen.getByLabelText(i18n.t('pages.tasks.selectSpecies'), { exact: false });
    await user.click(speciesInput);
    await user.click(await screen.findByRole('option', { name: /Solanum lycopersicum/ }));

    // gp-3 has no display_name -> chip falls back to its raw name.
    const chip = await screen.findByRole('button', { name: 'harvest' });
    await user.click(chip);
    await waitFor(() =>
      expect(screen.getByTestId('form-field-name').querySelector('input')).toHaveValue('harvest'),
    );
    await user.click(screen.getByTestId('form-submit-button'));
    await waitFor(() => expect(onSaved).toHaveBeenCalled());
    // Falsy stress_tolerance fell back to 'none'.
    expect(body!.stress_tolerance).toBe('none');
  });

  it('edits a phase with empty duration and stress tolerance', async () => {
    let body: Record<string, unknown> | null = null;
    seed();
    server.use(
      http.put(UPDATE_PHASE_URL, async ({ request }) => {
        body = (await request.json()) as Record<string, unknown>;
        return HttpResponse.json(makePhase());
      }),
    );
    const user = userEvent.setup();
    const { onSaved } = renderDialog({
      phase: makePhase({ duration_days: 0, stress_tolerance: '', trigger_phase: null, description: '' }),
    });

    await screen.findByTestId('workflow-phase-dialog');
    // duration_days 0 -> reset to null -> empty field.
    expect(screen.getByTestId('form-field-duration_days').querySelector('input')).toHaveValue(null);
    await user.type(screen.getByTestId('form-field-name').querySelector('input')!, ' X');
    await user.click(screen.getByTestId('form-submit-button'));

    await waitFor(() => expect(onSaved).toHaveBeenCalled());
    // Empty description omitted, trigger_phase normalised to null.
    expect(body!.description).toBeUndefined();
    expect(body!.trigger_phase).toBeNull();
    expect(body!.stress_tolerance).toBe('none');
  });

  it('surfaces an error when the create request fails', async () => {
    seed({ suggestions: [], createStatus: 500 });
    const user = userEvent.setup();
    const { onSaved } = renderDialog();

    await screen.findByTestId('workflow-phase-dialog');
    await user.type(screen.getByTestId('form-field-name').querySelector('input')!, 'Broken');
    await user.click(screen.getByTestId('form-submit-button'));

    expect(await screen.findByText(i18n.t('errors.server'))).toBeInTheDocument();
    expect(onSaved).not.toHaveBeenCalled();
  });

  it('tolerates species and suggestion load failures', async () => {
    seed({ speciesError: true, suggestionsError: true });
    renderDialog();

    await screen.findByTestId('workflow-phase-dialog');
    // Suggestions request failed -> empty list -> hint shown.
    expect(await screen.findByText(i18n.t('pages.tasks.noSuggestions'))).toBeInTheDocument();
  });

  it('tolerates a growth-phase load failure for the selected species', async () => {
    seed({ suggestions: [], growthError: true });
    const user = userEvent.setup();
    renderDialog();

    await screen.findByTestId('workflow-phase-dialog');
    const speciesInput = screen.getByLabelText(i18n.t('pages.tasks.selectSpecies'), { exact: false });
    await user.click(speciesInput);
    await user.click(await screen.findByRole('option', { name: /Solanum lycopersicum/ }));

    // Species-phases label is present but no chips are rendered (load failed).
    expect(
      await screen.findByText(
        i18n.t('pages.tasks.speciesPhases', { name: 'Solanum lycopersicum' }),
      ),
    ).toBeInTheDocument();
    expect(screen.queryByRole('button', { name: 'Vegetative' })).not.toBeInTheDocument();
  });

  it('closes via the cancel action', async () => {
    seed({ suggestions: [] });
    const user = userEvent.setup();
    const { onClose } = renderDialog();

    await screen.findByTestId('workflow-phase-dialog');
    await user.click(screen.getByTestId('form-cancel-button'));
    expect(onClose).toHaveBeenCalled();
  });
});
