import { renderHook, act } from '@testing-library/react';
import { describe, it, expect } from 'vitest';
import { createElement, type ReactNode } from 'react';
import { createMemoryRouter, RouterProvider } from 'react-router-dom';
import { useColumnFilters } from '@/hooks/useColumnFilters';

const FILTER_IDS = ['pest_type', 'difficulty'] as const;

/** Render the hook inside a memory data router so useSearchParams works. */
function renderColumnFilters(initialUrl = '/') {
  function wrapper({ children }: { children: ReactNode }) {
    const router = createMemoryRouter([{ path: '*', element: children }], {
      initialEntries: [initialUrl],
    });
    return createElement(RouterProvider, { router });
  }
  return renderHook(() => useColumnFilters(FILTER_IDS), { wrapper });
}

describe('useColumnFilters', () => {
  it('returns empty selections when no params are present', () => {
    const { result } = renderColumnFilters();
    expect(result.current.values).toEqual({ pest_type: [], difficulty: [] });
    expect(result.current.activeCount).toBe(0);
  });

  it('rehydrates comma-separated multi-values from the URL', () => {
    const { result } = renderColumnFilters('/?pest_type=insect,arachnid&difficulty=hard');
    expect(result.current.values.pest_type).toEqual(['insect', 'arachnid']);
    expect(result.current.values.difficulty).toEqual(['hard']);
    expect(result.current.activeCount).toBe(3);
  });

  it('serialises a selection as a comma-separated param', () => {
    const { result } = renderColumnFilters();
    act(() => result.current.setFilter('pest_type', ['insect', 'mite']));
    expect(result.current.values.pest_type).toEqual(['insect', 'mite']);
    expect(result.current.activeCount).toBe(2);
  });

  it('drops the param entirely when a selection becomes empty', () => {
    const { result } = renderColumnFilters('/?pest_type=insect');
    expect(result.current.values.pest_type).toEqual(['insect']);
    act(() => result.current.setFilter('pest_type', []));
    expect(result.current.values.pest_type).toEqual([]);
  });

  it('leaves other filter params untouched when updating one', () => {
    const { result } = renderColumnFilters('/?difficulty=easy');
    act(() => result.current.setFilter('pest_type', ['insect']));
    expect(result.current.values.pest_type).toEqual(['insect']);
    expect(result.current.values.difficulty).toEqual(['easy']);
  });

  it('clears all owned filter params via clearAll', () => {
    const { result } = renderColumnFilters('/?pest_type=insect&difficulty=hard');
    expect(result.current.activeCount).toBe(2);
    act(() => result.current.clearAll());
    expect(result.current.values).toEqual({ pest_type: [], difficulty: [] });
    expect(result.current.activeCount).toBe(0);
  });
});
