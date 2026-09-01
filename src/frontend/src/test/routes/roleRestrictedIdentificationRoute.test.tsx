import { describe, it, expect, beforeEach } from 'vitest';
import { screen } from '@testing-library/react';
import { http, HttpResponse } from 'msw';
import { server } from '@/test/mocks/server';
import { createStoreWithTenantRole, renderWithProviders } from '@/test/helpers';
import RequireRole from '@/auth/RequireRole';
import PlantIdentificationPage from '@/pages/ki-recognition/PlantIdentificationPage';

/**
 * #1261 on the real page, not a probe — the case the issue reports.
 *
 * `POST /identification/identify` has required `grower` since #1260, and nothing
 * in the router consulted the role, so a viewer could open
 * `/pflanzen/identifikation`, work through the whole wizard, and collect a 403 at
 * the end. What must change is the *entry point*; what must not change is the
 * identification history, which `GET /identification/history` deliberately keeps
 * open to every member (#1260: "this one is a read").
 */

const AVAILABLE = {
  available: true,
  primary_adapter: 'plantnet',
  active_adapter: 'plantnet',
  supports_health: false,
  adapters: { plantnet: { configured: true, supports_health: false, rate_limit_per_day: 500 } },
};

const HISTORY = [
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
];

describe('/pflanzen/identifikation under <RequireRole min="grower">', () => {
  beforeEach(() => {
    server.use(http.get('/api/v1/recognition/status', () => HttpResponse.json(AVAILABLE)));
    server.use(
      http.get('/api/v1/t/:tenant/identification/history', () => HttpResponse.json(HISTORY)),
    );
  });

  it('denies a viewer the wizard entry point but keeps the history readable', async () => {
    renderWithProviders(
      <RequireRole min="grower">
        <PlantIdentificationPage />
      </RequireRole>,
      { store: createStoreWithTenantRole('viewer') },
    );

    expect(await screen.findByTestId('identification-history-item')).toBeInTheDocument();
    expect(screen.getByText('Monstera deliciosa')).toBeInTheDocument();
    expect(screen.getByTestId('role-restriction-notice')).toBeInTheDocument();
    expect(screen.queryByTestId('open-identification-dialog')).not.toBeInTheDocument();
  });

  it('leaves the entry point for the same viewer once the guard is removed — negative control', async () => {
    // The falsification, on the same page with the same store and the same
    // assertion target. It is what distinguishes "the guard refuses the viewer"
    // from "this page never shows the button under these fixtures" — the class of
    // vacuous pass this repository has shipped before.
    renderWithProviders(<PlantIdentificationPage />, {
      store: createStoreWithTenantRole('viewer'),
    });

    expect(await screen.findByTestId('open-identification-dialog')).toBeInTheDocument();
    expect(screen.queryByTestId('role-restriction-notice')).not.toBeInTheDocument();
  });

  it('leaves the entry point in place for a grower', async () => {
    renderWithProviders(
      <RequireRole min="grower">
        <PlantIdentificationPage />
      </RequireRole>,
      { store: createStoreWithTenantRole('grower') },
    );

    expect(await screen.findByTestId('open-identification-dialog')).toBeInTheDocument();
    expect(screen.queryByTestId('role-restriction-notice')).not.toBeInTheDocument();
  });

  it('leaves the entry point in place for a lead', async () => {
    renderWithProviders(
      <RequireRole min="grower">
        <PlantIdentificationPage />
      </RequireRole>,
      { store: createStoreWithTenantRole('lead') },
    );

    expect(await screen.findByTestId('open-identification-dialog')).toBeInTheDocument();
    expect(screen.queryByTestId('role-restriction-notice')).not.toBeInTheDocument();
  });
});
