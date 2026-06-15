import { describe, it, expect, vi, beforeEach } from 'vitest';
import { screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { http, HttpResponse } from 'msw';
import { server } from '@/test/mocks/server';
import { renderWithProviders, createStoreWithExpertise } from '@/test/helpers';
import PlantIdentificationDialog from '@/components/identification/PlantIdentificationDialog';

/**
 * REQ-029 §4.1 / REQ-029-A §10.1 — dialog orchestration tests.
 *
 * The capture panel is mocked to expose a single "pick image" button that calls
 * onImageReady, so these tests focus on status gating, consent, candidate
 * selection, the select flow and error states.
 */

vi.mock('@/components/identification/ImageCapturePanel', () => ({
  default: ({ onImageReady }: { onImageReady: (f: File, url: string) => void }) => (
    <button
      type="button"
      data-testid="mock-pick-image"
      onClick={() =>
        onImageReady(new File([new Uint8Array([1])], 'p.jpg', { type: 'image/jpeg' }), 'blob:x')
      }
    >
      pick
    </button>
  ),
}));

const STATUS_AVAILABLE = {
  available: true,
  primary_adapter: 'plantnet',
  active_adapter: 'plantnet',
  supports_health: false,
  adapters: {
    plantnet: { configured: true, supports_health: false, rate_limit_per_day: 500 },
  },
};

const CONSENT_GRANTED = [
  {
    purpose: 'plant_identification',
    label: 'Plant identification',
    description: '',
    legal_basis: 'consent',
    required: false,
    granted: true,
    granted_at: '2026-06-15T00:00:00Z',
    revoked_at: null,
  },
];

const IDENTIFY_RESULT = {
  request_key: 'ident_1',
  is_plant: true,
  message: null,
  suggestions: [
    {
      rank: 1,
      scientific_name: 'Monstera deliciosa',
      common_names: ['Fensterblatt'],
      family: 'Araceae',
      genus: 'Monstera',
      confidence: 0.93,
      external_id: 'plantnet:1',
      image_url: null,
      gbif_id: 2873150,
      matched_species_key: 'species_monstera',
      species_in_database: true,
      auto_accept: true,
    },
    {
      rank: 2,
      scientific_name: 'Monstera adansonii',
      common_names: ['Monkey Mask'],
      family: 'Araceae',
      genus: 'Monstera',
      confidence: 0.04,
      external_id: 'plantnet:2',
      image_url: null,
      gbif_id: null,
      matched_species_key: null,
      species_in_database: false,
      auto_accept: false,
    },
  ],
};

function mockStatus(payload: Record<string, unknown>) {
  server.use(http.get('/api/v1/recognition/status', () => HttpResponse.json(payload)));
}
function mockConsents(payload: Record<string, unknown>[]) {
  server.use(http.get('/api/v1/privacy/consents', () => HttpResponse.json(payload)));
}

describe('PlantIdentificationDialog', () => {
  beforeEach(() => {
    mockStatus(STATUS_AVAILABLE);
    mockConsents(CONSENT_GRANTED);
  });

  it('shows the unavailable hint when the feature is not configured (503 path)', async () => {
    mockStatus({
      available: false,
      primary_adapter: '',
      active_adapter: null,
      supports_health: false,
      adapters: {},
    });
    renderWithProviders(
      <PlantIdentificationDialog open onClose={vi.fn()} />,
      { store: createStoreWithExpertise('intermediate') },
    );
    expect(await screen.findByTestId('feature-unavailable')).toBeInTheDocument();
    expect(screen.queryByTestId('mock-pick-image')).not.toBeInTheDocument();
  });

  it('blocks capture behind the consent gate until consent is granted', async () => {
    mockConsents([{ ...CONSENT_GRANTED[0], granted: false }]);
    server.use(
      http.post('/api/v1/privacy/consents', () =>
        HttpResponse.json({ ...CONSENT_GRANTED[0] }, { status: 201 }),
      ),
    );
    renderWithProviders(
      <PlantIdentificationDialog open onClose={vi.fn()} />,
      { store: createStoreWithExpertise('intermediate') },
    );
    expect(await screen.findByTestId('identification-consent-gate')).toBeInTheDocument();
    expect(screen.queryByTestId('mock-pick-image')).not.toBeInTheDocument();

    await userEvent.click(screen.getByTestId('consent-accept'));
    // After granting, the capture panel becomes available.
    expect(await screen.findByTestId('mock-pick-image')).toBeInTheDocument();
  });

  it('runs identify → renders candidates → persists explicit selection', async () => {
    server.use(
      http.post('/api/v1/t/:tenant/identification/identify', () =>
        HttpResponse.json(IDENTIFY_RESULT),
      ),
    );
    const selectSpy = vi.fn();
    server.use(
      http.post('/api/v1/t/:tenant/identification/ident_1/select', ({ request }) => {
        const url = new URL(request.url);
        selectSpy(url.searchParams.get('selected_rank'));
        return HttpResponse.json({
          request_key: 'ident_1',
          selected_rank: 1,
          matched_species_key: 'species_monstera',
          scientific_name: 'Monstera deliciosa',
          common_names: ['Fensterblatt'],
          family: 'Araceae',
          genus: 'Monstera',
          gbif_id: 2873150,
          confidence: 0.93,
          species_in_database: true,
        });
      }),
    );

    const onSpeciesResolved = vi.fn();
    renderWithProviders(
      <PlantIdentificationDialog open onClose={vi.fn()} onSpeciesResolved={onSpeciesResolved} />,
      { store: createStoreWithExpertise('intermediate') },
    );

    await userEvent.click(await screen.findByTestId('mock-pick-image'));
    await userEvent.click(await screen.findByTestId('identify-submit'));

    // Both candidates rendered for explicit selection.
    expect(await screen.findByTestId('suggestion-card-1')).toBeInTheDocument();
    expect(screen.getByTestId('suggestion-card-2')).toBeInTheDocument();

    // Confirm button only enabled after picking one.
    const confirm = screen.getByTestId('create-plant-from-selection');
    expect(confirm).toBeDisabled();
    await userEvent.click(screen.getByTestId('suggestion-select-1'));
    expect(confirm).toBeEnabled();

    await userEvent.click(confirm);
    await waitFor(() => expect(selectSpy).toHaveBeenCalledWith('1'));
    await waitFor(() =>
      expect(onSpeciesResolved).toHaveBeenCalledWith({
        speciesKey: 'species_monstera',
        scientificName: 'Monstera deliciosa',
      }),
    );
  });

  it('shows the "no plant detected" message when is_plant is false', async () => {
    server.use(
      http.post('/api/v1/t/:tenant/identification/identify', () =>
        HttpResponse.json({
          request_key: 'ident_2',
          is_plant: false,
          suggestions: [],
          message: 'No plant material detected.',
        }),
      ),
    );
    renderWithProviders(
      <PlantIdentificationDialog open onClose={vi.fn()} />,
      { store: createStoreWithExpertise('intermediate') },
    );
    await userEvent.click(await screen.findByTestId('mock-pick-image'));
    await userEvent.click(await screen.findByTestId('identify-submit'));
    expect(await screen.findByTestId('not-a-plant')).toBeInTheDocument();
  });

  it('surfaces the rate-limit error (429)', async () => {
    server.use(
      http.post('/api/v1/t/:tenant/identification/identify', () =>
        HttpResponse.json(
          {
            error_id: 'e1',
            error_code: 'RATE_LIMIT_EXCEEDED',
            message: 'limit',
            details: [],
            timestamp: '',
            path: '',
            method: 'POST',
          },
          { status: 429 },
        ),
      ),
    );
    renderWithProviders(
      <PlantIdentificationDialog open onClose={vi.fn()} />,
      { store: createStoreWithExpertise('intermediate') },
    );
    await userEvent.click(await screen.findByTestId('mock-pick-image'));
    await userEvent.click(await screen.findByTestId('identify-submit'));
    expect(await screen.findByTestId('identify-error')).toBeInTheDocument();
  });

  it('re-shows the consent gate on a CONSENT_REQUIRED response (403)', async () => {
    server.use(
      http.post('/api/v1/t/:tenant/identification/identify', () =>
        HttpResponse.json(
          {
            error_id: 'e2',
            error_code: 'CONSENT_REQUIRED',
            message: 'consent',
            details: [],
            timestamp: '',
            path: '',
            method: 'POST',
          },
          { status: 403 },
        ),
      ),
    );
    renderWithProviders(
      <PlantIdentificationDialog open onClose={vi.fn()} />,
      { store: createStoreWithExpertise('intermediate') },
    );
    await userEvent.click(await screen.findByTestId('mock-pick-image'));
    await userEvent.click(await screen.findByTestId('identify-submit'));
    expect(await screen.findByTestId('identification-consent-gate')).toBeInTheDocument();
  });

  it('hides the organ selector for beginners (Auto only)', async () => {
    renderWithProviders(
      <PlantIdentificationDialog open onClose={vi.fn()} />,
      { store: createStoreWithExpertise('beginner') },
    );
    await screen.findByTestId('mock-pick-image');
    expect(screen.queryByTestId('organ-chip-leaf')).not.toBeInTheDocument();
  });

  it('shows the organ selector for intermediate users', async () => {
    renderWithProviders(
      <PlantIdentificationDialog open onClose={vi.fn()} />,
      { store: createStoreWithExpertise('intermediate') },
    );
    expect(await screen.findByTestId('organ-chip-leaf')).toBeInTheDocument();
  });
});
