import type { Theme } from '@mui/material/styles';

/** A style rule of the theme's toolbar mixin: values, or media queries holding values. */
export type ToolbarRule = { readonly [key: string]: string | number | ToolbarRule };

function asLength(value: string | number): string {
  return typeof value === 'number' ? `${value}px` : value;
}

/**
 * Rewrites every `minHeight` of a toolbar rule into the styles `fromHeight` derives from it, media queries kept.
 * The theme's toolbar mixin is the rule the fixed app bar's `Toolbar` takes its height from (56 px, 48 px in
 * landscape, 64 px from `sm`), so whatever is derived here follows the bar at every breakpoint.
 */
export function fromToolbarHeight(
  rule: ToolbarRule,
  fromHeight: (height: string) => ToolbarRule,
): ToolbarRule {
  return Object.fromEntries(
    Object.entries(rule).flatMap(([key, value]) => {
      if (key === 'minHeight' && typeof value !== 'object') return Object.entries(fromHeight(asLength(value)));
      return [[key, typeof value === 'object' ? fromToolbarHeight(value, fromHeight) : value]];
    }),
  );
}

/**
 * Paper styles that start a full-height drawer below the fixed app bar (#3157).
 *
 * The app bar sits above every drawer (`zIndex: drawer + 1` in `MainLayout`, so it stays over the docked
 * sidebar). A drawer whose paper starts at the top of the viewport therefore lies with its header under the bar:
 * its title is hidden and a close button there cannot be hit with a pointer. The sidebar avoids this with a
 * toolbar-high spacer, the garden plan's bottom sheets by never growing that tall; a right-anchored drawer starts
 * below the bar instead, with its height reduced by the same amount so its bottom stays on screen.
 */
export const belowAppBar = (theme: Theme): ToolbarRule =>
  fromToolbarHeight(theme.mixins.toolbar as ToolbarRule, (height) => ({
    top: height,
    height: `calc(100% - ${height})`,
  }));
