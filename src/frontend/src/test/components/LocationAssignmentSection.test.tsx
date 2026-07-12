import { useEffect, useState } from 'react';
import { screen, waitFor, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, it, expect, beforeEach, vi } from 'vitest';
import { useForm, useWatch } from 'react-hook-form';
import i18n from 'i18next';
import LocationAssignmentSection from '@/components/form/LocationAssignmentSection';
import type { LocationTreeNode, Site, Slot } from '@/api/types';
import { renderWithProviders } from '../helpers';
import * as sitesApi from '@/api/endpoints/sites';

// Isolated module mock — the area tree is fetched by the embedded
// LocationTreeSelect; slots are supplied by the parent (mimicked in the harness).
vi.mock('@/api/endpoints/sites');
const mockGetLocationTree = vi.mocked(sitesApi.getLocationTree);

const MOCK_SITES: Site[] = [
  {
    key: 'site-1',
    name: 'Main Greenhouse',
    type: 'greenhouse',
    gps_coordinates: null,
    climate_zone: '8b',
    total_area_m2: 50,
    created_at: '2024-01-01T00:00:00Z',
    updated_at: null,
  } as unknown as Site,
];

function treeNode(key: string, name: string): LocationTreeNode {
  return {
    key,
    name,
    location_type_key: 'lt',
    depth: 0,
    parent_location_key: null,
    slot_count: 0,
    active_plant_count: 0,
    tank_name: null,
    children: [],
  };
}

function slot(key: string, slotId: string, occupied = false): Slot {
  return {
    key,
    slot_id: slotId,
    location_key: 'loc-1',
    position: [0, 0],
    capacity_plants: 1,
    currently_occupied: occupied,
    last_sanitization: null,
    created_at: null,
    updated_at: null,
  };
}

type FormValues = {
  site_key: string | null;
  location_key: string | null;
  slot_key: string | null;
};

// Stable empty reference — a fresh `[]` default would change identity every
// render and spin the harness's slot-loading effect into an infinite loop.
const EMPTY_SLOTS: Slot[] = [];

interface HarnessProps {
  variant?: 'card' | 'inline';
  onSubmit?: (values: FormValues) => void;
  slotsForArea?: Slot[];
  defaults?: Partial<FormValues>;
}

/**
 * Faithful stand-in for both call sites: it owns the slot list and reloads it
 * when the area changes — exactly what PlantInstanceCreateDialog and
 * PlantInstanceDetailPage do around the shared section.
 */
function Harness({ variant = 'card', onSubmit, slotsForArea = EMPTY_SLOTS, defaults }: HarnessProps) {
  const { control, handleSubmit } = useForm<FormValues>({
    defaultValues: {
      site_key: null,
      location_key: null,
      slot_key: null,
      ...defaults,
    },
  });
  const [slots, setSlots] = useState<Slot[]>(defaults?.location_key ? slotsForArea : []);
  const locationKey = useWatch({ control, name: 'location_key' });

  useEffect(() => {
    setSlots(locationKey ? slotsForArea : []);
  }, [locationKey, slotsForArea]);

  return (
    <form onSubmit={handleSubmit((v) => onSubmit?.(v))}>
      <LocationAssignmentSection control={control} sites={MOCK_SITES} slots={slots} variant={variant} />
      <button type="submit">save</button>
    </form>
  );
}

async function selectSite(user: ReturnType<typeof userEvent.setup>) {
  const siteField = within(screen.getByTestId('form-field-site_key')).getByRole('combobox');
  await user.click(siteField);
  await user.click(await screen.findByRole('option', { name: 'Main Greenhouse' }));
}

async function selectArea(user: ReturnType<typeof userEvent.setup>, name: string) {
  const areaField = within(screen.getByTestId('form-field-location_key')).getByRole('combobox');
  await waitFor(() => expect(areaField).not.toHaveAttribute('aria-disabled', 'true'));
  await user.click(areaField);
  await user.click(within(screen.getByRole('listbox')).getByText(name));
}

describe('LocationAssignmentSection', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockGetLocationTree.mockResolvedValue([]);
    i18n.changeLanguage('en');
  });

  it('disables area + slot and explains that a site must be picked first', () => {
    renderWithProviders(<Harness />);
    const areaField = within(screen.getByTestId('form-field-location_key')).getByRole('combobox');
    const slotField = within(screen.getByTestId('form-field-slot_key')).getByRole('combobox');
    expect(areaField).toHaveAttribute('aria-disabled', 'true');
    expect(slotField).toHaveAttribute('aria-disabled', 'true');
    expect(screen.getByText('Pick a site first to see its areas.')).toBeTruthy();
    expect(screen.getByText('Pick a site and an area first to choose a slot.')).toBeTruthy();
  });

  it('explains when the selected site has no areas yet', async () => {
    mockGetLocationTree.mockResolvedValue([]);
    const user = userEvent.setup();
    renderWithProviders(<Harness />);
    await selectSite(user);
    await waitFor(() =>
      expect(screen.getByText('This site has no areas yet. Create an area under "Sites" first.')).toBeTruthy(),
    );
  });

  it('enables the area select and shows the optional helper once a site with areas is picked', async () => {
    mockGetLocationTree.mockResolvedValue([treeNode('loc-1', 'Zone A')]);
    const user = userEvent.setup();
    renderWithProviders(<Harness />);
    await selectSite(user);
    await waitFor(() => expect(mockGetLocationTree).toHaveBeenCalledWith('site-1'));
    const areaField = within(screen.getByTestId('form-field-location_key')).getByRole('combobox');
    await waitFor(() => expect(areaField).not.toHaveAttribute('aria-disabled', 'true'));
    expect(screen.getByText('Area within the site (optional)')).toBeTruthy();
  });

  it('explains when the chosen area has no slots', async () => {
    mockGetLocationTree.mockResolvedValue([treeNode('loc-1', 'Zone A')]);
    const user = userEvent.setup();
    renderWithProviders(<Harness slotsForArea={[]} />);
    await selectSite(user);
    await selectArea(user, 'Zone A');
    await waitFor(() =>
      expect(screen.getByText('This area has no slots yet. Create a slot under "Sites" first.')).toBeTruthy(),
    );
    const slotField = within(screen.getByTestId('form-field-slot_key')).getByRole('combobox');
    expect(slotField).toHaveAttribute('aria-disabled', 'true');
  });

  it('enables the slot select and lists slots once an area with slots is chosen', async () => {
    mockGetLocationTree.mockResolvedValue([treeNode('loc-1', 'Zone A')]);
    const user = userEvent.setup();
    renderWithProviders(<Harness slotsForArea={[slot('slot-1', 'A-01')]} />);
    await selectSite(user);
    await selectArea(user, 'Zone A');
    const slotField = within(screen.getByTestId('form-field-slot_key')).getByRole('combobox');
    await waitFor(() => expect(slotField).not.toHaveAttribute('aria-disabled', 'true'));
    await user.click(slotField);
    expect(within(screen.getByRole('listbox')).getByText('A-01')).toBeTruthy();
  });

  it('blocks an occupied slot but keeps the currently assigned one selectable', async () => {
    mockGetLocationTree.mockResolvedValue([treeNode('loc-1', 'Zone A')]);
    const user = userEvent.setup();
    renderWithProviders(
      <Harness
        defaults={{ site_key: 'site-1', location_key: 'loc-1', slot_key: 'slot-own' }}
        slotsForArea={[slot('slot-busy', 'A-02', true), slot('slot-own', 'A-03', true)]}
      />,
    );
    const slotField = within(screen.getByTestId('form-field-slot_key')).getByRole('combobox');
    await waitFor(() => expect(slotField).not.toHaveAttribute('aria-disabled', 'true'));
    await user.click(slotField);
    const listbox = screen.getByRole('listbox');
    const busy = within(listbox).getByText(/A-02 \(occupied\)/).closest('li');
    const own = within(listbox).getByText(/A-03 \(occupied\)/).closest('li');
    expect(busy).toHaveAttribute('aria-disabled', 'true');
    expect(own).not.toHaveAttribute('aria-disabled', 'true');
  });

  it.each(['card', 'inline'] as const)(
    'submits identical site/location/slot field values from the %s variant',
    async (variant) => {
      mockGetLocationTree.mockResolvedValue([treeNode('loc-1', 'Zone A')]);
      const onSubmit = vi.fn();
      const user = userEvent.setup();
      renderWithProviders(
        <Harness variant={variant} onSubmit={onSubmit} slotsForArea={[slot('slot-1', 'A-01')]} />,
      );
      await selectSite(user);
      await selectArea(user, 'Zone A');
      const slotField = within(screen.getByTestId('form-field-slot_key')).getByRole('combobox');
      await waitFor(() => expect(slotField).not.toHaveAttribute('aria-disabled', 'true'));
      await user.click(slotField);
      await user.click(within(screen.getByRole('listbox')).getByText('A-01'));

      await user.click(screen.getByRole('button', { name: 'save' }));

      await waitFor(() => expect(onSubmit).toHaveBeenCalledTimes(1));
      expect(onSubmit).toHaveBeenCalledWith({
        site_key: 'site-1',
        location_key: 'loc-1',
        slot_key: 'slot-1',
      });
    },
  );
});
