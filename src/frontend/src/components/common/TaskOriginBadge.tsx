import { useTranslation } from 'react-i18next';
import Chip from '@mui/material/Chip';
import Tooltip from '@mui/material/Tooltip';
import SmartToyIcon from '@mui/icons-material/SmartToy';
import type { TaskOrigin } from '@/api/types';

interface TaskOriginBadgeProps {
  /** The task's origin. `'user'` (or undefined) renders nothing. */
  origin?: TaskOrigin | null;
  /** Optional test id override for E2E selectors. */
  testId?: string;
}

/**
 * REQ-006 FreeStyle machine-generated badge (#1082). Mirrors `OriginChip`'s
 * UI-NFR-018 pattern (leading icon, outlined variant, explanatory tooltip). The
 * chip is only rendered for machine origins (`system`/`pipeline`) so a normal
 * user-authored task's card and detail header stay unmarked — a machine origin is
 * the exception worth flagging, a user origin is the unremarkable default.
 *
 * The label distinguishes *which* producer class made it via
 * `enums.taskOrigin.*`, while the tooltip explains the general "created for you by
 * a pipeline" meaning so the badge is understandable without prior context.
 */
export default function TaskOriginBadge({ origin, testId }: TaskOriginBadgeProps) {
  const { t } = useTranslation();

  if (!origin || origin === 'user') {
    return null;
  }

  return (
    <Tooltip title={t('pages.tasks.machineGeneratedTooltip')} arrow>
      <Chip
        icon={<SmartToyIcon fontSize="small" />}
        label={t(`enums.taskOrigin.${origin}`)}
        color="secondary"
        size="small"
        variant="outlined"
        data-testid={testId ?? `task-origin-badge-${origin}`}
      />
    </Tooltip>
  );
}
