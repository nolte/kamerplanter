import { describe, expect, it } from 'vitest';
import { createTheme, getContrastRatio } from '@mui/material/styles';
import { darkTheme, highContrastTheme, lightTheme } from '@/theme/theme';
import {
  METRIC_COLOR_KEYS,
  PHASE_COLOR_KEYS,
  PHASE_FALLBACK_PALETTE,
  getEventCategoryColor,
  getMetricColor,
  getPhaseColor,
  paintedOver,
  phaseColorKey,
  planPhaseColor,
  readableTextOn,
} from '@/theme/domainColors';

/**
 * #3021 — the domain colour tokens and their lookups. The lookups are what every view calls, so they are tested
 * through the resolved themes the app actually mounts (`lightTheme` / `darkTheme`), not through the literals.
 */

const AA_NORMAL_TEXT = 4.5;
const NON_TEXT_CONTRAST = 3;

describe('phase colour tokens', () => {
  it('carries every phase token in the light and the dark theme', () => {
    for (const key of PHASE_COLOR_KEYS) {
      expect(lightTheme.palette.phase[key]).toMatch(/^#[0-9A-F]{6}$/i);
      expect(darkTheme.palette.phase[key]).toMatch(/^#[0-9A-F]{6}$/i);
    }
  });

  it('keeps the light tokens in the high-contrast theme built on the light base', () => {
    expect(highContrastTheme.palette.phase.vegetative).toBe(lightTheme.palette.phase.vegetative);
  });

  it('resolves by phase key, case and separators aside', () => {
    expect(phaseColorKey('vegetative')).toBe('vegetative');
    expect(phaseColorKey('FLOWERING')).toBe('flowering');
    expect(phaseColorKey('short_day_induction')).toBe('short_day_induction');
    expect(phaseColorKey('Short Day-Induction')).toBe('short_day_induction');
  });

  it('maps species-specific and sowing phases onto the phase they share a colour with', () => {
    expect(phaseColorKey('fruiting')).toBe('ripening');
    expect(phaseColorKey('winter_dormancy')).toBe('dormancy');
    expect(phaseColorKey('growth')).toBe('vegetative');
    expect(phaseColorKey('leaf_phase')).toBe('vegetative');
  });

  it('does not resolve a translated name or an unknown key', () => {
    expect(phaseColorKey('Keimung')).toBeUndefined();
    expect(phaseColorKey('')).toBeUndefined();
    expect(phaseColorKey(null)).toBeUndefined();
  });

  it('paints a phase in the mode of the active theme', () => {
    expect(getPhaseColor(lightTheme, 'germination')).toBe('#81C784');
    expect(getPhaseColor(darkTheme, 'germination')).toBe('#A5D6A7');
    expect(getPhaseColor(darkTheme, 'fruiting')).toBe(darkTheme.palette.phase.ripening);
  });

  it('gives an unknown phase the neutral grey, or a stable distinct colour on request', () => {
    expect(getPhaseColor(lightTheme, 'mystery')).toBe(lightTheme.palette.grey[500]);
    expect(getPhaseColor(darkTheme, 'mystery')).toBe(darkTheme.palette.grey[600]);
    const distinct = getPhaseColor(lightTheme, 'mystery', { unknown: 'distinct' });
    expect(PHASE_FALLBACK_PALETTE).toContain(distinct);
    expect(getPhaseColor(lightTheme, 'mystery', { unknown: 'distinct' })).toBe(distinct);
  });

  it('falls back to the static tokens for a theme built without them', () => {
    const bare = createTheme({ palette: { mode: 'dark' } });
    expect(getPhaseColor(bare, 'germination')).toBe('#A5D6A7');
    expect(getMetricColor(bare, 'ph')).toBe(darkTheme.palette.metric.ph);
    expect(getEventCategoryColor(bare, 'ipm')).toBe(darkTheme.palette.eventCategory.ipm);
  });

  it('keeps every dark phase token at 3:1 against the dark surfaces (WCAG 1.4.11)', () => {
    for (const key of PHASE_COLOR_KEYS) {
      const color = darkTheme.palette.phase[key];
      expect(getContrastRatio(color, darkTheme.palette.background.paper), key).toBeGreaterThanOrEqual(NON_TEXT_CONTRAST);
      expect(getContrastRatio(color, darkTheme.palette.background.default), key).toBeGreaterThanOrEqual(
        NON_TEXT_CONTRAST,
      );
    }
  });
});

describe('garden-plan phase colour', () => {
  it('uses the light tokens of the ten plan phases, mode-independent', () => {
    expect(planPhaseColor('vegetative')).toBe(lightTheme.palette.phase.vegetative);
    expect(planPhaseColor(' Flowering ')).toBe('#AB47BC');
  });

  it('does not apply aliases or the extra phases — the cross-language vectors hash them', () => {
    expect(PHASE_FALLBACK_PALETTE).toContain(planPhaseColor('dormancy'));
    expect(planPhaseColor('dormancy')).toBe('#FFA726');
    expect(PHASE_FALLBACK_PALETTE).toContain(planPhaseColor('fruiting'));
  });
});

describe('metric colour tokens', () => {
  it('carries every metric token in both modes and resolves by metric key', () => {
    for (const key of METRIC_COLOR_KEYS) {
      expect(getMetricColor(lightTheme, key)).toBe(lightTheme.palette.metric[key]);
      expect(getMetricColor(darkTheme, key)).toBe(darkTheme.palette.metric[key]);
    }
    expect(getMetricColor(lightTheme, 'ph')).toBe('#4caf50');
    expect(getMetricColor(darkTheme, 'ph')).not.toBe('#4caf50');
  });

  it('gives an unknown metric the `other` token, never an inherited property', () => {
    expect(getMetricColor(lightTheme, 'unknown_metric')).toBe(lightTheme.palette.metric.other);
    expect(getMetricColor(lightTheme, 'toString')).toBe(lightTheme.palette.metric.other);
    expect(getMetricColor(lightTheme, undefined)).toBe(lightTheme.palette.metric.other);
  });

  it('keeps every dark metric line at 3:1 against the dark paper', () => {
    for (const key of METRIC_COLOR_KEYS) {
      expect(getContrastRatio(darkTheme.palette.metric[key], darkTheme.palette.background.paper), key)
        .toBeGreaterThanOrEqual(NON_TEXT_CONTRAST);
    }
  });
});

describe('calendar category colour tokens', () => {
  it('resolves by category key in the mode of the theme', () => {
    expect(getEventCategoryColor(lightTheme, 'feeding')).toBe('#2196F3');
    expect(getEventCategoryColor(darkTheme, 'feeding')).toBe(darkTheme.palette.eventCategory.feeding);
  });

  it('gives an unknown category the theme grey', () => {
    expect(getEventCategoryColor(lightTheme, 'nope')).toBe(lightTheme.palette.grey[500]);
    expect(getEventCategoryColor(lightTheme, 'constructor')).toBe(lightTheme.palette.grey[500]);
  });

  it('lets a chip label reach AA on every category colour in both modes', () => {
    for (const theme of [lightTheme, darkTheme]) {
      for (const [key, color] of Object.entries(theme.palette.eventCategory)) {
        expect(getContrastRatio(readableTextOn(color), color), `${theme.palette.mode} ${key}`).toBeGreaterThanOrEqual(
          AA_NORMAL_TEXT,
        );
      }
    }
  });
});

describe('readableTextOn', () => {
  it('picks white on dark and black on light colours', () => {
    expect(readableTextOn('#1b5e20')).toBe('#ffffff');
    expect(readableTextOn('#FDD835')).toBe('#000000');
    // White on #F44336 is 3.68:1 — the old calendar chip label; black reaches AA.
    expect(readableTextOn('#F44336')).toBe('#000000');
  });

  it('measures the composited surface of a translucent fill', () => {
    const painted = paintedOver('#2E7D32', 0.45, '#ffffff');
    expect(painted).toBe('rgb(161, 197, 163)');
    expect(readableTextOn('#2E7D32', 0.45, '#ffffff')).toBe('#000000');
    expect(readableTextOn('#2E7D32')).toBe('#ffffff');
  });

  it('reaches AA on every phase fill the fertiliser Gantt paints', () => {
    for (const theme of [lightTheme, darkTheme]) {
      const paper = theme.palette.background.paper;
      for (const key of PHASE_COLOR_KEYS) {
        for (const opacity of [0.45, 0.85]) {
          const surface = paintedOver(theme.palette.phase[key], opacity, paper);
          const text = readableTextOn(theme.palette.phase[key], opacity, paper);
          expect(getContrastRatio(text, surface), `${theme.palette.mode} ${key} @${opacity}`).toBeGreaterThanOrEqual(
            AA_NORMAL_TEXT,
          );
        }
      }
    }
  });

  it('falls back to black for a colour it cannot parse', () => {
    expect(readableTextOn('var(--x)')).toBe('#000000');
  });
});
