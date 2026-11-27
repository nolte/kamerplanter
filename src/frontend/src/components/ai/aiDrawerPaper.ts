import { useContext } from 'react';
import type { SxProps, Theme } from '@mui/material/styles';
import { belowAppBar } from '@/components/layout/appBarOffset';
import { KioskContext } from '@/kiosk/KioskProvider';

/**
 * Paper styles of a right-anchored KI drawer (#3162): full width on a phone, `width` from `sm`.
 *
 * In the standard shell the app bar lies above every drawer (`zIndex: drawer + 1` in `MainLayout`), so the paper
 * starts below it — from the top of the viewport the drawer's title and close button sat under the bar. The kiosk
 * shell's bar keeps MUI's `appBar` stack level, below the drawer's: there the drawer covers the bar, its header is
 * visible from the top, and an offset would only leave a dimmed strip of an unreachable bar.
 *
 * An array, not a spread: the offset's media queries carry the same keys as the responsive width's, and one object
 * would let them replace the width instead of joining it (#3161).
 */
export function aiDrawerPaperSx(width: number, belowBar: boolean): SxProps<Theme> {
  const size = { width: { xs: '100%', sm: width }, maxWidth: '100vw' };
  return (belowBar ? [size, belowAppBar] : [size]) as SxProps<Theme>;
}

/** Whether a KI drawer has to start below a bar stacked above it: the standard shell's, not the kiosk's. */
export function useAiDrawerBelowBar(): boolean {
  // Optional read: a drawer rendered without a KioskProvider (tests, standalone use) is in the standard shell.
  return !(useContext(KioskContext)?.isKiosk ?? false);
}
