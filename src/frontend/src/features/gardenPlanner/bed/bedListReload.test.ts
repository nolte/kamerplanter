import { describe, expect, it } from 'vitest';
import { bedListReloadToken } from './bedListReload';

describe('bedListReloadToken (#2813)', () => {
  it('changes when a save moves the plan revision, so the bed list fetches again', () => {
    expect(bedListReloadToken('load-1', 4)).not.toBe(bedListReloadToken('load-1', 5));
  });

  it('changes on a new plan load and stays the same while nothing was saved', () => {
    expect(bedListReloadToken('load-1', 4)).not.toBe(bedListReloadToken('load-2', 4));
    expect(bedListReloadToken('load-1', 4)).toBe(bedListReloadToken('load-1', 4));
  });

  it('is null before a plan was requested', () => {
    expect(bedListReloadToken(null, 3)).toBeNull();
  });
});
