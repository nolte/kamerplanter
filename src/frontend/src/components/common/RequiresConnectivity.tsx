import type { ReactElement } from 'react';
import { useTranslation } from 'react-i18next';
import Box from '@mui/material/Box';
import Tooltip from '@mui/material/Tooltip';

export interface RequiresConnectivityProps {
  /** `true` while the browser is offline; the action inside is then disabled by its owner. */
  offline: boolean;
  /** The action button. Its owner adds `!online` to its `disabled`. */
  children: ReactElement;
}

/**
 * UI-NFR-012 R-020a–R-020e (#3025 N-39) — the hint on an action that the server has to validate and that is
 * therefore locked offline (phase change, harvest, treatment, actuator command).
 *
 * The owner disables the button; this wrapper names the reason: the tooltip "Netzwerkverbindung erforderlich".
 * A disabled button fires no pointer or focus events, so the tooltip hangs on a wrapping element that stays
 * focusable (`tabIndex=0`) for keyboard users; the tooltip also names that element for assistive tech. Online, the button renders unwrapped and keeps its layout.
 */
export default function RequiresConnectivity({ offline, children }: RequiresConnectivityProps) {
  const { t } = useTranslation();
  if (!offline) return children;
  return (
    <Tooltip title={t('common.pwa.requiresConnectivity')}>
      <Box
        component="span"
        tabIndex={0}
        data-testid="requires-connectivity"
        sx={{ display: 'inline-flex' }}
      >
        {children}
      </Box>
    </Tooltip>
  );
}
