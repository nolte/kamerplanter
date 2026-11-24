/**
 * Card grids shared by the settings groups.
 *
 * They switch on the width of the group panel, not of the viewport (F-11): next
 * to the app drawer and the 260 px settings navigation, a 1000 px wide window
 * leaves the panel only about 400 px, which a viewport breakpoint would still
 * split into two or three columns. The panel declares itself the query
 * container ({@link SETTINGS_PANEL_CONTAINER}).
 */
export const SETTINGS_PANEL_CONTAINER = {
  containerType: 'inline-size',
  containerName: 'settings-panel',
} as const;

/*
 * Every track is `minmax(0, 1fr)`, never a bare `1fr`: a bare `1fr` cannot shrink
 * below its content's min-content width, so a long German word or a row of
 * buttons pushed the card past the panel, where the card's `overflow: hidden`
 * clipped it (tablet, 820 px: the panel is ~250 px wide next to the app drawer
 * and the settings navigation).
 */

/** Two columns once the panel is at least 720 px wide. */
export const GRID_2COL = {
  display: 'grid',
  gridTemplateColumns: 'minmax(0, 1fr)',
  gap: 2,
  '@container settings-panel (min-width: 720px)': { gridTemplateColumns: 'repeat(2, minmax(0, 1fr))' },
} as const;

/** Two columns from 560 px, three from 960 px panel width. */
export const GRID_3COL = {
  display: 'grid',
  gridTemplateColumns: 'minmax(0, 1fr)',
  gap: 2,
  '@container settings-panel (min-width: 560px)': { gridTemplateColumns: 'repeat(2, minmax(0, 1fr))' },
  '@container settings-panel (min-width: 960px)': { gridTemplateColumns: 'repeat(3, minmax(0, 1fr))' },
} as const;

/** A card in {@link GRID_3COL} that spans two columns once there are three. */
export const GRID_3COL_WIDE_ITEM = {
  gridColumn: '1 / -1',
  '@container settings-panel (min-width: 960px)': { gridColumn: '1 / 3' },
} as const;

/** Panel width below which a horizontal three-way toggle no longer fits (the grids' one-column range). */
const TOGGLE_STACK_BELOW = '559.98px';

/**
 * A horizontal, full-width `ToggleButtonGroup` that stacks its buttons once the
 * panel is narrower than {@link TOGGLE_STACK_BELOW}.
 *
 * Switched on the panel's width like the grids, not on the viewport: at tablet
 * width the viewport is "desktop" while the panel next to two navigations is
 * only ~250 px, and three side-by-side buttons there ran out of the card, which
 * clipped the last one out of reach. The group keeps `orientation="horizontal"`
 * (a prop cannot follow a container query), so the stacked state undoes the
 * horizontal joins MUI draws and draws the vertical ones instead.
 */
export const TOGGLE_GROUP_STACK_WHEN_NARROW = {
  [`@container settings-panel (max-width: ${TOGGLE_STACK_BELOW})`]: {
    flexDirection: 'column',
    '& .MuiToggleButtonGroup-grouped': {
      marginLeft: 0,
      borderLeft: 1,
      borderLeftColor: 'divider',
    },
    '& .MuiToggleButtonGroup-grouped.Mui-selected + .MuiToggleButtonGroup-grouped.Mui-selected': {
      borderTop: 0,
      marginTop: 0,
    },
    // The buttons are the group's direct children, so `inherit` is the group's own radius.
    '& .MuiToggleButtonGroup-firstButton, & .MuiToggleButtonGroup-middleButton': {
      borderTopRightRadius: 'inherit',
      borderBottomLeftRadius: 0,
      borderBottomRightRadius: 0,
    },
    '& .MuiToggleButtonGroup-lastButton, & .MuiToggleButtonGroup-middleButton': {
      marginTop: '-1px',
      borderTop: '1px solid transparent',
      borderTopLeftRadius: 0,
      borderTopRightRadius: 0,
    },
    '& .MuiToggleButtonGroup-lastButton': {
      borderBottomLeftRadius: 'inherit',
    },
    '& .MuiToggleButtonGroup-middleButton': {
      borderTopRightRadius: 0,
    },
  },
} as const;
