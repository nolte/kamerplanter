import { screen, waitFor, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, it, expect, beforeEach, vi } from 'vitest';
import { useForm } from 'react-hook-form';
import LocationTreeSelect from '@/components/form/LocationTreeSelect';
import type { LocationTreeNode } from '@/api/types';
import { renderWithProviders } from '../helpers';
import * as sitesApi from '@/api/endpoints/sites';

// Isolated module mock — no real HTTP and no handlers.ts dependency.
vi.mock('@/api/endpoints/sites');
const mockGetLocationTree = vi.mocked(sitesApi.getLocationTree);

function node(key: string, name: string, children: LocationTreeNode[] = []): LocationTreeNode {
  return {
    key,
    name,
    location_type_key: 'lt',
    depth: 0,
    parent_location_key: null,
    slot_count: 0,
    active_plant_count: 0,
    tank_name: null,
    children,
  };
}

function TestForm({ siteKey }: { siteKey: string | null }) {
  const { control } = useForm({ defaultValues: { location_key: '' } });
  return <LocationTreeSelect name="location_key" control={control} siteKey={siteKey} />;
}

describe('LocationTreeSelect', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockGetLocationTree.mockResolvedValue([]);
  });

  it('does not fetch and stays disabled without a siteKey', () => {
    renderWithProviders(<TestForm siteKey={null} />);
    expect(mockGetLocationTree).not.toHaveBeenCalled();
  });

  it('loads and flattens the location tree for a site', async () => {
    mockGetLocationTree.mockResolvedValue([
      node('loc-bed', 'Beet', [node('loc-row', 'Reihe 1')]),
    ]);
    renderWithProviders(<TestForm siteKey="site-1" />);
    await waitFor(() => expect(mockGetLocationTree).toHaveBeenCalledWith('site-1'));

    const user = userEvent.setup();
    await user.click(screen.getByRole('combobox'));
    const listbox = screen.getByRole('listbox');
    expect(within(listbox).getByText('Beet')).toBeTruthy();
    expect(within(listbox).getByText('Reihe 1')).toBeTruthy();
  });

  it('selects a flattened location option', async () => {
    mockGetLocationTree.mockResolvedValue([node('loc-bed', 'Beet')]);
    renderWithProviders(<TestForm siteKey="site-1" />);
    await waitFor(() => expect(mockGetLocationTree).toHaveBeenCalled());

    const user = userEvent.setup();
    await user.click(screen.getByRole('combobox'));
    await user.click(within(screen.getByRole('listbox')).getByText('Beet'));
    expect(screen.getByText('Beet')).toBeTruthy();
  });

  it('falls back to an empty option list when the fetch fails', async () => {
    mockGetLocationTree.mockRejectedValue(new Error('network'));
    renderWithProviders(<TestForm siteKey="site-1" />);
    await waitFor(() => expect(mockGetLocationTree).toHaveBeenCalled());

    const user = userEvent.setup();
    await user.click(screen.getByRole('combobox'));
    // Only the empty placeholder "—" option is present.
    expect(within(screen.getByRole('listbox')).getAllByRole('option').length).toBe(1);
  });
});
