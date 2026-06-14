import { describe, it, expect } from 'vitest';
import reducer, {
  clearCurrentPlan,
  clearError,
  fetchNutrientPlans,
  fetchNutrientPlan,
} from '@/store/slices/nutrientPlansSlice';

const baseState = { plans: [], currentPlan: null, loading: false, error: null };

describe('nutrientPlansSlice', () => {
  it('has the empty initial state', () => {
    expect(reducer(undefined, { type: 'unknown' })).toEqual(baseState);
  });

  it('clearCurrentPlan resets the selection', () => {
    const state = reducer({ ...baseState, currentPlan: { key: 'p1' } as never }, clearCurrentPlan());
    expect(state.currentPlan).toBeNull();
  });

  it('clearError resets the error', () => {
    const state = reducer({ ...baseState, error: 'boom' }, clearError());
    expect(state.error).toBeNull();
  });

  it('fetchNutrientPlans.pending sets loading and clears prior error', () => {
    const state = reducer({ ...baseState, error: 'old' }, { type: fetchNutrientPlans.pending.type });
    expect(state.loading).toBe(true);
    expect(state.error).toBeNull();
  });

  it('fetchNutrientPlans.fulfilled stores the plans', () => {
    const plans = [{ key: 'p1' }];
    const state = reducer(undefined, { type: fetchNutrientPlans.fulfilled.type, payload: plans });
    expect(state.plans).toEqual(plans);
    expect(state.loading).toBe(false);
  });

  it('fetchNutrientPlans.rejected stores the error', () => {
    const state = reducer(undefined, { type: fetchNutrientPlans.rejected.type, error: { message: 'fail' } });
    expect(state.error).toBe('fail');
  });

  it('fetchNutrientPlans.rejected falls back to a default message', () => {
    const state = reducer(undefined, { type: fetchNutrientPlans.rejected.type, error: {} });
    expect(state.error).toBe('Failed to load nutrient plans');
  });

  it('fetchNutrientPlan.fulfilled stores the selected plan', () => {
    const plan = { key: 'p1' };
    const state = reducer(undefined, { type: fetchNutrientPlan.fulfilled.type, payload: plan });
    expect(state.currentPlan).toEqual(plan);
  });
});
