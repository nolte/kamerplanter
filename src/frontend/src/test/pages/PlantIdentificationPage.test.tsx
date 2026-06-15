import { describe, it, expect, vi, beforeEach } from 'vitest';
import { screen } from '@testing-library/react';
import { http, HttpResponse } from 'msw';
import { server } from '@/test/mocks/server';
import { renderWithProviders, createStoreWithExpertise } from '@/test/helpers';
import PlantIdentificationPage from '@/pages/ki-recognition/PlantIdentificationPage';

// The dialog is exercised separately; stub it to a marker here.
vi.mock('@/components/identification/PlantIdentificationDialog', () => ({
  default: ({ open }: { open: boolean }) =>
    open ? <div data-testid="mock-dialog-open" /> : null,
}));
vi.mock('@/pages/pflanzen/PlantInstanceCreateDialog', () => ({
  default: () => null,
}));

const AVAILABLE = {
  available: true,
  primary_adapter: 'plantnet',
  active_adapter: 'plantnet',
  supports_health: false,
  adapters: { plantnet: { configured: true, supports_health: false, rate_limit_per_day: 500 } },
};

const UNAVAILABLE = {
  available: false,
  primary_adapter: '',
  active_adapter: null,
  supports_health: false,
  adapters: {},
};

describe('PlantIdentificationPage', () => {
  beforeEach(() => {
    server.use(http.get('/api/v1/recognition/status', () => HttpResponse.json(AVAILABLE)));
    server.use(
      http.get('/api/v1/t/:tenant/identification/history', () => HttpResponse.json([])),
    );
  });

  it('shows the unavailable hint and hides the start button when not configured', async () => {
    server.use(http.get('/api/v1/recognition/status', () => HttpResponse.json(UNAVAILABLE)));
    renderWithProviders(<PlantIdentificationPage />, {
      store: createStoreWithExpertise('beginner'),
    });
    expect(await screen.findByTestId('page-feature-unavailable')).toBeInTheDocument();
    expect(screen.queryByTestId('open-identification-dialog')).not.toBeInTheDocument();
  });

  it('shows the start button and an empty history when available', async () => {
    renderWithProviders(<PlantIdentificationPage />, {
      store: createStoreWithExpertise('beginner'),
    });
    expect(await screen.findByTestId('open-identification-dialog')).toBeInTheDocument();
    expect(await screen.findByTestId('empty-state')).toBeInTheDocument();
  });

  it('renders identification history entries', async () => {
    server.use(
      http.get('/api/v1/t/:tenant/identification/history', () =>
        HttpResponse.json([
          {
            key: 'ident_1',
            adapter_key: 'plantnet',
            request_type: 'identification',
            image_organ: 'auto',
            status: 'completed',
            selected_result_rank: 1,
            created_at: '2026-06-15T10:00:00Z',
            results: [
              {
                rank: 1,
                scientific_name: 'Monstera deliciosa',
                common_names: [],
                family: null,
                genus: null,
                confidence: 0.9,
                external_id: 'plantnet:1',
                image_url: null,
                gbif_id: null,
                matched_species_key: 'species_monstera',
                species_in_database: true,
                auto_accept: true,
              },
            ],
          },
        ]),
      ),
    );
    renderWithProviders(<PlantIdentificationPage />, {
      store: createStoreWithExpertise('beginner'),
    });
    expect(await screen.findByText('Monstera deliciosa')).toBeInTheDocument();
    expect(screen.getByTestId('identification-history-item')).toBeInTheDocument();
  });
});
