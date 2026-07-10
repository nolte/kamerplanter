import type { ReactNode } from 'react';
import { renderHook, act, waitFor } from '@testing-library/react';
import { describe, it, expect, beforeEach, afterAll, vi } from 'vitest';
import { Provider } from 'react-redux';
import { MemoryRouter } from 'react-router-dom';
import { SnackbarProvider } from 'notistack';
import i18n from 'i18next';
import type { NutrientPlan, NutrientPlanPhaseEntry } from '@/api/types';
import type { EditFormData } from '@/pages/duengung/nutrient-plan-detail/nutrientPlanSchema';
import { createTestStore } from '../helpers';

let paramsKey: string | undefined = 'np-1';
const navigate = vi.fn();
vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual<typeof import('react-router-dom')>('react-router-dom');
  return {
    ...actual,
    useParams: () => ({ key: paramsKey }),
    useNavigate: () => navigate,
  };
});

vi.mock('@/api/endpoints/nutrient-plans', () => ({
  fetchNutrientPlan: vi.fn(),
  fetchPhaseEntries: vi.fn(),
  validateNutrientPlan: vi.fn(),
  deleteNutrientPlan: vi.fn(),
  updateNutrientPlan: vi.fn(),
}));
vi.mock('@/api/endpoints/fertilizers', () => ({
  fetchFertilizers: vi.fn(),
}));

import * as planApi from '@/api/endpoints/nutrient-plans';
import * as fertApi from '@/api/endpoints/fertilizers';
import { useNutrientPlanData } from '@/pages/duengung/nutrient-plan-detail/useNutrientPlanData';

function installLocalStorage() {
  const store = new Map<string, string>();
  Object.defineProperty(globalThis, 'localStorage', {
    configurable: true,
    value: {
      getItem: (k: string) => (store.has(k) ? store.get(k)! : null),
      setItem: (k: string, v: string) => void store.set(k, String(v)),
      removeItem: (k: string) => void store.delete(k),
      clear: () => store.clear(),
    },
  });
}

function makePlan(overrides: Partial<NutrientPlan> = {}): NutrientPlan {
  return {
    key: 'np-1',
    name: 'Veg Plan',
    description: 'desc',
    recommended_substrate_type: null,
    reference_substrate_type: 'soil',
    author: 'me',
    is_template: false,
    version: '1.0',
    tags: ['a'],
    cloned_from_key: null,
    watering_schedule: null,
    water_mix_ratio_ro_percent: null,
    cycle_restart_from_sequence: null,
    created_at: '2024-01-01T00:00:00Z',
    updated_at: null,
    ...overrides,
  } as NutrientPlan;
}

function makeEditData(overrides: Partial<EditFormData> = {}): EditFormData {
  return {
    name: 'New name',
    description: 'd',
    recommended_substrate_type: null,
    reference_substrate_type: 'soil',
    author: '',
    is_template: false,
    version: '1',
    tags: [],
    schedule_enabled: false,
    schedule_mode: 'weekdays',
    weekday_schedule: [],
    interval_days: null,
    preferred_time: '',
    application_method: 'drench',
    reminder_hours_before: 2,
    times_per_day: 1,
    water_mix_ratio_ro_percent: null,
    cycle_restart_from_sequence: null,
    ...overrides,
  };
}

function makeWrapper(route = '/plan') {
  const store = createTestStore();
  return function Wrapper({ children }: { children: ReactNode }) {
    return (
      <Provider store={store}>
        <MemoryRouter initialEntries={[route]}>
          <SnackbarProvider>{children}</SnackbarProvider>
        </MemoryRouter>
      </Provider>
    );
  };
}

async function renderLoaded(route = '/plan') {
  const view = renderHook(() => useNutrientPlanData(), { wrapper: makeWrapper(route) });
  await waitFor(() => expect(view.result.current.loading).toBe(false));
  return view;
}

const entries: NutrientPlanPhaseEntry[] = [];

describe('useNutrientPlanData', () => {
  beforeEach(() => {
    installLocalStorage();
    paramsKey = 'np-1';
    i18n.changeLanguage('de');
    navigate.mockReset();
    vi.mocked(planApi.fetchNutrientPlan).mockReset().mockResolvedValue(makePlan());
    vi.mocked(planApi.fetchPhaseEntries).mockReset().mockResolvedValue(entries);
    vi.mocked(planApi.validateNutrientPlan).mockReset().mockResolvedValue({
      completeness: { complete: true, issues: [] },
      channel_validations: [],
      valid: true,
    });
    vi.mocked(planApi.deleteNutrientPlan).mockReset().mockResolvedValue(undefined);
    vi.mocked(planApi.updateNutrientPlan).mockReset().mockResolvedValue(makePlan());
    vi.mocked(fertApi.fetchFertilizers).mockReset().mockResolvedValue([]);
  });

  afterAll(() => {
    i18n.changeLanguage('en');
  });

  it('loads the plan, entries and fertilizers on mount', async () => {
    const { result } = await renderLoaded();
    expect(result.current.plan?.name).toBe('Veg Plan');
    expect(result.current.error).toBeNull();
    expect(planApi.fetchNutrientPlan).toHaveBeenCalledWith('np-1');
    expect(fertApi.fetchFertilizers).toHaveBeenCalledWith(0, 200);
  });

  it('captures a load error', async () => {
    vi.mocked(planApi.fetchNutrientPlan).mockRejectedValueOnce(new Error('load boom'));
    const { result } = renderHook(() => useNutrientPlanData(), { wrapper: makeWrapper() });
    await waitFor(() => expect(result.current.error).toContain('load boom'));
    expect(result.current.plan).toBeNull();
  });

  it('resolves origin protection for a system plan', async () => {
    vi.mocked(planApi.fetchNutrientPlan).mockResolvedValue(
      makePlan({ origin: 'system' } as Partial<NutrientPlan>),
    );
    const { result } = await renderLoaded();
    expect(result.current.isReadOnly).toBe(true);
    expect(result.current.canCopyAsTemplate).toBe(true);
    expect(result.current.planOrigin).toBe('system');
  });

  it('seeds the form from a plan that carries a weekday schedule', async () => {
    vi.mocked(planApi.fetchNutrientPlan).mockResolvedValue(
      makePlan({
        watering_schedule: {
          schedule_mode: 'weekdays',
          weekday_schedule: [0, 2],
          interval_days: null,
          preferred_time: '08:00',
          application_method: 'drench',
          reminder_hours_before: 2,
          times_per_day: 1,
        },
      } as Partial<NutrientPlan>),
    );
    const { result } = await renderLoaded();
    expect(result.current.editScheduleEnabled).toBe(true);
    expect(result.current.editWeekdaySchedule).toEqual([0, 2]);
    expect(result.current.editScheduleMode).toBe('weekdays');
  });

  it('saves a plan with a weekday watering schedule', async () => {
    const { result } = await renderLoaded();
    await act(async () =>
      result.current.onSave(
        makeEditData({ schedule_enabled: true, schedule_mode: 'weekdays', weekday_schedule: [1, 3] }),
      ),
    );
    const payload = vi.mocked(planApi.updateNutrientPlan).mock.calls[0][1];
    expect(payload.watering_schedule).not.toBeNull();
    expect(payload.watering_schedule?.weekday_schedule).toEqual([1, 3]);
  });

  it('saves a plan with an interval watering schedule', async () => {
    const { result } = await renderLoaded();
    await act(async () =>
      result.current.onSave(
        makeEditData({ schedule_enabled: true, schedule_mode: 'interval', interval_days: 5 }),
      ),
    );
    const payload = vi.mocked(planApi.updateNutrientPlan).mock.calls[0][1];
    expect(payload.watering_schedule?.interval_days).toBe(5);
  });

  it('clears the watering schedule when it is incomplete or disabled', async () => {
    const { result } = await renderLoaded();
    // enabled but no weekdays selected → hasSchedule false
    await act(async () =>
      result.current.onSave(
        makeEditData({ schedule_enabled: true, schedule_mode: 'weekdays', weekday_schedule: [] }),
      ),
    );
    expect(vi.mocked(planApi.updateNutrientPlan).mock.calls[0][1].watering_schedule).toBeNull();
  });

  it('surfaces a save error', async () => {
    vi.mocked(planApi.updateNutrientPlan).mockRejectedValueOnce(new Error('boom'));
    const { result } = await renderLoaded();
    await act(async () => result.current.onSave(makeEditData()));
    expect(result.current.saving).toBe(false);
  });

  it('deletes the plan and navigates back to the list', async () => {
    const { result } = await renderLoaded();
    await act(async () => result.current.onDelete());
    expect(planApi.deleteNutrientPlan).toHaveBeenCalledWith('np-1');
    expect(navigate).toHaveBeenCalledWith('/duengung/plans');
  });

  it('does not navigate when deletion fails', async () => {
    vi.mocked(planApi.deleteNutrientPlan).mockRejectedValueOnce(new Error('boom'));
    const { result } = await renderLoaded();
    await act(async () => result.current.onDelete());
    expect(navigate).not.toHaveBeenCalled();
    expect(result.current.deleting).toBe(false);
  });

  it('loads validation automatically when the validation tab is active', async () => {
    const { result } = await renderLoaded('/plan#validation');
    expect(result.current.tab).toBe(1);
    await waitFor(() => expect(result.current.validation).not.toBeNull());
    expect(planApi.validateNutrientPlan).toHaveBeenCalledWith('np-1');
    expect(result.current.validating).toBe(false);
  });

  it('surfaces a validation error without setting a result', async () => {
    vi.mocked(planApi.validateNutrientPlan).mockRejectedValueOnce(new Error('bad'));
    const { result } = await renderLoaded('/plan#validation');
    await waitFor(() => expect(result.current.validating).toBe(false));
    expect(result.current.validation).toBeNull();
  });

  it('toggles a single weekday on and off', async () => {
    const { result } = await renderLoaded();
    act(() => result.current.handleEditWeekdayToggle(2));
    expect(result.current.editWeekdaySchedule).toEqual([2]);
    act(() => result.current.handleEditWeekdayToggle(2));
    expect(result.current.editWeekdaySchedule).toEqual([]);
  });

  it('switches tabs through the URL hash and toggles favorites', async () => {
    const { result } = await renderLoaded();
    act(() => result.current.setTab(1));
    expect(navigate).toHaveBeenCalledWith({ hash: 'validation' }, { replace: true });

    act(() => result.current.toggleFavorite('np-1'));
    expect(result.current.isFavorite('np-1')).toBe(true);

    act(() => result.current.resetForm());
    act(() => result.current.setDeleteOpen(true));
    expect(result.current.deleteOpen).toBe(true);
  });

  it('does nothing without a plan key', async () => {
    paramsKey = undefined;
    const { result } = renderHook(() => useNutrientPlanData(), { wrapper: makeWrapper() });
    await act(async () => result.current.onSave(makeEditData()));
    await act(async () => result.current.onDelete());
    expect(planApi.fetchNutrientPlan).not.toHaveBeenCalled();
    expect(planApi.updateNutrientPlan).not.toHaveBeenCalled();
    expect(planApi.deleteNutrientPlan).not.toHaveBeenCalled();
  });
});
