/**
 * The polite live region of the editor (REQ-053 GP-NFR-022/070): one visually hidden element
 * that is always in the DOM (a region inserted together with its text is not announced) and says
 * the result of an action once the burst of actions has settled - holding an arrow key moves a
 * bed many steps but is announced once, at the position it stops at.
 */
import { useEffect, useState } from 'react';
import Box from '@mui/material/Box';
import { visuallyHidden } from '@mui/utils';

/** Long enough to swallow key repeat (about 30 ms), short enough to feel immediate. */
export const SETTLE_MS = 350;

interface LiveRegionProps {
  /** The latest result; changes while it is still being produced are collapsed. */
  message: string;
  settleMs?: number;
}

export function LiveRegion({ message, settleMs = SETTLE_MS }: LiveRegionProps) {
  const [spoken, setSpoken] = useState('');
  useEffect(() => {
    const timer = setTimeout(() => setSpoken(message), message === '' ? 0 : settleMs);
    return () => clearTimeout(timer);
  }, [message, settleMs]);
  return (
    <Box
      role="status"
      aria-live="polite"
      aria-atomic="true"
      sx={visuallyHidden}
      data-testid="garden-plan-live-region"
    >
      {spoken}
    </Box>
  );
}
