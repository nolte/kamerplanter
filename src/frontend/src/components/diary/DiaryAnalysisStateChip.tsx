import type { ReactElement } from 'react';
import { useTranslation } from 'react-i18next';
import Chip from '@mui/material/Chip';
import Tooltip from '@mui/material/Tooltip';
import HourglassEmptyIcon from '@mui/icons-material/HourglassEmpty';
import AutoAwesomeIcon from '@mui/icons-material/AutoAwesome';
import CheckCircleIcon from '@mui/icons-material/CheckCircle';
import ErrorOutlineIcon from '@mui/icons-material/ErrorOutlined';
import RadioButtonUncheckedIcon from '@mui/icons-material/RadioButtonUnchecked';
import type { DiaryAnalysisState } from '@/api/types';

interface DiaryAnalysisStateChipProps {
  state: DiaryAnalysisState;
  /** `analysis_claimed_at`, shown as context while an agent holds the entry. */
  claimedAt?: string | null;
  size?: 'small' | 'medium';
}

/**
 * REQ-050 §2.5.2 — the analysis state as a single, legible badge.
 *
 * Shared by the plant diary tab and the tenant-wide overview so the five states
 * cannot come to look different in the two places a user meets them (AK-16).
 *
 * **Deliberately not a progress indicator.** `requested` means "waiting for an
 * analysis" and nothing more: the analysing agent runs outside this system, so
 * there is no completion estimate to show and a bar would assert one that does
 * not exist (AK-27, AK-29, §3). The same reason rules out a spinner for
 * `in_progress` — the claim timestamp is a fact, a spinning circle would imply
 * the server is watching the work.
 */
export default function DiaryAnalysisStateChip({
  state,
  claimedAt,
  size = 'small',
}: DiaryAnalysisStateChipProps) {
  const { t } = useTranslation();

  const label = t(`enums.diaryAnalysisState.${state}`);
  const description = t(`pages.plantDiary.analysis.stateHint.${state}`);

  const visuals: Record<
    DiaryAnalysisState,
    {
      color: 'default' | 'info' | 'success' | 'error';
      variant: 'filled' | 'outlined';
      icon: ReactElement;
    }
  > = {
    none: { color: 'default', variant: 'outlined', icon: <RadioButtonUncheckedIcon /> },
    requested: { color: 'info', variant: 'outlined', icon: <HourglassEmptyIcon /> },
    in_progress: { color: 'info', variant: 'filled', icon: <AutoAwesomeIcon /> },
    // `completed` is the one state the user is actively looking for, so it is
    // the only filled success chip (§2.5.2 "deutlich hervorgehoben").
    completed: { color: 'success', variant: 'filled', icon: <CheckCircleIcon /> },
    failed: { color: 'error', variant: 'outlined', icon: <ErrorOutlineIcon /> },
  };

  const { color, variant, icon } = visuals[state];

  return (
    <Tooltip title={description}>
      <Chip
        icon={icon}
        label={label}
        color={color}
        variant={variant}
        size={size}
        /* The tooltip is pointer-only; screen readers get the same sentence. */
        aria-label={`${label} – ${description}`}
        data-testid="diary-analysis-state"
        data-state={state}
        data-claimed-at={claimedAt ?? undefined}
      />
    </Tooltip>
  );
}
