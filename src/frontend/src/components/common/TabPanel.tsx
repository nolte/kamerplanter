import Box from '@mui/material/Box';
import type { ReactNode } from 'react';

interface TabPanelProps {
  index: number;
  value: number;
  /** Namespace for the WAI-ARIA ids, e.g. "species" → "species-tabpanel-0". */
  idPrefix: string;
  children: ReactNode;
}

/**
 * Accessible tab panel wrapper (QW-1): wires the WAI-ARIA tabs pattern — each
 * panel exposes role="tabpanel", an id matched by the owning tab's
 * aria-controls, and aria-labelledby pointing back at that tab. Hidden panels
 * stay in the DOM but `hidden`, so the panel that is shown is always associated
 * with its tab for assistive tech. Children of hidden panels are unmounted so a
 * tab's data is only loaded while it is active.
 */
export function TabPanel({ index, value, idPrefix, children }: TabPanelProps) {
  const hidden = value !== index;
  return (
    <Box
      role="tabpanel"
      hidden={hidden}
      id={`${idPrefix}-tabpanel-${index}`}
      aria-labelledby={`${idPrefix}-tab-${index}`}
    >
      {!hidden && children}
    </Box>
  );
}

/** ARIA wiring props for a tab at a given index within a prefix namespace (QW-1). */
export function tabA11yProps(idPrefix: string, index: number) {
  return {
    id: `${idPrefix}-tab-${index}`,
    'aria-controls': `${idPrefix}-tabpanel-${index}`,
  };
}
