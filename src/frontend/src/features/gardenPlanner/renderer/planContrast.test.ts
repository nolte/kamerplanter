/**
 * Non-text contrast of the plan (REQ-053 GP-NFR-024, WCAG 1.4.11): every line and mark that tells
 * one thing on the plan from another - outlines, the garden boundary, plants, empty slots, the
 * selection - is at least 3:1 against the canvas in every theme. Fills are translucent washes and
 * carry no information on their own (the outline and a dash pattern do), so they are not measured.
 */
import { describe, expect, it } from 'vitest';
import { decomposeColor, type Theme } from '@mui/material/styles';
import { darkTheme, highContrastTheme, lightTheme } from '@/theme/theme';
import { planPalette } from './SvgPlanRenderer';

type Rgb = [number, number, number];

/** `color` flattened onto `backdrop` (rgba -> rgb), as the browser paints it. */
function flatten(color: string, backdrop: Rgb): Rgb {
  const { values } = decomposeColor(color);
  const alpha = values[3] ?? 1;
  return [0, 1, 2].map((i) => Math.round(values[i] * alpha + backdrop[i] * (1 - alpha))) as Rgb;
}

function luminance([r, g, b]: Rgb): number {
  const [lr, lg, lb] = [r, g, b].map((v) => {
    const c = v / 255;
    return c <= 0.03928 ? c / 12.92 : ((c + 0.055) / 1.055) ** 2.4;
  });
  return 0.2126 * lr + 0.7152 * lg + 0.0722 * lb;
}

function contrast(foreground: string, background: string): number {
  const back = flatten(background, [255, 255, 255]);
  const high = luminance(flatten(foreground, back));
  const low = luminance(back);
  return (Math.max(high, low) + 0.05) / (Math.min(high, low) + 0.05);
}

const THEMES: [string, Theme][] = [
  ['light', lightTheme],
  ['dark', darkTheme],
  ['high contrast', highContrastTheme],
];

describe.each(THEMES)('plan elements in the %s theme', (_name, theme) => {
  const palette = planPalette(theme);
  const canvas = theme.palette.background.paper;

  it.each(['stroke', 'boundary', 'selected', 'plant', 'slot', 'text'] as const)(
    '%s reaches 3:1 against the canvas',
    (name) => {
      expect(contrast(palette[name], canvas)).toBeGreaterThanOrEqual(3);
    },
  );

  it.each(['badgeOverdue', 'badgeOpen'] as const)('the %s badge is 3:1 against the canvas and its number 4.5:1 on it', (name) => {
    expect(contrast(palette[name].fill, canvas)).toBeGreaterThanOrEqual(3);
    expect(contrast(palette[name].text, palette[name].fill)).toBeGreaterThanOrEqual(4.5);
  });

  it('draws the invalid-ghost red and the draft blue at 3:1 too', () => {
    expect(contrast(theme.palette.error.main, canvas)).toBeGreaterThanOrEqual(3);
    expect(contrast(theme.palette.primary.main, canvas)).toBeGreaterThanOrEqual(3);
  });
});

describe('the measuring stick', () => {
  it('rejects the colour the plan used to draw its boundary with (text.disabled on white)', () => {
    expect(contrast('rgba(0, 0, 0, 0.38)', '#ffffff')).toBeLessThan(3);
    expect(contrast('rgba(0, 0, 0, 0.6)', '#ffffff')).toBeGreaterThan(5);
  });
});
