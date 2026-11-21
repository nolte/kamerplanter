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
    const { container } = renderWithProviders(<TestForm siteKey="site-1" />);
    await waitFor(() => expect(mockGetLocationTree).toHaveBeenCalled());

    const user = userEvent.setup();
    await user.click(screen.getByRole('combobox'));
    await user.click(within(screen.getByRole('listbox')).getByText('Beet'));

    // #1564 — asserted on the two places that carry the *selection*, never with
    // a global text match. The previous `expect(screen.getByText('Beet'))` was
    // wrong in both directions: it was already satisfiable before the click
    // (the option renders that text), so it stated nothing about selecting; and
    // while MUI's close transition is still running the menu is still mounted,
    // so the same text exists twice and the query throws `Found multiple
    // elements with the text: Beet` — which is how it failed under full-suite
    // contention while passing alone. Neither the combobox display nor the
    // hidden form input can ever hold a second copy, so these two assertions
    // are non-vacuous and independent of how fast the transition runs.
    expect(screen.getByRole('combobox')).toHaveTextContent('Beet');
    expect(container.querySelector('input[name="location_key"]')).toHaveValue('loc-bed');
  });

  it('shows a failed fetch with a retry, not as a site without areas (#3037)', async () => {
    mockGetLocationTree
      .mockRejectedValueOnce(new Error('network'))
      .mockResolvedValue([node('loc-bed', 'Beet')]);
    const onTreeLoaded = vi.fn();
    const user = userEvent.setup();
    function Form() {
      const { control } = useForm({ defaultValues: { location_key: '' } });
      return (
        <LocationTreeSelect
          name="location_key"
          control={control}
          siteKey="site-1"
          emptyHelperText="Dieser Standort hat noch keine Bereiche"
          onTreeLoaded={onTreeLoaded}
        />
      );
    }
    renderWithProviders(<Form />);

    await user.click(await screen.findByTestId('form-field-location_key-load-error-retry'));
    // The failure was no count of areas, and its empty hint never showed.
    expect(onTreeLoaded).not.toHaveBeenCalledWith(0);
    await waitFor(() => expect(onTreeLoaded).toHaveBeenCalledWith(1));
    expect(screen.queryByText('Dieser Standort hat noch keine Bereiche')).toBeNull();
    expect(screen.queryByTestId('form-field-location_key-load-error')).toBeNull();

    await user.click(screen.getByRole('combobox'));
    expect(within(screen.getByRole('listbox')).getByText('Beet')).toBeTruthy();
  });
});
