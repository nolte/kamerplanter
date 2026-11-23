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

/** Two columns once the panel is at least 720 px wide. */
export const GRID_2COL = {
  display: 'grid',
  gridTemplateColumns: '1fr',
  gap: 2,
  '@container settings-panel (min-width: 720px)': { gridTemplateColumns: '1fr 1fr' },
} as const;

/** Two columns from 560 px, three from 960 px panel width. */
export const GRID_3COL = {
  display: 'grid',
  gridTemplateColumns: '1fr',
  gap: 2,
  '@container settings-panel (min-width: 560px)': { gridTemplateColumns: '1fr 1fr' },
  '@container settings-panel (min-width: 960px)': { gridTemplateColumns: '1fr 1fr 1fr' },
} as const;

/** A card in {@link GRID_3COL} that spans two columns once there are three. */
export const GRID_3COL_WIDE_ITEM = {
  gridColumn: '1 / -1',
  '@container settings-panel (min-width: 960px)': { gridColumn: '1 / 3' },
} as const;
