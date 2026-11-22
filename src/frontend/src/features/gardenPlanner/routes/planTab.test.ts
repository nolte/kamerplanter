import { describe, expect, it } from 'vitest';
import { isTabOnlyChange, planTabSearch, resolvePlanTab } from './planTab';

const at = (search: string, pathname = '/standorte/sites/site_1/plan', hash = '') => ({ pathname, search, hash });

describe('resolvePlanTab (GP-UX-064)', () => {
  it('takes the three known values and falls back to the plan for a missing or unknown one', () => {
    expect(resolvePlanTab('plan')).toBe('plan');
    expect(resolvePlanTab('list')).toBe('list');
    expect(resolvePlanTab('beds')).toBe('beds');
    expect(resolvePlanTab(null)).toBe('plan');
    expect(resolvePlanTab('')).toBe('plan');
    expect(resolvePlanTab('xyz')).toBe('plan');
    expect(resolvePlanTab('BEDS')).toBe('plan');
  });
});

describe('planTabSearch', () => {
  it('sets the tab and keeps every other parameter', () => {
    const next = planTabSearch(new URLSearchParams('mode=plan&tab=list&year=2026'), 'beds');
    expect(next.get('tab')).toBe('beds');
    expect(next.get('mode')).toBe('plan');
    expect(next.get('year')).toBe('2026');
  });
});

describe('isTabOnlyChange (GP-UX-065)', () => {
  it('lets a move between tabs through, in any parameter order', () => {
    expect(isTabOnlyChange(at(''), at('?tab=beds'))).toBe(true);
    expect(isTabOnlyChange(at('?mode=plan&tab=list'), at('?tab=plan&mode=plan'))).toBe(true);
  });

  it('does not for another route, another mode, another hash or another parameter', () => {
    expect(isTabOnlyChange(at('?tab=beds'), at('', '/standorte/sites/site_1'))).toBe(false);
    expect(isTabOnlyChange(at('?tab=beds'), at('?tab=beds&mode=field'))).toBe(false);
    expect(isTabOnlyChange(at('?mode=plan'), at('?mode=field'))).toBe(false);
    expect(isTabOnlyChange(at(''), at('', undefined, '#care'))).toBe(false);
    expect(isTabOnlyChange(at('?tab=plan'), at('?tab=plan&year=2025'))).toBe(false);
  });
});
