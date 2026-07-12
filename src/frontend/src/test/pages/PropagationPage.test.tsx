import { screen, waitFor, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, it, expect, beforeEach, vi } from 'vitest';
import { http, HttpResponse } from 'msw';
import i18n from 'i18next';
import type { UserEvent } from '@testing-library/user-event';
import PropagationPage from '@/pages/propagation/PropagationPage';
import { renderWithProviders } from '../helpers';
import { server } from '../mocks/server';

const T = '/api/v1/t/:tenant';

const EVENT = {
  _key: 'evt1',
  method: 'cutting',
  status: 'completed',
  parent_plant_keys: ['mother-1'],
  child_plant_keys: ['pup-1'],
  species_key: 'solanum_lycopersicum',
  cultivar_key: null,
  protocol_key: null,
  batch_key: null,
  quantity: 10,
  survived_count: 8,
  success_rate: 0.8,
  failure_reasons: [],
  happened_at: '2026-03-01T10:00:00Z',
  notes: null,
};

// Plant instances the name-based picker offers. The display shows plant_name /
// instance_id, but the value stored/submitted is always the internal `key`.
const INSTANCES = [
  {
    key: 'mother-1',
    instance_id: 'M-1',
    species_key: 'sp-1',
    cultivar_key: null,
    site_key: null,
    location_key: null,
    slot_key: null,
    substrate_batch_key: null,
    substrate_key: null,
    plant_name: 'Mutter Rot',
    planted_on: '2024-03-15',
    removed_on: null,
    termination_type: null,
    termination_cause: null,
    current_phase: 'vegetative',
    current_phase_key: null,
    current_phase_started_at: null,
    container_volume_liters: null,
    substrate_type_override: null,
    species: { scientific_name: 'Solanum lycopersicum', common_names: ['Tomate'] },
    cultivar: null,
    mother_key: null,
    created_at: null,
    updated_at: null,
  },
  {
    key: 'pup-1',
    instance_id: 'P-1',
    species_key: 'sp-1',
    cultivar_key: null,
    site_key: null,
    location_key: null,
    slot_key: null,
    substrate_batch_key: null,
    substrate_key: null,
    plant_name: 'Ableger Gruen',
    planted_on: '2024-04-15',
    removed_on: null,
    termination_type: null,
    termination_cause: null,
    current_phase: 'seedling',
    current_phase_key: null,
    current_phase_started_at: null,
    container_volume_liters: null,
    substrate_type_override: null,
    species: { scientific_name: 'Solanum lycopersicum', common_names: ['Tomate'] },
    cultivar: null,
    mother_key: null,
    created_at: null,
    updated_at: null,
  },
];

function mockEvents(events: unknown[]) {
  server.use(http.get(`${T}/propagation/events`, () => HttpResponse.json(events)));
}

function mockInstances(list: unknown[] = INSTANCES) {
  server.use(http.get(`${T}/plant-instances`, () => HttpResponse.json(list)));
}

/** Open an autocomplete picker (via its root testid), type a query and click the option. */
async function pickByName(
  user: UserEvent,
  container: HTMLElement,
  fieldTestId: string,
  query: string,
  optionName: RegExp,
) {
  const input = within(container)
    .getByTestId(fieldTestId)
    .querySelector('input') as HTMLInputElement;
  await user.click(input);
  await user.type(input, query);
  await user.click(await screen.findByRole('option', { name: optionName }));
}

describe('PropagationPage', () => {
  beforeEach(() => {
    i18n.changeLanguage('de');
    mockEvents([]);
    mockInstances();
  });

  it('renders the title, intro and create button', async () => {
    renderWithProviders(<PropagationPage />);
    await waitFor(() =>
      expect(screen.getByTestId('create-event-button')).toBeInTheDocument(),
    );
    expect(screen.getByTestId('page-title')).toHaveTextContent('Vermehrungsmanagement');
    expect(screen.getByText(/Vermehrungsaktionen/)).toBeInTheDocument();
  });

  it('shows the empty state when there are no events', async () => {
    renderWithProviders(<PropagationPage />);
    await waitFor(() =>
      expect(screen.getByText(/Noch keine Vermehrungsevents/)).toBeInTheDocument(),
    );
  });

  it('lists propagation events with method, status and success rate', async () => {
    mockEvents([EVENT]);
    renderWithProviders(<PropagationPage />);
    await waitFor(() => expect(screen.getByText('Steckling')).toBeInTheDocument());
    expect(screen.getByText('Abgeschlossen')).toBeInTheDocument();
    expect(screen.getByText('80 %')).toBeInTheDocument();
    expect(screen.getByText('8 / 10')).toBeInTheDocument();
  });

  it('creates an event, submitting the picked plant KEYS (not the names)', async () => {
    const user = userEvent.setup();
    const created = vi.fn();
    server.use(
      http.post(`${T}/propagation/events`, async ({ request }) => {
        created(await request.json());
        return HttpResponse.json({ ...EVENT, _key: 'new1' }, { status: 201 });
      }),
    );
    renderWithProviders(<PropagationPage />);
    await user.click(await screen.findByTestId('create-event-button'));
    const dialog = await screen.findByRole('dialog');

    // Species: pick "Tomato" — stores sp-1.
    await pickByName(user, dialog, 'form-field-species_key', 'Tomato', /Tomato/);

    // Parent plants (multi-picker): pick by human-readable name → stores mother-1.
    await pickByName(user, dialog, 'form-field-parent_plant_keys', 'Mutter', /Mutter Rot/);
    // Child plants (multi-picker): pick "Ableger Gruen" → stores pup-1.
    await pickByName(user, dialog, 'form-field-child_plant_keys', 'Ableger', /Ableger Gruen/);

    await user.click(within(dialog).getByTestId('form-submit-button'));

    await waitFor(() => expect(created).toHaveBeenCalled());
    // The submitted payload carries the internal KEYS, proving name→key mapping.
    expect(created.mock.calls[0][0]).toMatchObject({
      method: 'cutting',
      species_key: 'sp-1',
      parent_plant_keys: ['mother-1'],
      child_plant_keys: ['pup-1'],
    });
  });

  it('uses graft-specific picker labels when the method is graft', async () => {
    const user = userEvent.setup();
    renderWithProviders(<PropagationPage />);
    await user.click(await screen.findByTestId('create-event-button'));
    const dialog = await screen.findByRole('dialog');

    // Default method is "cutting" → source/result labels.
    expect(within(dialog).getByLabelText('Quell-Pflanzen')).toBeInTheDocument();

    // Switch to graft → rootstock / scion labels.
    await user.click(within(within(dialog).getByTestId('form-field-method')).getByRole('combobox'));
    await user.click(await screen.findByRole('option', { name: 'Veredelung' }));

    expect(within(dialog).getByLabelText('Unterlage(n)')).toBeInTheDocument();
    expect(within(dialog).getByLabelText('Edelreis')).toBeInTheDocument();
  });

  it('supports multi-selecting several parent plants', async () => {
    const user = userEvent.setup();
    const created = vi.fn();
    server.use(
      http.post(`${T}/propagation/events`, async ({ request }) => {
        created(await request.json());
        return HttpResponse.json({ ...EVENT, _key: 'new2' }, { status: 201 });
      }),
    );
    renderWithProviders(<PropagationPage />);
    await user.click(await screen.findByTestId('create-event-button'));
    const dialog = await screen.findByRole('dialog');

    await pickByName(user, dialog, 'form-field-parent_plant_keys', 'Mutter', /Mutter Rot/);
    await pickByName(user, dialog, 'form-field-parent_plant_keys', 'Ableger', /Ableger Gruen/);

    await user.click(within(dialog).getByTestId('form-submit-button'));

    await waitFor(() => expect(created).toHaveBeenCalled());
    expect(created.mock.calls[0][0].parent_plant_keys).toEqual(['mother-1', 'pup-1']);
  });

  it('traces lineage (ancestors + descendants) via the name picker', async () => {
    const user = userEvent.setup();
    server.use(
      http.get(`${T}/plant-instances/:key/lineage`, () =>
        HttpResponse.json({
          plant_key: 'pup-1',
          paths: [['mother-1']],
          ancestors: [{ key: 'mother-1', instance_id: 'M-1', plant_name: 'Mutter 1' }],
        }),
      ),
      http.get(`${T}/plant-instances/:key/descendants`, () =>
        HttpResponse.json({ plant_key: 'pup-1', descendants: [] }),
      ),
    );
    renderWithProviders(<PropagationPage />);
    await user.click(await screen.findByTestId('tab-lineage'));

    await pickByName(user, document.body, 'lineage-plant-key', 'Ableger', /Ableger Gruen/);
    await user.click(screen.getByTestId('trace-button'));

    await waitFor(() =>
      expect(screen.getByTestId('lineage-result')).toBeInTheDocument(),
    );
    expect(screen.getByText('Mutter 1')).toBeInTheDocument();
    expect(screen.getByText(/Keine Nachkommen/)).toBeInTheDocument();
  });

  it('shows a neutral fallback (never a raw key) for unnamed lineage nodes', async () => {
    const user = userEvent.setup();
    server.use(
      http.get(`${T}/plant-instances/:key/lineage`, () =>
        HttpResponse.json({ plant_key: 'mother-1', paths: [], ancestors: [] }),
      ),
      http.get(`${T}/plant-instances/:key/descendants`, () =>
        HttpResponse.json({
          plant_key: 'mother-1',
          // No plant_name AND no instance_id → must fall back to a neutral label,
          // never the raw `_key`.
          descendants: [{ key: 'secret-key-xyz', instance_id: null, plant_name: null }],
        }),
      ),
    );
    renderWithProviders(<PropagationPage />);
    await user.click(await screen.findByTestId('tab-lineage'));
    await pickByName(user, document.body, 'lineage-plant-key', 'Mutter', /Mutter Rot/);
    await user.click(screen.getByTestId('trace-button'));

    await waitFor(() =>
      expect(screen.getByText(/Keine Vorfahren/)).toBeInTheDocument(),
    );
    expect(screen.getByText('Unbenannte Pflanze')).toBeInTheDocument();
    expect(screen.queryByText('secret-key-xyz')).not.toBeInTheDocument();
  });

  it('renders an in-progress event without survival data', async () => {
    mockEvents([
      { ...EVENT, _key: 'evt2', status: 'in_progress', survived_count: null, success_rate: null },
    ]);
    renderWithProviders(<PropagationPage />);
    await waitFor(() =>
      expect(screen.getByText('In Bearbeitung')).toBeInTheDocument(),
    );
    expect(screen.getAllByText('—').length).toBeGreaterThanOrEqual(2);
  });

  it('reports an incompatible graft, resolving species keys to names', async () => {
    const user = userEvent.setup();
    // Species list resolves the graft response's *_species_key to a name.
    server.use(
      http.get('/api/v1/species', () =>
        HttpResponse.json({
          items: [
            { key: 'sp-tom', scientific_name: 'Solanum lycopersicum', common_names: ['Tomato'] },
            { key: 'sp-cuc', scientific_name: 'Cucumis sativus', common_names: ['Cucumber'] },
          ],
          total: 2,
          offset: 0,
          limit: 200,
        }),
      ),
      http.get(`${T}/propagation/graft-compatibility`, () =>
        HttpResponse.json({
          scion_key: 'mother-1',
          rootstock_key: 'pup-1',
          scion_species_key: 'sp-tom',
          rootstock_species_key: 'sp-cuc',
          compatible: false,
          level: 'incompatible',
          same_genus: false,
          same_family: false,
          message: 'Unterschiedliche Familien.',
        }),
      ),
    );
    renderWithProviders(<PropagationPage />);
    await user.click(await screen.findByTestId('tab-lineage'));
    await pickByName(user, document.body, 'graft-scion-key', 'Mutter', /Mutter Rot/);
    await pickByName(user, document.body, 'graft-rootstock-key', 'Ableger', /Ableger Gruen/);
    await user.click(screen.getByTestId('graft-check-button'));

    const result = within(await screen.findByTestId('graft-result'));
    expect(result.getByText('Nicht kompatibel')).toBeInTheDocument();
    expect(result.getByText(/Unterschiedliche Familien/)).toBeInTheDocument();
    // Species names are resolved; the raw keys never appear.
    expect(result.getByText(/Tomato/)).toBeInTheDocument();
    expect(result.getByText(/Cucumber/)).toBeInTheDocument();
    expect(result.queryByText(/sp-tom/)).not.toBeInTheDocument();
    expect(result.queryByText(/sp-cuc/)).not.toBeInTheDocument();
  });

  it('runs a graft-compatibility check using the plant pickers', async () => {
    const user = userEvent.setup();
    server.use(
      http.get(`${T}/propagation/graft-compatibility`, ({ request }) => {
        const url = new URL(request.url);
        // Prove the pickers pass the internal keys to the API.
        expect(url.searchParams.get('scion_key')).toBe('mother-1');
        expect(url.searchParams.get('rootstock_key')).toBe('pup-1');
        return HttpResponse.json({
          scion_key: 'mother-1',
          rootstock_key: 'pup-1',
          scion_species_key: 'sp-1',
          rootstock_species_key: 'sp-1',
          compatible: true,
          level: 'compatible',
          same_genus: true,
          same_family: true,
          message: 'Gleiche Gattung (Solanum).',
        });
      }),
    );
    renderWithProviders(<PropagationPage />);
    await user.click(await screen.findByTestId('tab-lineage'));

    await pickByName(user, document.body, 'graft-scion-key', 'Mutter', /Mutter Rot/);
    await pickByName(user, document.body, 'graft-rootstock-key', 'Ableger', /Ableger Gruen/);
    await user.click(screen.getByTestId('graft-check-button'));

    const result = within(await screen.findByTestId('graft-result'));
    expect(result.getByText('Kompatibel')).toBeInTheDocument();
    expect(result.getByText(/Gleiche Gattung \(Solanum\)/)).toBeInTheDocument();
    expect(result.getByText('Gleiche Gattung')).toBeInTheDocument();
    expect(result.getByText('Gleiche Familie')).toBeInTheDocument();
  });

  it('deep-links directly to the lineage tab via the #lineage anchor', async () => {
    renderWithProviders(<PropagationPage />, { route: '/vermehrung#lineage' });
    // The lineage panel (not the events table) is shown on load.
    await waitFor(() =>
      expect(screen.getByText('Abstammung erkunden')).toBeInTheDocument(),
    );
    expect(screen.getByTestId('tab-lineage')).toHaveAttribute('aria-selected', 'true');
    expect(screen.getByTestId('tab-events')).toHaveAttribute('aria-selected', 'false');
  });

  it('defaults to the events tab with no anchor', async () => {
    renderWithProviders(<PropagationPage />, { route: '/vermehrung' });
    await waitFor(() =>
      expect(screen.getByTestId('tab-events')).toHaveAttribute('aria-selected', 'true'),
    );
    expect(screen.getByTestId('tab-lineage')).toHaveAttribute('aria-selected', 'false');
  });

  it('activates the lineage tab (and its panel) when the tab is clicked', async () => {
    const user = userEvent.setup();
    renderWithProviders(<PropagationPage />, { route: '/vermehrung' });
    // Starts on events.
    expect(screen.getByTestId('tab-events')).toHaveAttribute('aria-selected', 'true');
    await user.click(await screen.findByTestId('tab-lineage'));
    await waitFor(() =>
      expect(screen.getByTestId('tab-lineage')).toHaveAttribute('aria-selected', 'true'),
    );
    // The lineage panel content is rendered — the URL-synced tab switch worked.
    expect(screen.getByText('Abstammung erkunden')).toBeInTheDocument();
  });
});
