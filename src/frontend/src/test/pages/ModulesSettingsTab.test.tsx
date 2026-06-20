import { describe, it, expect, vi, beforeEach } from 'vitest';
import { screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';

vi.mock('@/api/endpoints/userPreferences', () => ({
  getPreferences: vi.fn(),
  updatePreferences: vi.fn(),
}));

import ModulesSettingsTab from '@/pages/auth/ModulesSettingsTab';
import { updatePreferences } from '@/api/endpoints/userPreferences';
import {
  renderWithProviders,
  createStoreWithExpertise,
  createStoreWithModuleOverrides,
} from '../helpers';
import type { UserPreference } from '@/api/types';

const mockUpdate = vi.mocked(updatePreferences);

describe('ModulesSettingsTab', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockUpdate.mockResolvedValue({
      key: 'pref-1',
      user_key: 'user-1',
      experience_level: 'expert',
      onboarding_completed: true,
      locale: 'de',
      theme: 'light',
      watering_can_liters: 5,
      smart_home_enabled: false,
      module_visibility: {},
    } as UserPreference);
  });

  it('renders the category accordions and the core section', () => {
    renderWithProviders(<ModulesSettingsTab />, {
      store: createStoreWithExpertise('expert'),
    });
    expect(screen.getByTestId('modules-settings-tab')).toBeInTheDocument();
    expect(screen.getByTestId('modules-category-care_planning')).toBeInTheDocument();
    expect(screen.getByTestId('modules-core-section')).toBeInTheDocument();
  });

  it('disables core module switches', () => {
    renderWithProviders(<ModulesSettingsTab />, {
      store: createStoreWithExpertise('expert'),
    });
    const coreCard = screen.getByTestId('module-core-dashboard');
    const coreSwitch = coreCard.querySelector('input[type="checkbox"]');
    expect(coreSwitch).toBeDisabled();
    expect(coreSwitch).toBeChecked();
  });

  it('persists an explicit override when a module switch is toggled off', async () => {
    const user = userEvent.setup();
    mockUpdate.mockResolvedValue({
      key: 'pref-1',
      user_key: 'user-1',
      experience_level: 'expert',
      onboarding_completed: true,
      locale: 'de',
      theme: 'light',
      watering_can_liters: 5,
      smart_home_enabled: false,
      module_visibility: { tanks: 'disabled' },
    } as UserPreference);

    renderWithProviders(<ModulesSettingsTab />, {
      store: createStoreWithExpertise('expert'),
    });

    const tanksSwitch = screen
      .getByTestId('module-switch-tanks')
      .querySelector('input[type="checkbox"]') as HTMLInputElement;
    expect(tanksSwitch).toBeChecked();

    await user.click(tanksSwitch);

    await waitFor(() => {
      expect(mockUpdate).toHaveBeenCalledWith({
        module_visibility: { tanks: 'disabled' },
      });
    });
  });

  it('removes the override when reset is clicked', async () => {
    const user = userEvent.setup();
    renderWithProviders(<ModulesSettingsTab />, {
      store: createStoreWithModuleOverrides('expert', { tanks: 'disabled' }),
    });

    await user.click(screen.getByTestId('module-reset-tanks'));

    await waitFor(() => {
      expect(mockUpdate).toHaveBeenCalledWith({ module_visibility: {} });
    });
  });
});
