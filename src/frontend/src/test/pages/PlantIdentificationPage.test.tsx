import { describe, it, expect, vi, beforeEach } from 'vitest';
import { screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { http, HttpResponse } from 'msw';
import { server } from '@/test/mocks/server';
import { renderWithProviders, createStoreWithExpertise } from '@/test/helpers';
import PlantIdentificationPage from '@/pages/ki-recognition/PlantIdentificationPage';
import type { IdentifiedSpecies } from '@/components/identification/PlantIdentificationDialog';
import * as identificationApi from '@/api/endpoints/identification';

const navigateSpy = vi.fn();
vi.mock('react-router-dom', async (importOriginal) => {
  const actual = await importOriginal<typeof import('react-router-dom')>();
  return { ...actual, useNavigate: () => navigateSpy };
});

// The dialog is exercised separately; stub it so we can drive the resolve and
// manual-search callbacks the page wires up.
const dialogProps = vi.hoisted(() => ({
  current: null as {
    onSpeciesResolved?: (s: IdentifiedSpecies) => void;
    onManualSearch?: () => void;
  } | null,
}));
vi.mock('@/components/identification/PlantIdentificationDialog', () => ({
  default: ({
    open,
    onSpeciesResolved,
    onManualSearch,
  }: {
    open: boolean;
    onSpeciesResolved?: (s: IdentifiedSpecies) => void;
    onManualSearch?: () => void;
  }) => {
    dialogProps.current = { onSpeciesResolved, onManualSearch };
    return open ? <div data-testid="mock-dialog-open" /> : null;
  },
}));
const createDialogProps = vi.hoisted(() => ({
  current: null as {
    open: boolean;
    onCreated?: (key: string) => void;
    identificationPhoto?: File;
    allowReferenceContribution?: boolean;
  } | null,
}));
vi.mock('@/pages/pflanzen/PlantInstanceCreateDialog', () => ({
  default: ({
    open,
    onCreated,
    identificationPhoto,
    allowReferenceContribution,
  }: {
    open: boolean;
    onCreated?: (key: string) => void;
    identificationPhoto?: File;
    allowReferenceContribution?: boolean;
  }) => {
    createDialogProps.current = { open, onCreated, identificationPhoto, allowReferenceContribution };
    return open ? <div data-testid="mock-create-dialog-open" /> : null;
  },
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

function historyEntry(overrides: Record<string, unknown> = {}) {
  return {
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
    ...overrides,
  };
}

describe('PlantIdentificationPage', () => {
  beforeEach(() => {
    // Restore any vi.spyOn (e.g. linkPlantInstance) so call history never leaks
    // between tests. navigateSpy is a vi.fn (not a spy) and is cleared below.
    vi.restoreAllMocks();
    navigateSpy.mockClear();
    dialogProps.current = null;
    createDialogProps.current = null;
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

  it('shows the top result (no chip) when nothing was explicitly selected', async () => {
    server.use(
      http.get('/api/v1/t/:tenant/identification/history', () =>
        HttpResponse.json([historyEntry({ selected_result_rank: null })]),
      ),
    );
    renderWithProviders(<PlantIdentificationPage />, {
      store: createStoreWithExpertise('beginner'),
    });
    expect(await screen.findByText('Monstera deliciosa')).toBeInTheDocument();
    // No "selected" success chip when nothing was picked.
    expect(screen.queryByText('Selected')).not.toBeInTheDocument();
  });

  it('renders a "no result" caption for a failed identification with no candidates', async () => {
    server.use(
      http.get('/api/v1/t/:tenant/identification/history', () =>
        HttpResponse.json([
          historyEntry({ selected_result_rank: null, results: [], status: 'failed' }),
        ]),
      ),
    );
    renderWithProviders(<PlantIdentificationPage />, {
      store: createStoreWithExpertise('beginner'),
    });
    expect(await screen.findByTestId('identification-history-item')).toBeInTheDocument();
    expect(screen.getByText('No result')).toBeInTheDocument();
  });

  it('opens the identification dialog from the start button', async () => {
    renderWithProviders(<PlantIdentificationPage />, {
      store: createStoreWithExpertise('intermediate'),
    });
    await userEvent.click(await screen.findByTestId('open-identification-dialog'));
    expect(await screen.findByTestId('mock-dialog-open')).toBeInTheDocument();
  });

  it('hands a resolved species to the create-plant dialog', async () => {
    renderWithProviders(<PlantIdentificationPage />, {
      store: createStoreWithExpertise('intermediate'),
    });
    await screen.findByTestId('open-identification-dialog');
    await waitFor(() => expect(dialogProps.current?.onSpeciesResolved).toBeDefined());
    dialogProps.current!.onSpeciesResolved!({
      speciesKey: 'species_monstera',
      scientificName: 'Monstera deliciosa',
    });
    expect(await screen.findByTestId('mock-create-dialog-open')).toBeInTheDocument();
  });

  it('navigates to manual species search from the dialog callback', async () => {
    renderWithProviders(<PlantIdentificationPage />, {
      store: createStoreWithExpertise('intermediate'),
    });
    await screen.findByTestId('open-identification-dialog');
    await waitFor(() => expect(dialogProps.current?.onManualSearch).toBeDefined());
    dialogProps.current!.onManualSearch!();
    expect(navigateSpy).toHaveBeenCalledWith('/stammdaten/species');
  });

  it('threads the identification photo through to the create dialog', async () => {
    renderWithProviders(<PlantIdentificationPage />, {
      store: createStoreWithExpertise('intermediate'),
    });
    await screen.findByTestId('open-identification-dialog');
    await waitFor(() => expect(dialogProps.current?.onSpeciesResolved).toBeDefined());
    const photo = new File([new Uint8Array([1])], 'capture.jpg', { type: 'image/jpeg' });
    dialogProps.current!.onSpeciesResolved!({
      speciesKey: 'species_monstera',
      scientificName: 'Monstera deliciosa',
      photo,
    });
    await waitFor(() => expect(createDialogProps.current?.open).toBe(true));
    expect(createDialogProps.current?.identificationPhoto).toBe(photo);
    // Pl@ntNet is the active adapter here → no DINOv2 reference toggle.
    expect(createDialogProps.current?.allowReferenceContribution).toBe(false);
  });

  it('enables the reference contribution when the DINOv2 adapter is active', async () => {
    server.use(
      http.get('/api/v1/recognition/status', () =>
        HttpResponse.json({ ...AVAILABLE, active_adapter: 'local_embedding' }),
      ),
    );
    renderWithProviders(<PlantIdentificationPage />, {
      store: createStoreWithExpertise('intermediate'),
    });
    await screen.findByTestId('open-identification-dialog');
    await waitFor(() => expect(dialogProps.current?.onSpeciesResolved).toBeDefined());
    dialogProps.current!.onSpeciesResolved!({
      speciesKey: 'species_monstera',
      scientificName: 'Monstera deliciosa',
      photo: new File([new Uint8Array([1])], 'capture.jpg', { type: 'image/jpeg' }),
    });
    await waitFor(() => expect(createDialogProps.current?.open).toBe(true));
    expect(createDialogProps.current?.allowReferenceContribution).toBe(true);
  });

  it('navigates to the new plant after creation and refreshes history', async () => {
    renderWithProviders(<PlantIdentificationPage />, {
      store: createStoreWithExpertise('intermediate'),
    });
    await screen.findByTestId('open-identification-dialog');
    await waitFor(() => expect(dialogProps.current?.onSpeciesResolved).toBeDefined());
    dialogProps.current!.onSpeciesResolved!({
      speciesKey: 'species_monstera',
      scientificName: 'Monstera deliciosa',
    });
    await waitFor(() => expect(createDialogProps.current?.open).toBe(true));
    createDialogProps.current!.onCreated!('plant_42');
    expect(navigateSpy).toHaveBeenCalledWith('/pflanzen/plant-instances/plant_42');
  });

  // ── issue #630 — persist + surface the link to the created instance ──────

  it('links the created instance to the identification request, then navigates', async () => {
    const linkSpy = vi
      .spyOn(identificationApi, 'linkPlantInstance')
      .mockResolvedValue({ request_key: 'ident_7', plant_instance_key: 'plant_42' });
    renderWithProviders(<PlantIdentificationPage />, {
      store: createStoreWithExpertise('intermediate'),
    });
    await screen.findByTestId('open-identification-dialog');
    await waitFor(() => expect(dialogProps.current?.onSpeciesResolved).toBeDefined());
    dialogProps.current!.onSpeciesResolved!({
      speciesKey: 'species_monstera',
      scientificName: 'Monstera deliciosa',
      requestKey: 'ident_7',
    });
    await waitFor(() => expect(createDialogProps.current?.open).toBe(true));
    await createDialogProps.current!.onCreated!('plant_42');
    await waitFor(() => expect(linkSpy).toHaveBeenCalledWith('ident_7', 'plant_42'));
    expect(navigateSpy).toHaveBeenCalledWith('/pflanzen/plant-instances/plant_42');
  });

  it('still navigates when there is no request key to link', async () => {
    const linkSpy = vi.spyOn(identificationApi, 'linkPlantInstance');
    renderWithProviders(<PlantIdentificationPage />, {
      store: createStoreWithExpertise('intermediate'),
    });
    await screen.findByTestId('open-identification-dialog');
    await waitFor(() => expect(dialogProps.current?.onSpeciesResolved).toBeDefined());
    dialogProps.current!.onSpeciesResolved!({
      speciesKey: 'species_monstera',
      scientificName: 'Monstera deliciosa',
    });
    await waitFor(() => expect(createDialogProps.current?.open).toBe(true));
    await createDialogProps.current!.onCreated!('plant_42');
    expect(linkSpy).not.toHaveBeenCalled();
    expect(navigateSpy).toHaveBeenCalledWith('/pflanzen/plant-instances/plant_42');
  });

  it('renders a link chip to the created instance and navigates on click', async () => {
    server.use(
      http.get('/api/v1/t/:tenant/identification/history', () =>
        HttpResponse.json([historyEntry({ plant_instance_key: 'plant_42' })]),
      ),
    );
    renderWithProviders(<PlantIdentificationPage />, {
      store: createStoreWithExpertise('beginner'),
    });
    const chip = await screen.findByTestId('identification-history-instance-link');
    expect(screen.getByTestId('identification-history-instance-created')).toBeInTheDocument();
    await userEvent.click(chip);
    expect(navigateSpy).toHaveBeenCalledWith('/pflanzen/plant-instances/plant_42');
  });
});
