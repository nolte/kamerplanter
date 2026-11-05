import { describe, it, expect, vi } from 'vitest';

const slug = vi.hoisted(() => ({ current: 'mein-garten' as string | null }));

vi.mock('@/api/client', () => ({
  __esModule: true,
  getActiveTenantSlug: () => slug.current,
}));

import { attachmentUri } from '@/api/endpoints/attachments';

describe('attachmentUri — the one builder for photo URIs from bare attachment ids', () => {
  it('builds the original and the rendition URI from the id and the active slug', () => {
    // Diary entries, tasks and beds store bare ids (NFR-013 §2.2 / AC-09); the URI
    // is rebuilt at render time, which is what survives a tenant rename.
    slug.current = 'mein-garten';
    expect(attachmentUri('att-1')).toBe('/api/v1/t/mein-garten/attachments/att-1');
    expect(attachmentUri('att-1', 512)).toBe('/api/v1/t/mein-garten/attachments/att-1/thumbnails/512');
    expect(attachmentUri('att-1', 128)).toMatch(/\/attachments\/att-1\/thumbnails\/128$/);
  });

  it('encodes slug and id as one path segment each', () => {
    slug.current = 'a/b';
    expect(attachmentUri('x/../y?z', 1280)).toBe('/api/v1/t/a%2Fb/attachments/x%2F..%2Fy%3Fz/thumbnails/1280');
  });

  it('builds an empty slug segment without an active tenant', () => {
    slug.current = null;
    expect(attachmentUri('att-1')).toBe('/api/v1/t//attachments/att-1');
  });
});
