import { describe, it, expect } from 'vitest';
import { stripHtml } from '@/utils/formatting';

describe('stripHtml', () => {
  it('removes anchor markup from Wikimedia attributions', () => {
    const raw =
      '<a rel="nofollow" class="external text" href="https://flickr.com/x">INRA DIST</a> from France';
    expect(stripHtml(raw)).toBe('INRA DIST from France');
  });

  it('decodes HTML entities', () => {
    expect(stripHtml('Jane &amp; John')).toBe('Jane & John');
  });

  it('collapses whitespace', () => {
    expect(stripHtml('  Jane\n  Doe  ')).toBe('Jane Doe');
  });

  it('leaves plain text unchanged', () => {
    expect(stripHtml('rarehero')).toBe('rarehero');
  });

  it('returns empty string for nullish input', () => {
    expect(stripHtml(null)).toBe('');
    expect(stripHtml(undefined)).toBe('');
  });
});
