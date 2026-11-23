/** Responsive card grids shared by the settings groups (unchanged from the former tabs). */
export const GRID_2COL = {
  display: 'grid',
  gridTemplateColumns: { xs: '1fr', md: '1fr 1fr' },
  gap: 2,
} as const;

export const GRID_3COL = {
  display: 'grid',
  gridTemplateColumns: { xs: '1fr', sm: '1fr 1fr', lg: '1fr 1fr 1fr' },
  gap: 2,
} as const;
