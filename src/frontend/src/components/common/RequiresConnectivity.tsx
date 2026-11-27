import { cloneElement, useId, type MouseEvent, type ReactElement } from 'react';
import { useTranslation } from 'react-i18next';
import Box from '@mui/material/Box';
import Tooltip from '@mui/material/Tooltip';
import type { SxProps, Theme } from '@mui/material/styles';
import { visuallyHidden } from '@mui/utils';

/** The props this wrapper sets on the action button it wraps. */
interface LockableButtonProps {
  onClick?: (event: MouseEvent<HTMLElement>) => void;
  sx?: SxProps<Theme>;
  'aria-disabled'?: boolean | 'true' | 'false';
  'aria-describedby'?: string;
}

export interface RequiresConnectivityProps {
  /** `true` while the browser is offline: the action is locked and says why. */
  offline: boolean;
  /** The action button. Do NOT add `!online` to its `disabled`: this wrapper locks it. */
  children: ReactElement<LockableButtonProps>;
}

/** Looks disabled without being `disabled` (which would drop it from the tab order and blur it). */
const LOCKED_SX = {
  color: 'action.disabled',
  bgcolor: 'action.disabledBackground',
  borderColor: 'action.disabledBackground',
  boxShadow: 'none',
  cursor: 'not-allowed',
  '&:hover': { bgcolor: 'action.disabledBackground', boxShadow: 'none' },
} as const;

function sxList(sx: SxProps<Theme> | undefined): ReadonlyArray<SxProps<Theme>> {
  if (sx === undefined) return [];
  return Array.isArray(sx) ? (sx as ReadonlyArray<SxProps<Theme>>) : [sx];
}

/**
 * UI-NFR-012 R-020a–R-020e (#3025 N-39) — an action the server has to validate (phase change, harvest,
 * actuator command) is locked offline and names the reason: "Netzwerkverbindung erforderlich".
 *
 * Accessibility: the button stays focusable and keeps its own accessible name. Offline it carries
 * `aria-disabled="true"`, a click guard (which also stops a form's implicit submit) and `aria-describedby`
 * pointing at the reason, so a screen reader hears the action, "not available" and the reason. The tooltip
 * describes the button (`describeChild`) instead of renaming it.
 *
 * The element structure is the same online and offline (wrapper, tooltip, button, reason element), so a change
 * of connectivity does not remount the button and a focused button keeps its focus.
 */
export default function RequiresConnectivity({ offline, children }: RequiresConnectivityProps) {
  const { t } = useTranslation();
  const reasonId = useId();
  const reason = t('common.pwa.requiresConnectivity');
  const own = children.props;

  const describedBy = offline
    ? [own['aria-describedby'], reasonId].filter(Boolean).join(' ')
    : own['aria-describedby'];

  const button = cloneElement(children, {
    'aria-disabled': offline ? true : own['aria-disabled'],
    'aria-describedby': describedBy,
    onClick: (event: MouseEvent<HTMLElement>) => {
      if (offline) {
        event.preventDefault();
        event.stopPropagation();
        return;
      }
      own.onClick?.(event);
    },
    // A flat list: the caller's sx entries (an object or an sx array) followed by the locked look.
    sx: offline ? ([...sxList(own.sx), LOCKED_SX] as SxProps<Theme>) : own.sx,
  });

  return (
    <Box
      component="span"
      sx={{ display: 'inline-flex' }}
      data-testid="requires-connectivity"
      data-offline={offline ? 'true' : 'false'}
    >
      <Tooltip title={offline ? reason : ''} describeChild>
        {button}
      </Tooltip>
      <Box component="span" id={reasonId} sx={visuallyHidden}>
        {offline ? reason : ''}
      </Box>
    </Box>
  );
}
