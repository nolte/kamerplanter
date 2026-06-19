import { describe, it, expect, vi, beforeEach } from 'vitest';
import { screen, waitFor, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { renderWithProviders } from '../helpers';
import HaPublishSettingsTab from '@/pages/auth/HaPublishSettingsTab';

vi.mock('@/api/endpoints/plantInstances', () => ({
  listPlantInstances: vi.fn(),
}));
vi.mock('@/api/endpoints/tanks', () => ({
  listTanks: vi.fn(),
}));
vi.mock('@/api/endpoints/sites', () => ({
  listSites: vi.fn(),
  listLocations: vi.fn(),
}));
vi.mock('@/api/endpoints/haPublish', () => ({
  listHaPublishSettings: vi.fn(),
  setHaPublishStatus: vi.fn(),
  bulkSetHaPublishStatus: vi.fn(),
}));

import { listPlantInstances } from '@/api/endpoints/plantInstances';
import { listTanks } from '@/api/endpoints/tanks';
import { listSites, listLocations } from '@/api/endpoints/sites';
import {
  listHaPublishSettings,
  setHaPublishStatus,
  bulkSetHaPublishStatus,
} from '@/api/endpoints/haPublish';
import type { PlantInstance, Tank, Site, Location } from '@/api/types';

const mockListPlants = vi.mocked(listPlantInstances);
const mockListTanks = vi.mocked(listTanks);
const mockListSites = vi.mocked(listSites);
const mockListLocations = vi.mocked(listLocations);
const mockListSettings = vi.mocked(listHaPublishSettings);
const mockSetStatus = vi.mocked(setHaPublishStatus);
const mockBulkSet = vi.mocked(bulkSetHaPublishStatus);

describe('HaPublishSettingsTab', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockListPlants.mockResolvedValue([
      { key: 'plant-1', plant_name: 'Tomate', instance_id: 'T-001' },
      { key: 'plant-2', plant_name: null, instance_id: 'T-002' },
    ] as unknown as PlantInstance[]);
    mockListTanks.mockResolvedValue([{ key: 'tank-1', name: 'Haupttank' }] as unknown as Tank[]);
    mockListSites.mockResolvedValue([{ key: 'site-1', name: 'Garten' }] as unknown as Site[]);
    mockListLocations.mockResolvedValue([{ key: 'loc-1', name: 'Beet A' }] as unknown as Location[]);
  });

  it('renders the plant table reflecting current publish state', async () => {
    mockListSettings.mockResolvedValue([
      { entity_type: 'plant', entity_key: 'plant-1', enabled: true },
    ]);

    renderWithProviders(<HaPublishSettingsTab />);

    expect(await screen.findByText('Tomate')).toBeInTheDocument();
    // Falls back to instance_id when plant_name is null.
    expect(screen.getByText('T-002')).toBeInTheDocument();

    const switches = screen.getAllByRole('switch');
    expect(switches[0]).toBeChecked();
    expect(switches[1]).not.toBeChecked();
    expect(mockListPlants).toHaveBeenCalled();
  });

  it('persists a toggle via the API', async () => {
    mockListSettings.mockResolvedValue([]);
    mockSetStatus.mockResolvedValue({ entity_type: 'plant', entity_key: 'plant-1', enabled: true });

    renderWithProviders(<HaPublishSettingsTab />);

    const row = (await screen.findByText('Tomate')).closest('tr')!;
    const toggle = within(row).getByRole('switch');
    expect(toggle).not.toBeChecked();

    await userEvent.click(toggle);

    await waitFor(() => {
      expect(mockSetStatus).toHaveBeenCalledWith('plant', 'plant-1', true);
    });
    expect(toggle).toBeChecked();
  });

  it('links each entry to its detail page', async () => {
    mockListSettings.mockResolvedValue([]);

    renderWithProviders(<HaPublishSettingsTab />);

    const link = await screen.findByRole('link', { name: 'Tomate' });
    expect(link).toHaveAttribute('href', '/pflanzen/plant-instances/plant-1');
  });

  it('bulk-enables the selected entries', async () => {
    mockListSettings.mockResolvedValue([]);
    mockBulkSet.mockResolvedValue([
      { entity_type: 'plant', entity_key: 'plant-1', enabled: true },
      { entity_type: 'plant', entity_key: 'plant-2', enabled: true },
    ]);

    renderWithProviders(<HaPublishSettingsTab />);
    await screen.findByText('Tomate');

    // Select all visible rows via the header checkbox, then bulk-publish.
    await userEvent.click(screen.getByLabelText('Select all visible entries'));
    await userEvent.click(screen.getByRole('button', { name: 'Publish' }));

    await waitFor(() => {
      expect(mockBulkSet).toHaveBeenCalledWith('plant', [
        { entity_key: 'plant-1', enabled: true },
        { entity_key: 'plant-2', enabled: true },
      ]);
    });

    // All switches reflect the new enabled state.
    for (const sw of screen.getAllByRole('switch')) {
      expect(sw).toBeChecked();
    }
  });

  it('loads tanks when switching to the tank sub-tab', async () => {
    mockListSettings.mockResolvedValue([]);

    renderWithProviders(<HaPublishSettingsTab />);
    await screen.findByText('Tomate');

    await userEvent.click(screen.getByRole('tab', { name: /tank/i }));

    expect(await screen.findByText('Haupttank')).toBeInTheDocument();
    expect(mockListTanks).toHaveBeenCalled();
  });
});
