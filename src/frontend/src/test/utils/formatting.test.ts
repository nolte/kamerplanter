import { describe, it, expect } from 'vitest';
import { formatDate, stripHtml } from '@/utils/formatting';

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

describe('formatDate', () => {
  it('renders a bare YYYY-MM-DD string as the same local calendar day', () => {
    // Regression: `new Date('2026-07-06')` is UTC midnight, which renders as
    // 2026-07-05 in negative-UTC-offset zones. A date-only string must format
    // identically to the local `Date` for that calendar day, regardless of the
    // runtime timezone offset — never the previous day.
    const fromString = formatDate('2026-07-06');
    const fromLocalDate = formatDate(new Date(2026, 6, 6));
    expect(fromString).toBe(fromLocalDate);
    expect(fromString).not.toBe('—');
    // The rendered day component is the 6th, not the 5th (the off-by-one bug).
    expect(fromString).toContain('06');
    expect(fromString).not.toContain('05');
  });

  it('returns the placeholder for nullish input', () => {
    expect(formatDate(null)).toBe('—');
    expect(formatDate(undefined)).toBe('—');
  });
});
