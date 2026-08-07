/**
 * Tests for the complete-catalogue paging helper (#995).
 *
 * The behaviour that matters is *termination*: it must keep asking while the
 * endpoint keeps returning full pages, and stop on the first short one. Both
 * directions are asserted, because getting either wrong is silent — stopping
 * early drops rows (the defect this closes), never stopping hangs the view.
 */
import { describe, it, expect, vi } from 'vitest';
import { CATALOGUE_PAGE_SIZE, MAX_PAGE_SIZE, fetchAllPages } from '@/api/paginate';

/** Builds `count` distinct rows, so a lost or duplicated page is visible. */
function rows(count: number, from = 0): { id: number }[] {
  return Array.from({ length: count }, (_, i) => ({ id: from + i }));
}

describe('fetchAllPages', () => {
  it('stops after a single short page', async () => {
    const loadPage = vi.fn().mockResolvedValue(rows(3));
    const all = await fetchAllPages(loadPage, 10);
    expect(loadPage).toHaveBeenCalledTimes(1);
    expect(loadPage).toHaveBeenCalledWith(0, 10);
    expect(all).toHaveLength(3);
  });

  it('keeps paging while pages come back full, and concatenates in order', async () => {
    const loadPage = vi
      .fn()
      .mockResolvedValueOnce(rows(2, 0))
      .mockResolvedValueOnce(rows(2, 2))
      .mockResolvedValueOnce(rows(1, 4));
    const all = await fetchAllPages<{ id: number }>(loadPage, 2);
    expect(loadPage).toHaveBeenCalledTimes(3);
    expect(loadPage).toHaveBeenNthCalledWith(1, 0, 2);
    expect(loadPage).toHaveBeenNthCalledWith(2, 2, 2);
    expect(loadPage).toHaveBeenNthCalledWith(3, 4, 2);
    expect(all.map((r) => r.id)).toEqual([0, 1, 2, 3, 4]);
  });

  it('stops on an exactly-full last page followed by an empty one', async () => {
    // The boundary that a `<=` instead of `<` would get wrong: the catalogue is
    // an exact multiple of the page size, so the short page is the empty one.
    const loadPage = vi
      .fn()
      .mockResolvedValueOnce(rows(2, 0))
      .mockResolvedValueOnce(rows(0));
    const all = await fetchAllPages(loadPage, 2);
    expect(loadPage).toHaveBeenCalledTimes(2);
    expect(all).toHaveLength(2);
  });

  it('terminates against an endpoint that ignores the offset', async () => {
    // Without the loop bound this is an infinite loop, i.e. a hung list view.
    const loadPage = vi.fn().mockResolvedValue(rows(1));
    const all = await fetchAllPages(loadPage, 1);
    expect(loadPage).toHaveBeenCalledTimes(1000);
    expect(all).toHaveLength(1000);
  });

  it('defaults to the backend page cap', async () => {
    const loadPage = vi.fn().mockResolvedValue([]);
    await fetchAllPages(loadPage);
    expect(loadPage).toHaveBeenCalledWith(0, CATALOGUE_PAGE_SIZE);
    expect(CATALOGUE_PAGE_SIZE).toBe(MAX_PAGE_SIZE);
  });

  it('propagates a rejection instead of returning a partial result', async () => {
    // A caught-and-ignored page error would produce a silently short catalogue —
    // the same class of defect, one layer down.
    const loadPage = vi
      .fn()
      .mockResolvedValueOnce(rows(2, 0))
      .mockRejectedValueOnce(new Error('page 2 failed'));
    await expect(fetchAllPages(loadPage, 2)).rejects.toThrow('page 2 failed');
  });
});
