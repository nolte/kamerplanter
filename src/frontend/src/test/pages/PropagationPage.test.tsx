import { screen, waitFor, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, it, expect, beforeEach, vi } from 'vitest';
import { http, HttpResponse } from 'msw';
import i18n from 'i18next';
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

function mockEvents(events: unknown[]) {
  server.use(http.get(`${T}/propagation/events`, () => HttpResponse.json(events)));
}

describe('PropagationPage', () => {
  beforeEach(() => {
    i18n.changeLanguage('de');
    mockEvents([]);
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

  it('creates an event through the dialog', async () => {
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

    const speciesInput = within(dialog)
      .getByTestId('form-field-species_key')
      .querySelector('input') as HTMLInputElement;
    await user.type(speciesInput, 'ocimum_basilicum');
    await user.type(
      within(dialog)
        .getByTestId('form-field-parent_plant_keys')
        .querySelector('input') as HTMLInputElement,
      'mother-1, mother-1',
    );
    await user.click(within(dialog).getByTestId('form-submit-button'));

    await waitFor(() => expect(created).toHaveBeenCalled());
    expect(created.mock.calls[0][0]).toMatchObject({
      method: 'cutting',
      species_key: 'ocimum_basilicum',
      parent_plant_keys: ['mother-1'], // de-duplicated
    });
  });

  it('traces lineage (ancestors + descendants) in the lineage tab', async () => {
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

    await user.type(screen.getByTestId('lineage-plant-key'), 'pup-1');
    await user.click(screen.getByTestId('trace-button'));

    await waitFor(() =>
      expect(screen.getByTestId('lineage-result')).toBeInTheDocument(),
    );
    expect(screen.getByText('Mutter 1')).toBeInTheDocument();
    expect(screen.getByText(/Keine Nachkommen/)).toBeInTheDocument();
  });

  it('shows descendants and a root plant with no ancestors', async () => {
    const user = userEvent.setup();
    server.use(
      http.get(`${T}/plant-instances/:key/lineage`, () =>
        HttpResponse.json({ plant_key: 'mother-1', paths: [], ancestors: [] }),
      ),
      http.get(`${T}/plant-instances/:key/descendants`, () =>
        HttpResponse.json({
          plant_key: 'mother-1',
          descendants: [{ key: 'pup-1', instance_id: 'P-1', plant_name: null }],
        }),
      ),
    );
    renderWithProviders(<PropagationPage />);
    await user.click(await screen.findByTestId('tab-lineage'));
    await user.type(screen.getByTestId('lineage-plant-key'), 'mother-1');
    await user.click(screen.getByTestId('trace-button'));

    await waitFor(() =>
      expect(screen.getByText(/Keine Vorfahren/)).toBeInTheDocument(),
    );
    // descendant chip falls back to instance_id when plant_name is null
    expect(screen.getByText('P-1')).toBeInTheDocument();
  });

  it('renders an in-progress event without survival data', async () => {
    mockEvents([
      { ...EVENT, _key: 'evt2', status: 'in_progress', survived_count: null, success_rate: null },
    ]);
    renderWithProviders(<PropagationPage />);
    await waitFor(() =>
      expect(screen.getByText('In Bearbeitung')).toBeInTheDocument(),
    );
    // survived + success columns render an em dash placeholder
    expect(screen.getAllByText('—').length).toBeGreaterThanOrEqual(2);
  });

  it('reports an incompatible graft with a warning', async () => {
    const user = userEvent.setup();
    server.use(
      http.get(`${T}/propagation/graft-compatibility`, () =>
        HttpResponse.json({
          scion_key: 's1',
          rootstock_key: 'r1',
          scion_species_key: 'tomato',
          rootstock_species_key: 'cucumber',
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
    await user.type(screen.getByTestId('graft-scion-key'), 's1');
    await user.type(screen.getByTestId('graft-rootstock-key'), 'r1');
    await user.click(screen.getByTestId('graft-check-button'));

    await waitFor(() =>
      expect(screen.getByTestId('graft-result')).toBeInTheDocument(),
    );
    expect(screen.getByText('Nicht kompatibel')).toBeInTheDocument();
    expect(screen.getByText(/Unterschiedliche Familien/)).toBeInTheDocument();
  });

  it('runs a graft-compatibility check', async () => {
    const user = userEvent.setup();
    server.use(
      http.get(`${T}/propagation/graft-compatibility`, () =>
        HttpResponse.json({
          scion_key: 's1',
          rootstock_key: 'r1',
          scion_species_key: 'tomato',
          rootstock_species_key: 'tomato2',
          compatible: true,
          level: 'compatible',
          same_genus: true,
          same_family: true,
          message: 'Gleiche Gattung (Solanum).',
        }),
      ),
    );
    renderWithProviders(<PropagationPage />);
    await user.click(await screen.findByTestId('tab-lineage'));

    await user.type(screen.getByTestId('graft-scion-key'), 's1');
    await user.type(screen.getByTestId('graft-rootstock-key'), 'r1');
    await user.click(screen.getByTestId('graft-check-button'));

    await waitFor(() =>
      expect(screen.getByTestId('graft-result')).toBeInTheDocument(),
    );
    expect(screen.getByText('Kompatibel')).toBeInTheDocument();
    expect(screen.getByText(/Gleiche Gattung/)).toBeInTheDocument();
  });
});
