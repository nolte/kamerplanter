import { describe, it, expect, vi, beforeEach } from 'vitest';
import { screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { renderWithProviders, createTestStore, type TestStore } from '../helpers';
import HaPublishToggle from '@/components/ha/HaPublishToggle';

vi.mock('@/api/endpoints/haPublish', () => ({
  getHaPublishStatus: vi.fn(),
  setHaPublishStatus: vi.fn(),
}));

import { getHaPublishStatus, setHaPublishStatus } from '@/api/endpoints/haPublish';

const mockGetStatus = vi.mocked(getHaPublishStatus);
const mockSetStatus = vi.mocked(setHaPublishStatus);

function storeWithSmartHome(enabled: boolean): TestStore {
  return createTestStore({
    userPreferences: {
      preferences: {
        key: 'pref-1',
        user_key: 'user-1',
        experience_level: 'expert',
        onboarding_completed: true,
        locale: 'de',
        theme: 'light',
        watering_can_liters: 5,
        smart_home_enabled: enabled,
      },
      loading: false,
      error: null,
    },
  });
}

describe('HaPublishToggle', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders nothing when smart home is disabled', () => {
    const store = storeWithSmartHome(false);
    renderWithProviders(<HaPublishToggle entityType="plant" entityKey="plant-1" />, { store });
    expect(screen.queryByTestId('ha-publish-toggle')).not.toBeInTheDocument();
    expect(mockGetStatus).not.toHaveBeenCalled();
  });

  it('loads and reflects the current published status', async () => {
    mockGetStatus.mockResolvedValue({ entity_type: 'tank', entity_key: 'tank-1', enabled: true });
    const store = storeWithSmartHome(true);
    renderWithProviders(<HaPublishToggle entityType="tank" entityKey="tank-1" />, { store });

    expect(await screen.findByTestId('ha-publish-toggle')).toBeInTheDocument();
    await waitFor(() => {
      expect(screen.getByRole('switch')).toBeChecked();
    });
    expect(mockGetStatus).toHaveBeenCalledWith('tank', 'tank-1');
  });

  it('persists the new value when toggled on', async () => {
    mockGetStatus.mockResolvedValue({ entity_type: 'location', entity_key: 'loc-1', enabled: false });
    mockSetStatus.mockResolvedValue({ entity_type: 'location', entity_key: 'loc-1', enabled: true });
    const store = storeWithSmartHome(true);
    renderWithProviders(<HaPublishToggle entityType="location" entityKey="loc-1" />, { store });

    const toggle = await screen.findByRole('switch');
    await waitFor(() => expect(toggle).not.toBeChecked());

    await userEvent.click(toggle);

    await waitFor(() => {
      expect(mockSetStatus).toHaveBeenCalledWith('location', 'loc-1', true);
    });
    expect(toggle).toBeChecked();
  });

  it('reverts the toggle when saving fails', async () => {
    mockGetStatus.mockResolvedValue({ entity_type: 'plant', entity_key: 'plant-1', enabled: false });
    mockSetStatus.mockRejectedValue(new Error('boom'));
    const store = storeWithSmartHome(true);
    renderWithProviders(<HaPublishToggle entityType="plant" entityKey="plant-1" />, { store });

    const toggle = await screen.findByRole('switch');
    await waitFor(() => expect(toggle).not.toBeChecked());

    await userEvent.click(toggle);

    await waitFor(() => {
      expect(toggle).not.toBeChecked();
    });
  });
});
