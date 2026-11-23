import { describe, it, expect } from 'vitest';
import { render } from '@testing-library/react';
import Box from '@mui/material/Box';
import { ThemeContextProvider } from '@/theme';
import {
  GRID_2COL,
  GRID_3COL,
  GRID_3COL_WIDE_ITEM,
  SETTINGS_PANEL_CONTAINER,
} from '@/pages/auth/settings/settingsLayout';

/**
 * F-11 follow-up — the settings card grids switch on the width of the group
 * panel, not of the viewport: next to the app drawer and the settings
 * navigation, a 900–1100 px window leaves the panel ~320–500 px, which a
 * viewport breakpoint would still split into columns.
 *
 * jsdom lays nothing out, so this pins what reaches the browser: the emitted CSS
 * carries container queries on the named panel and no viewport media query.
 */
function emittedCss(): string {
  return Array.from(document.querySelectorAll('style'))
    .map((el) => el.textContent ?? '')
    .join('\n');
}

describe('settings layout grids', () => {
  it('declare their columns as container queries on the settings panel', () => {
    render(
      <ThemeContextProvider>
        <Box sx={SETTINGS_PANEL_CONTAINER}>
          <Box sx={GRID_2COL} />
          <Box sx={GRID_3COL}>
            <Box sx={GRID_3COL_WIDE_ITEM} />
          </Box>
        </Box>
      </ThemeContextProvider>,
    );
    const css = emittedCss().replace(/\s+/g, ' ');
    expect(css).toMatch(/container-type: ?inline-size/);
    expect(css).toMatch(/container-name: ?settings-panel/);
    expect(css).toContain('@container settings-panel (min-width: 720px)');
    expect(css).toContain('@container settings-panel (min-width: 560px)');
    expect(css).toContain('@container settings-panel (min-width: 960px)');
  });

  it('use no viewport breakpoint', () => {
    for (const grid of [GRID_2COL, GRID_3COL, GRID_3COL_WIDE_ITEM]) {
      expect(JSON.stringify(grid)).not.toMatch(/"(xs|sm|md|lg|xl)"|@media/);
    }
  });
});
