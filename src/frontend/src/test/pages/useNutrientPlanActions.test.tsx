import type { ReactNode } from 'react';
import { renderHook, act } from '@testing-library/react';
import { describe, it, expect, beforeEach, afterAll, vi } from 'vitest';
import { SnackbarProvider } from 'notistack';
import i18n from 'i18next';
import type {
  NutrientPlan,
  NutrientPlanPhaseEntry,
  DeliveryChannel,
  Fertilizer,
  FertilizerDosage,
} from '@/api/types';

vi.mock('@/api/endpoints/nutrient-plans', () => ({
  deletePhaseEntry: vi.fn(),
  removeFertilizerFromChannel: vi.fn(),
  updatePhaseEntry: vi.fn(),
  addFertilizerToChannel: vi.fn(),
}));

import * as planApi from '@/api/endpoints/nutrient-plans';
import { useNutrientPlanActions } from '@/pages/duengung/nutrient-plan-detail/useNutrientPlanActions';

function wrapper({ children }: { children: ReactNode }) {
  return <SnackbarProvider>{children}</SnackbarProvider>;
}

function makeDosage(overrides: Partial<FertilizerDosage> = {}): FertilizerDosage {
  return { fertilizer_key: 'f1', ml_per_liter: 2, optional: false, mixing_order: 1, ...overrides };
}

function makeChannel(overrides: Partial<DeliveryChannel> = {}): DeliveryChannel {
  return {
    channel_id: 'c1',
    label: 'Channel One',
    application_method: 'drench',
    enabled: true,
    notes: null,
    schedule: null,
    target_ec_ms: 1.2,
    target_ph: 6,
    fertilizer_dosages: [makeDosage()],
    method_params: { method: 'drench', volume_per_feeding_liters: 5 },
    ...overrides,
  } as DeliveryChannel;
}

function makeEntry(overrides: Partial<NutrientPlanPhaseEntry> = {}): NutrientPlanPhaseEntry {
  return {
    key: 'e1',
    plan_key: 'np-1',
    phase_name: 'vegetative',
    sequence_order: 1,
    week_start: 1,
    week_end: 4,
    is_recurring: false,
    npk_ratio: [3, 1, 2],
    calcium_ppm: null,
    magnesium_ppm: null,
    target_ec_ms: 1.2,
    reference_ec_ms: null,
    target_calcium_ppm: null,
    target_magnesium_ppm: null,
    reference_base_ec: 0.3,
    notes: null,
    delivery_channels: [makeChannel()],
    watering_schedule_override: null,
    water_mix_ratio_ro_percent: null,
    created_at: null,
    updated_at: null,
    ...overrides,
  };
}

const plan = { key: 'np-1', name: 'Plan' } as NutrientPlan;
const fertilizers = [{ key: 'f1', product_name: 'Grow' } as Fertilizer];

function setup(args: {
  key?: string | undefined;
  plan?: NutrientPlan | null;
  entries?: NutrientPlanPhaseEntry[];
  fertilizers?: Fertilizer[];
} = {}) {
  const load = vi.fn().mockResolvedValue(undefined);
  const { result } = renderHook(
    () =>
      useNutrientPlanActions({
        key: 'key' in args ? args.key : 'np-1',
        plan: args.plan ?? plan,
        entries: args.entries ?? [makeEntry()],
        fertilizers: args.fertilizers ?? fertilizers,
        load,
      }),
    { wrapper },
  );
  return { result, load };
}

describe('useNutrientPlanActions', () => {
  beforeEach(() => {
    i18n.changeLanguage('de');
    vi.mocked(planApi.deletePhaseEntry).mockReset().mockResolvedValue(undefined);
    vi.mocked(planApi.removeFertilizerFromChannel).mockReset().mockResolvedValue(undefined);
    vi.mocked(planApi.updatePhaseEntry).mockReset().mockResolvedValue({} as never);
    vi.mocked(planApi.addFertilizerToChannel).mockReset().mockResolvedValue({} as never);
  });

  afterAll(() => {
    i18n.changeLanguage('en');
  });

  it('toggles a row expansion on and off', () => {
    const { result } = setup();
    act(() => result.current.toggleExpanded('e1'));
    expect(result.current.expandedEntries.has('e1')).toBe(true);
    act(() => result.current.toggleExpanded('e1'));
    expect(result.current.expandedEntries.has('e1')).toBe(false);
  });

  it('opens the add- and edit-entry dialogs', () => {
    const { result } = setup();
    act(() => result.current.openAddEntry());
    expect(result.current.entryDialogOpen).toBe(true);
    expect(result.current.editingEntry).toBeNull();

    act(() => result.current.closeEntryDialog());
    expect(result.current.entryDialogOpen).toBe(false);

    const entry = makeEntry();
    act(() => result.current.openEditEntry(entry));
    expect(result.current.entryDialogOpen).toBe(true);
    expect(result.current.editingEntry).toBe(entry);
  });

  it('runs the entry-saved refresh callback', async () => {
    const { result, load } = setup();
    await act(async () => result.current.onEntrySaved());
    expect(result.current.entryDialogOpen).toBe(false);
    expect(load).toHaveBeenCalledWith(true);
  });

  it('deletes a phase entry and closes the confirm dialog', async () => {
    const entry = makeEntry();
    const { result, load } = setup();
    act(() => result.current.openDeleteEntry(entry));
    expect(result.current.deleteEntryOpen).toBe(true);
    await act(async () => result.current.onDeleteEntry());
    expect(planApi.deletePhaseEntry).toHaveBeenCalledWith('np-1', 'e1');
    expect(result.current.deleteEntryOpen).toBe(false);
    expect(load).toHaveBeenCalledWith(true);
  });

  it('keeps the delete dialog open when the delete request fails', async () => {
    vi.mocked(planApi.deletePhaseEntry).mockRejectedValueOnce(new Error('boom'));
    const entry = makeEntry();
    const { result } = setup();
    act(() => result.current.openDeleteEntry(entry));
    await act(async () => result.current.onDeleteEntry());
    expect(result.current.deletingEntryPending).toBe(false);
    expect(result.current.deleteEntryOpen).toBe(true);
  });

  it('cancels the delete confirmation and does nothing without a selected entry', async () => {
    const { result } = setup();
    act(() => result.current.cancelDeleteEntry());
    await act(async () => result.current.onDeleteEntry());
    expect(planApi.deletePhaseEntry).not.toHaveBeenCalled();
  });

  it('removes a single channel fertilizer, handling success and error', async () => {
    const { result, load } = setup();
    await act(async () => result.current.onRemoveChannelFertilizer('e1', 'c1', 'f1'));
    expect(planApi.removeFertilizerFromChannel).toHaveBeenCalledWith('e1', 'c1', 'f1');
    expect(load).toHaveBeenCalledWith(true);

    vi.mocked(planApi.removeFertilizerFromChannel).mockRejectedValueOnce(new Error('x'));
    await act(async () => result.current.onRemoveChannelFertilizer('e1', 'c1', 'f1'));
    // no throw — error swallowed by handleError
    expect(planApi.removeFertilizerFromChannel).toHaveBeenCalledTimes(2);
  });

  it('opens the remove-from-all confirm with a resolved fertilizer name', () => {
    const { result } = setup();
    act(() => result.current.onRemoveFertilizerFromGantt('f1', false, [makeEntry()]));
    expect(result.current.removeFertAllOpen).toBe(true);
    expect(result.current.removeFertAllPayload?.fertilizerName).toBe('Grow');
    expect(result.current.removeFertAllPayload?.targets).toHaveLength(1);
  });

  it('falls back to the fertilizer key when the fertilizer is unknown', () => {
    const { result } = setup({ fertilizers: [] });
    act(() => result.current.onRemoveFertilizerFromGantt('f1', false, [makeEntry()]));
    expect(result.current.removeFertAllPayload?.fertilizerName).toBe('f1');
  });

  it('does not open the remove-from-all confirm when no target matches', () => {
    const { result } = setup();
    // isAuto=true but the only channel is a manual (drench) channel → no targets
    act(() => result.current.onRemoveFertilizerFromGantt('f1', true, [makeEntry()]));
    expect(result.current.removeFertAllOpen).toBe(false);
    expect(result.current.removeFertAllPayload).toBeNull();
  });

  it('confirms removal from all matching targets', async () => {
    const { result, load } = setup();
    act(() => result.current.onRemoveFertilizerFromGantt('f1', false, [makeEntry()]));
    await act(async () => result.current.onConfirmRemoveFertilizerFromAll());
    expect(planApi.removeFertilizerFromChannel).toHaveBeenCalledWith('e1', 'c1', 'f1');
    expect(load).toHaveBeenCalledWith(true);
    expect(result.current.removeFertAllOpen).toBe(false);
  });

  it('confirm-remove-all is a no-op without a payload, and cancels cleanly', async () => {
    const { result } = setup();
    act(() => result.current.cancelRemoveFertAll());
    await act(async () => result.current.onConfirmRemoveFertilizerFromAll());
    expect(planApi.removeFertilizerFromChannel).not.toHaveBeenCalled();
  });

  it('surfaces errors from confirm-remove-all without leaving the dialog open', async () => {
    vi.mocked(planApi.removeFertilizerFromChannel).mockRejectedValueOnce(new Error('boom'));
    const { result } = setup();
    act(() => result.current.onRemoveFertilizerFromGantt('f1', false, [makeEntry()]));
    await act(async () => result.current.onConfirmRemoveFertilizerFromAll());
    expect(result.current.removeFertAllOpen).toBe(false);
    expect(result.current.removingFertAll).toBe(false);
  });

  it('saves a new delivery channel merging default dosages', async () => {
    const { result, load } = setup();
    act(() => result.current.openAddChannel('e1', ['c1']));
    expect(result.current.channelDialogOpen).toBe(true);
    await act(async () =>
      result.current.onSaveChannel({ channel_id: 'c2', application_method: 'drench' }),
    );
    expect(planApi.updatePhaseEntry).toHaveBeenCalledWith('np-1', 'e1', {
      delivery_channels: expect.arrayContaining([
        expect.objectContaining({ channel_id: 'c2', fertilizer_dosages: [] }),
      ]),
    });
    expect(result.current.channelDialogOpen).toBe(false);
    expect(load).toHaveBeenCalledWith(true);
  });

  it('saves an edited channel preserving its existing dosages', async () => {
    const entry = makeEntry();
    const { result } = setup({ entries: [entry] });
    act(() => result.current.onEditChannel('e1', entry.delivery_channels[0]));
    expect(result.current.editingChannel).toEqual(entry.delivery_channels[0]);
    await act(async () =>
      result.current.onSaveChannel({ channel_id: 'c1', application_method: 'drench' }),
    );
    const call = vi.mocked(planApi.updatePhaseEntry).mock.calls[0][2];
    const saved = call.delivery_channels!.find((ch) => ch.channel_id === 'c1');
    expect(saved?.fertilizer_dosages).toHaveLength(1);
  });

  it('save-channel is a no-op without an active entry key, and when the entry is missing', async () => {
    const { result } = setup();
    // channelDialogEntryKey is '' initially → early return
    await act(async () =>
      result.current.onSaveChannel({ channel_id: 'c9', application_method: 'drench' }),
    );
    expect(planApi.updatePhaseEntry).not.toHaveBeenCalled();

    // entry key set but not present in entries → inner return
    act(() => result.current.openAddChannel('missing', []));
    await act(async () =>
      result.current.onSaveChannel({ channel_id: 'c9', application_method: 'drench' }),
    );
    expect(planApi.updatePhaseEntry).not.toHaveBeenCalled();
  });

  it('surfaces save-channel errors', async () => {
    vi.mocked(planApi.updatePhaseEntry).mockRejectedValueOnce(new Error('boom'));
    const { result } = setup();
    act(() => result.current.openAddChannel('e1', []));
    await act(async () =>
      result.current.onSaveChannel({ channel_id: 'c2', application_method: 'drench' }),
    );
    // dialog stays open because the catch runs before the close
    expect(result.current.channelDialogOpen).toBe(true);
  });

  it('deletes a delivery channel through the confirm', async () => {
    const { result, load } = setup();
    act(() => result.current.openDeleteChannel('e1', 'c1'));
    expect(result.current.deleteChannelOpen).toBe(true);
    await act(async () => result.current.onDeleteChannel());
    expect(planApi.updatePhaseEntry).toHaveBeenCalledWith('np-1', 'e1', { delivery_channels: [] });
    expect(result.current.deleteChannelOpen).toBe(false);
    expect(load).toHaveBeenCalledWith(true);
  });

  it('delete-channel is a no-op without a selection, and when the entry is missing', async () => {
    const { result } = setup();
    await act(async () => result.current.onDeleteChannel());
    expect(planApi.updatePhaseEntry).not.toHaveBeenCalled();

    act(() => result.current.openDeleteChannel('missing', 'c1'));
    await act(async () => result.current.onDeleteChannel());
    expect(planApi.updatePhaseEntry).not.toHaveBeenCalled();

    act(() => result.current.cancelDeleteChannel());
    expect(result.current.deleteChannelOpen).toBe(false);
  });

  it('surfaces delete-channel errors', async () => {
    vi.mocked(planApi.updatePhaseEntry).mockRejectedValueOnce(new Error('boom'));
    const { result } = setup();
    act(() => result.current.openDeleteChannel('e1', 'c1'));
    await act(async () => result.current.onDeleteChannel());
    expect(result.current.deletingChannel).toBe(false);
  });

  it('persists only the entries whose channels changed', async () => {
    const entry = makeEntry();
    const { result, load } = setup({ entries: [entry] });
    const changed = { ...entry, delivery_channels: [] };
    await act(async () => result.current.handleEntriesChange([changed]));
    expect(planApi.updatePhaseEntry).toHaveBeenCalledWith('np-1', 'e1', { delivery_channels: [] });
    expect(load).toHaveBeenCalledWith(true);
  });

  it('does not persist unchanged entries or unknown keys', async () => {
    const entry = makeEntry();
    const { result, load } = setup({ entries: [entry] });
    await act(async () =>
      result.current.handleEntriesChange([{ ...entry }, makeEntry({ key: 'ghost' })]),
    );
    expect(planApi.updatePhaseEntry).not.toHaveBeenCalled();
    expect(load).not.toHaveBeenCalled();
  });

  it('surfaces errors while persisting changed entries', async () => {
    vi.mocked(planApi.updatePhaseEntry).mockRejectedValueOnce(new Error('boom'));
    const entry = makeEntry();
    const { result } = setup({ entries: [entry] });
    await act(async () =>
      result.current.handleEntriesChange([{ ...entry, delivery_channels: [] }]),
    );
    expect(planApi.updatePhaseEntry).toHaveBeenCalled();
  });

  it('opens the fertilizer dialog for add and edit', () => {
    const { result } = setup();
    act(() => result.current.onAddChannelFertilizer('e1', 'c1'));
    expect(result.current.fertDialogOpen).toBe(true);
    expect(result.current.editingFertDosage).toBeNull();
    expect(result.current.fertDialogExistingKeys).toEqual(['f1']);

    act(() => result.current.closeFertDialog());
    expect(result.current.fertDialogOpen).toBe(false);

    const dosage = makeDosage();
    act(() => result.current.onEditChannelFertilizer('e1', 'c1', dosage));
    expect(result.current.editingFertDosage).toBe(dosage);
    expect(result.current.fertDialogOpen).toBe(true);
  });

  it('saves added fertilizer dosages without a prior edit', async () => {
    const { result, load } = setup();
    act(() => result.current.onAddChannelFertilizer('e1', 'c1'));
    await act(async () =>
      result.current.onSaveChannelFertilizer([
        { fertilizer_key: 'f2', ml_per_liter: 1, optional: false },
      ]),
    );
    expect(planApi.removeFertilizerFromChannel).not.toHaveBeenCalled();
    expect(planApi.addFertilizerToChannel).toHaveBeenCalledWith('e1', 'c1', expect.objectContaining({ fertilizer_key: 'f2' }));
    expect(result.current.fertDialogOpen).toBe(false);
    expect(load).toHaveBeenCalledWith(true);
  });

  it('removes the previous dosage before re-adding when editing', async () => {
    const dosage = makeDosage({ fertilizer_key: 'f1' });
    const { result } = setup();
    act(() => result.current.onEditChannelFertilizer('e1', 'c1', dosage));
    await act(async () =>
      result.current.onSaveChannelFertilizer([
        { fertilizer_key: 'f1', ml_per_liter: 3, optional: false },
      ]),
    );
    expect(planApi.removeFertilizerFromChannel).toHaveBeenCalledWith('e1', 'c1', 'f1');
    expect(planApi.addFertilizerToChannel).toHaveBeenCalled();
  });

  it('surfaces errors while saving fertilizer dosages', async () => {
    vi.mocked(planApi.addFertilizerToChannel).mockRejectedValueOnce(new Error('boom'));
    const { result } = setup();
    act(() => result.current.onAddChannelFertilizer('e1', 'c1'));
    await act(async () =>
      result.current.onSaveChannelFertilizer([
        { fertilizer_key: 'f2', ml_per_liter: 1, optional: false },
      ]),
    );
    expect(result.current.fertDialogOpen).toBe(true);
  });

  it('opens the watering-log dialog with a drench volume', () => {
    const { result } = setup();
    act(() => result.current.onLogWatering(makeChannel()));
    expect(result.current.wateringLogOpen).toBe(true);
    expect(result.current.wateringLogChannel?.volumeLiters).toBe(5);
    expect(result.current.wateringLogChannel?.channelLabel).toBe('Channel One');
  });

  it('derives a foliar spray volume and falls back to channel id for a blank label', () => {
    const { result } = setup();
    act(() =>
      result.current.onLogWatering(
        makeChannel({
          label: '',
          application_method: 'foliar',
          method_params: { method: 'foliar', volume_per_spray_liters: 3 },
        }),
      ),
    );
    expect(result.current.wateringLogChannel?.volumeLiters).toBe(3);
    expect(result.current.wateringLogChannel?.channelLabel).toBe('c1');
  });

  it('yields a null volume for top-dress channels and for channels without method params', () => {
    const { result } = setup();
    act(() =>
      result.current.onLogWatering(
        makeChannel({
          application_method: 'top_dress',
          method_params: { method: 'top_dress', grams_per_plant: 2, grams_per_m2: null },
        }),
      ),
    );
    expect(result.current.wateringLogChannel?.volumeLiters).toBeNull();

    act(() => result.current.onLogWatering(makeChannel({ method_params: null })));
    expect(result.current.wateringLogChannel?.volumeLiters).toBeNull();
  });

  it('filters out optional dosages and orders the mix for the watering log', () => {
    const channel = makeChannel({
      fertilizer_dosages: [
        makeDosage({ fertilizer_key: 'late', mixing_order: 2 }),
        makeDosage({ fertilizer_key: 'skip', optional: true, mixing_order: 0 }),
        makeDosage({ fertilizer_key: 'early', mixing_order: 1 }),
      ],
    });
    const { result } = setup();
    act(() => result.current.onLogWatering(channel));
    expect(result.current.wateringLogChannel?.fertilizers.map((f) => f.fertilizer_key)).toEqual([
      'early',
      'late',
    ]);
  });

  it('closes the watering-log dialog and reports a logged watering', () => {
    const { result } = setup();
    act(() => result.current.onLogWatering(makeChannel()));
    act(() => result.current.closeWateringLog());
    expect(result.current.wateringLogOpen).toBe(false);
    act(() => result.current.onWateringLogged());
    expect(result.current.wateringLogOpen).toBe(false);
    expect(result.current.wateringLogChannel).toBeUndefined();
  });

  it('closes the channel dialog', () => {
    const { result } = setup();
    act(() => result.current.openAddChannel('e1', []));
    act(() => result.current.closeChannelDialog());
    expect(result.current.channelDialogOpen).toBe(false);
    expect(result.current.editingChannel).toBeNull();
  });

  it('guards every mutation when no plan key is present', async () => {
    const { result } = setup({ key: undefined });
    await act(async () => result.current.onDeleteEntry());
    await act(async () => result.current.handleEntriesChange([makeEntry()]));
    await act(async () =>
      result.current.onSaveChannel({ channel_id: 'c1', application_method: 'drench' }),
    );
    await act(async () => result.current.onDeleteChannel());
    expect(planApi.deletePhaseEntry).not.toHaveBeenCalled();
    expect(planApi.updatePhaseEntry).not.toHaveBeenCalled();
  });
});
