import { afterEach, describe, expect, it } from 'vitest';
import { cleanup, render } from '@testing-library/react';
import { ThemeProvider, getContrastRatio } from '@mui/material/styles';
import Alert from '@mui/material/Alert';
import Chip from '@mui/material/Chip';
import Paper from '@mui/material/Paper';
import { darkTheme } from '@/theme/theme';

/**
 * #3047 — dark-mode contrast on the surfaces the dark theme actually paints.
 *
 * `paletteContrast.test.ts` pins the role colours against `background.default` / `background.paper`.
 * What it cannot see is the surface MUI paints *above* those in dark mode: an elevated Paper gets a
 * white overlay that grows with the elevation (Menu 8, Drawer 16, Dialog 24). jsdom computes no
 * contrast, and the nightly axe pass reports MUI Buttons as `incomplete`, so the dialog's text
 * buttons and links went unmeasured — and measured 4.19:1 (`primary.main` on the Dialog paper).
 *
 * The surfaces here are read from a *rendered* Paper (its `background-image` overlay composited over
 * its `background-color`), not re-derived from the formula, so the test follows whatever the theme
 * and MUI really emit. Alpha is composited before measuring: `getContrastRatio` ignores it.
 */

const AA_NORMAL_TEXT = 4.5;

function channels(color: string): [number, number, number, number] {
  const short = color.match(/^#([0-9a-f]{3})$/i);
  const hex = short ? `#${[...short[1]].map((d) => d + d).join('')}` : color;
  const long = hex.match(/^#([0-9a-f]{6})$/i);
  if (long) {
    const n = parseInt(long[1], 16);
    return [(n >> 16) & 255, (n >> 8) & 255, n & 255, 1];
  }
  const fn = color.match(/rgba?\(([^)]+)\)/);
  if (!fn) throw new Error(`unsupported colour ${color}`);
  const [r, g, b, a = '1'] = fn[1].split(',').map((part) => part.trim());
  return [Number(r), Number(g), Number(b), Number(a)];
}

/** `foreground` painted over the opaque `surface`. */
function over(foreground: string, surface: string): string {
  const [fr, fg, fb, fa] = channels(foreground);
  const [sr, sg, sb, sa] = channels(surface);
  if (sa !== 1) throw new Error(`surface ${surface} is not opaque`);
  const mix = (f: number, s: number) => Math.round(f * fa + s * (1 - fa));
  return `rgb(${mix(fr, sr)}, ${mix(fg, sg)}, ${mix(fb, sb)})`;
}

function ratio(foreground: string, surface: string): number {
  return getContrastRatio(over(foreground, surface), surface);
}

/** The colour a dark Paper of `elevation` paints: background plus its overlay gradient, if any. */
function paintedPaper(elevation: number): string {
  const { getByTestId } = render(
    <ThemeProvider theme={darkTheme}>
      <Paper elevation={elevation} data-testid="surface">
        x
      </Paper>
    </ThemeProvider>,
  );
  const el = getByTestId('surface');
  const style = getComputedStyle(el);
  const image = style.backgroundImage.includes('var(--Paper-overlay)')
    ? style.getPropertyValue('--Paper-overlay')
    : style.backgroundImage;
  cleanup();
  const tint = image.match(/rgba?\([^)]+\)/);
  return tint ? over(tint[0], style.backgroundColor) : over(style.backgroundColor, '#000000');
}

const { palette } = darkTheme;
const ROLES = ['primary', 'secondary', 'error', 'warning', 'info', 'success'] as const;

describe('dark theme: text and role labels on elevated surfaces (#3047)', () => {
  afterEach(() => cleanup());

  describe.each([
    ['card / page paper', 0],
    ['app bar', 4],
    ['menu / popover', 8],
    ['temporary drawer', 16],
    ['dialog', 24],
  ])('%s (elevation %i)', (_name, elevation) => {
    it('carries primary and secondary text at AA', () => {
      const surface = paintedPaper(elevation);
      expect(ratio(palette.text.primary, surface)).toBeGreaterThanOrEqual(AA_NORMAL_TEXT);
      expect(ratio(palette.text.secondary, surface)).toBeGreaterThanOrEqual(AA_NORMAL_TEXT);
    });

    it.each(ROLES)('keeps %s.main legible as a label (text button, link, outlined chip)', (role) => {
      const surface = paintedPaper(elevation);
      expect(ratio(palette[role].main, surface)).toBeGreaterThanOrEqual(AA_NORMAL_TEXT);
    });
  });

  it('reads a lighter surface for a higher elevation, so the measurement is not of one flat colour', () => {
    const flat = channels(paintedPaper(0))[0];
    const dialog = channels(paintedPaper(24))[0];
    expect(dialog).toBeGreaterThan(flat);
  });

  it.each(['success', 'info', 'warning', 'error'] as const)(
    'paints the standard and outlined %s Alert legibly',
    (severity) => {
      const { getByTestId } = render(
        <ThemeProvider theme={darkTheme}>
          <Paper>
            <Alert severity={severity} data-testid="standard">
              x
            </Alert>
            <Alert severity={severity} variant="outlined" data-testid="outlined">
              x
            </Alert>
          </Paper>
        </ThemeProvider>,
      );
      const standard = getComputedStyle(getByTestId('standard'));
      expect(ratio(standard.color, standard.backgroundColor)).toBeGreaterThanOrEqual(AA_NORMAL_TEXT);
      // The outlined Alert is transparent: its label sits on the paper behind it.
      const outlined = getComputedStyle(getByTestId('outlined'));
      expect(ratio(outlined.color, palette.background.paper)).toBeGreaterThanOrEqual(AA_NORMAL_TEXT);
    },
  );

  it('paints the default filled Chip label legibly on paper', () => {
    const { getByTestId } = render(
      <ThemeProvider theme={darkTheme}>
        <Chip label="x" data-testid="chip" />
      </ThemeProvider>,
    );
    const chip = getComputedStyle(getByTestId('chip'));
    const surface = over(chip.backgroundColor, palette.background.paper);
    expect(ratio(chip.color, surface)).toBeGreaterThanOrEqual(AA_NORMAL_TEXT);
  });
});
