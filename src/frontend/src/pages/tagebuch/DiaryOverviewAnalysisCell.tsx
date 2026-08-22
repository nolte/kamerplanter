import { useTranslation } from 'react-i18next';
import Box from '@mui/material/Box';
import Button from '@mui/material/Button';
import Typography from '@mui/material/Typography';
import { alpha } from '@mui/material/styles';
import AutoAwesomeIcon from '@mui/icons-material/AutoAwesome';
import ReplayIcon from '@mui/icons-material/Replay';
import DiaryAnalysisStateChip from '@/components/diary/DiaryAnalysisStateChip';
import { formatDateTime } from '@/utils/formatting';
import type { DiaryOverviewItem } from '@/api/types';

interface DiaryOverviewAnalysisCellProps {
  row: DiaryOverviewItem;
  /** A marking request for this row is in flight — disables the control. */
  busy?: boolean;
  /** Mark for analysis; also used to re-request after `completed`/`failed`. */
  onRequestAnalysis: (row: DiaryOverviewItem) => void;
}

/**
 * REQ-051 §6.2 — the analysis column, the core of the overview.
 *
 * It distinguishes **all five** states visibly, not "result yes/no" (AK-16):
 * the badge carries colour, icon and wording per state, `completed` adds the
 * summary as a one-line preview inside a highlighted frame, and `failed` names
 * the reported cause and offers re-marking.
 *
 * **`in_progress` names the moment of claiming, and only that.** §2.5.2 asks
 * for "wird analysiert" *with* the time an agent took the entry; the server
 * sends it as `analysis_claimed_at` and suppresses it on a row whose lease has
 * run out (such a row reads as `requested` anyway). A missing value is not an
 * error — the sentence stands on its own. What must not grow here is a running
 * "since 14 minutes": the moment is a fact, an elapsed-time counter would be
 * the suggestion of progress that §3 and AK-27/AK-29 rule out.
 *
 * **No progress indicator for `requested`.** Not a bar, not a spinner, not a
 * shimmer that reads like one (AK-27, AK-29, §3): the analysing agent runs
 * outside this installation, so nothing here knows when — or whether — it will
 * run. "Waiting for analysis" is the honest statement; anything animated would
 * assert a duration the server cannot promise.
 *
 * **The control follows `can_request_analysis` from the row** (AK-19), which the
 * server evaluated from role, authorship, consent and operating mode. The rule
 * is not rebuilt here. It stays a display aid: a 403 on the marking call is the
 * binding answer, which is why the caller reports it in words instead of
 * treating a hidden button as the whole enforcement.
 */
export default function DiaryOverviewAnalysisCell({
  row,
  busy = false,
  onRequestAnalysis,
}: DiaryOverviewAnalysisCellProps) {
  const { t } = useTranslation();
  const state = row.analysis_state;
  const completed = state === 'completed';

  /** The state machine's leavable states (§2.2): `none`, `completed`, `failed`. */
  const canMarkNow = state === 'none' || completed || state === 'failed';
  const showControl = row.can_request_analysis && canMarkNow;

  return (
    <Box
      sx={{
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'flex-start',
        gap: 0.5,
        minWidth: 0,
        // "deutlich hervorgehoben" for the one state the user came here to find
        // — a tinted frame derived from the theme's success colour, never a
        // hard-coded hex (UI-NFR-006).
        ...(completed
          ? {
              borderLeft: 3,
              borderColor: 'success.main',
              bgcolor: (theme) => alpha(theme.palette.success.main, 0.08),
              borderRadius: 1,
              px: 1,
              py: 0.5,
            }
          : {}),
      }}
      data-testid="diary-analysis-cell"
      data-state={state}
      data-highlighted={completed ? 'true' : 'false'}
    >
      <DiaryAnalysisStateChip state={state} />

      {completed && row.analysis_summary && (
        <Typography
          variant="body2"
          noWrap
          // The full sentence on hover; the cell shows one line by design —
          // the complete result belongs to the entry's detail view (AK-18).
          title={row.analysis_summary}
          sx={{ maxWidth: { xs: 220, md: 320 }, fontWeight: 500 }}
          data-testid="diary-analysis-summary-preview"
        >
          {row.analysis_summary}
        </Typography>
      )}

      {completed && row.analyzed_at && (
        <Typography variant="caption" color="text.secondary">
          {t('pages.diaryOverview.analysis.analyzedAt', {
            time: formatDateTime(row.analyzed_at),
          })}
        </Typography>
      )}

      {state === 'requested' && (
        /* A sentence, deliberately static. See the component docstring. */
        <Typography
          variant="caption"
          color="text.secondary"
          data-testid="diary-analysis-waiting-hint"
        >
          {t('pages.diaryOverview.analysis.waitingHint')}
        </Typography>
      )}

      {state === 'in_progress' && (
        <Typography
          variant="caption"
          color="text.secondary"
          data-testid="diary-analysis-running-hint"
        >
          {t('pages.diaryOverview.analysis.runningHint')}
        </Typography>
      )}

      {state === 'in_progress' && row.analysis_claimed_at && (
        /* §2.5.2 wants the moment of claiming on this row — a fixed point in
           time, rendered exactly like `analyzed_at` above. Deliberately not
           "running for 14 minutes": an elapsed-time counter reads as progress,
           and nothing here knows how long the run takes (§3, AK-27/AK-29). */
        <Typography
          variant="caption"
          color="text.secondary"
          data-testid="diary-analysis-claimed-at"
        >
          {t('pages.diaryOverview.analysis.claimedAt', {
            time: formatDateTime(row.analysis_claimed_at),
          })}
        </Typography>
      )}

      {state === 'failed' && (
        <Typography
          variant="caption"
          color="error.main"
          sx={{ maxWidth: { xs: 220, md: 320 } }}
          data-testid="diary-analysis-error-preview"
        >
          {row.analysis_error || t('pages.plantDiary.analysis.failedUnknown')}
        </Typography>
      )}

      {showControl && (
        <Button
          size="small"
          variant="outlined"
          startIcon={completed || state === 'failed' ? <ReplayIcon /> : <AutoAwesomeIcon />}
          disabled={busy}
          onClick={(event) => {
            // The whole row is a click target that opens the entry; without this
            // the button would mark *and* open the detail in the same tap.
            event.stopPropagation();
            onRequestAnalysis(row);
          }}
          sx={{ minHeight: 36 }}
          data-testid="diary-request-analysis"
        >
          {state === 'none'
            ? t('pages.plantDiary.analysis.request')
            : t('pages.plantDiary.analysis.requestAgain')}
        </Button>
      )}
    </Box>
  );
}
