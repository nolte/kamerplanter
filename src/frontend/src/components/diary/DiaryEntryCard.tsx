import { useMemo } from 'react';
import { useTranslation } from 'react-i18next';
import Alert from '@mui/material/Alert';
import AlertTitle from '@mui/material/AlertTitle';
import Box from '@mui/material/Box';
import Button from '@mui/material/Button';
import Card from '@mui/material/Card';
import CardContent from '@mui/material/CardContent';
import Chip from '@mui/material/Chip';
import CircularProgress from '@mui/material/CircularProgress';
import IconButton from '@mui/material/IconButton';
import Tooltip from '@mui/material/Tooltip';
import Typography from '@mui/material/Typography';
import AutoAwesomeIcon from '@mui/icons-material/AutoAwesome';
import DeleteIcon from '@mui/icons-material/Delete';
import EditIcon from '@mui/icons-material/Edit';
import UndoIcon from '@mui/icons-material/Undo';
import ReplayIcon from '@mui/icons-material/Replay';
import { formatDateTime } from '@/utils/formatting';
import type { PlantDiaryEntry } from '@/api/types';
import DiaryAnalysisResult from './DiaryAnalysisResult';
import DiaryAnalysisStateChip from './DiaryAnalysisStateChip';
import DiaryEnvironmentReadings from './DiaryEnvironmentReadings';
import DiaryPhotoStrip from './DiaryPhotoStrip';

interface DiaryEntryCardProps {
  entry: PlantDiaryEntry;
  /**
   * The server's §7.2 verdict on whether this user may mark this entry
   * (`can_request_analysis`). **Not computed here.** Whether marking is allowed
   * depends on role, authorship, consent and operating mode; REQ-050 §2.5.2 is
   * explicit that rebuilding that in the client means maintaining it twice.
   *
   * `undefined` means "no verdict available" — the control is then offered and
   * the server's 403 decides, which is safe because the marking endpoint
   * re-evaluates the rule unconditionally (AK-18a).
   */
  canRequestAnalysis?: boolean;
  /** Whether editing/deleting is offered at all (write role, plant not removed). */
  canWrite?: boolean;
  onEdit?: (entry: PlantDiaryEntry) => void;
  onDelete?: (entry: PlantDiaryEntry) => void;
  /** Mark for analysis — also used to re-request after `completed`/`failed`. */
  onRequestAnalysis?: (entry: PlantDiaryEntry) => void;
  /** Withdraw the marking; only meaningful while the state is `requested`. */
  onCancelAnalysis?: (entry: PlantDiaryEntry) => void;
  /** A request for this entry is in flight — disables both analysis controls. */
  analysisBusy?: boolean;
}

/**
 * REQ-050 §2.5.1 / §2.5.3 — one diary entry with its analysis state and result.
 *
 * Shared between the plant's diary tab and the tenant-wide overview's detail
 * view, so an entry looks the same wherever a user opens it.
 *
 * The component is presentational: it renders the state it is given and calls
 * back. It never decides *whether* a user may mark an entry — see
 * {@link DiaryEntryCardProps.canRequestAnalysis}.
 *
 * **`entry.analysis_state` is the displayed state, full stop.** There is no
 * `displayState` override prop: every endpoint that answers with an entry — the
 * plant listing, the single read, both marking calls — projects the state
 * through `effective_analysis_state()`, so an entry whose agent lease ran out
 * already reads as `requested` here (`api/v1/planting_runs/diary_schemas.py:185`).
 * An override existed while the single read still returned the raw stored state;
 * keeping it now would only offer callers a way to display a state the entry
 * contradicts.
 */
export default function DiaryEntryCard({
  entry,
  canRequestAnalysis,
  canWrite = false,
  onEdit,
  onDelete,
  onRequestAnalysis,
  onCancelAnalysis,
  analysisBusy = false,
}: DiaryEntryCardProps) {
  const { t } = useTranslation();

  const state = entry.analysis_state;
  // `undefined` = the verdict could not be fetched; offer the control and let
  // the server answer. `false` = the server said no — hide it (AK-19).
  const mayMark = canRequestAnalysis !== false;

  const measurements = useMemo(
    () => Object.entries(entry.measurements ?? {}),
    [entry.measurements],
  );

  // REQ-013 §2.3a — read defensively: an entry stored before the field existed
  // carries no `environment` at all, and this component is also fed by fixtures
  // and by the overview's detail view.
  const environment = useMemo(() => entry.environment ?? [], [entry.environment]);

  const title = entry.title ?? t(`enums.diaryEntryType.${entry.entry_type}`);

  return (
    <Card variant="outlined" sx={{ mb: 2 }} data-testid="diary-entry-card" data-entry-key={entry.key}>
      <CardContent>
        {/* Header: type, timestamp, state badge, write actions. */}
        <Box
          sx={{
            display: 'flex',
            flexWrap: 'wrap',
            alignItems: 'flex-start',
            justifyContent: 'space-between',
            gap: 1,
            mb: 1,
          }}
        >
          <Box sx={{ minWidth: 0 }}>
            <Box sx={{ display: 'flex', flexWrap: 'wrap', alignItems: 'center', gap: 1 }}>
              <Chip
                size="small"
                label={t(`enums.diaryEntryType.${entry.entry_type}`)}
                data-testid="diary-entry-type"
              />
              <DiaryAnalysisStateChip state={state} claimedAt={entry.analysis_claimed_at} />
            </Box>
            <Typography
              component="h3"
              variant="subtitle1"
              sx={{ fontWeight: 600, mt: 0.5 }}
              data-testid="diary-entry-title"
            >
              {title}
            </Typography>
            <Typography variant="caption" color="text.secondary">
              {formatDateTime(entry.created_at)}
            </Typography>
          </Box>

          {canWrite && (
            <Box sx={{ display: 'flex', gap: 0.5, flexShrink: 0 }}>
              <Tooltip title={t('pages.plantDiary.editEntry')}>
                <span>
                  <IconButton
                    onClick={() => onEdit?.(entry)}
                    aria-label={t('pages.plantDiary.editEntry')}
                    sx={{ minWidth: 44, minHeight: 44 }}
                    data-testid="diary-entry-edit"
                  >
                    <EditIcon />
                  </IconButton>
                </span>
              </Tooltip>
              <Tooltip title={t('pages.plantDiary.deleteEntry')}>
                <span>
                  <IconButton
                    onClick={() => onDelete?.(entry)}
                    aria-label={t('pages.plantDiary.deleteEntry')}
                    sx={{ minWidth: 44, minHeight: 44 }}
                    data-testid="diary-entry-delete"
                  >
                    <DeleteIcon />
                  </IconButton>
                </span>
              </Tooltip>
            </Box>
          )}
        </Box>

        {/* Free text — preserve the user's own line breaks. */}
        <Typography
          variant="body2"
          sx={{ whiteSpace: 'pre-wrap' }}
          data-testid="diary-entry-text"
        >
          {entry.text}
        </Typography>

        {entry.tags.length > 0 && (
          <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5, mt: 1 }} data-testid="diary-entry-tags">
            {entry.tags.map((tag) => (
              <Chip key={tag} size="small" variant="outlined" label={tag} />
            ))}
          </Box>
        )}

        {measurements.length > 0 && (
          <Box sx={{ mt: 1 }} data-testid="diary-entry-measurements">
            <Typography variant="caption" color="text.secondary" sx={{ display: 'block' }}>
              {t('pages.plantDiary.measurements')}
            </Typography>
            <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5, mt: 0.5 }}>
              {measurements.map(([name, value]) => (
                <Chip
                  key={name}
                  size="small"
                  variant="outlined"
                  label={`${name}: ${String(value)}`}
                />
              ))}
            </Box>
          </Box>
        )}

        {/* ── Environment snapshot (REQ-013 §2.3a) ─────────────────── */}
        {/* Its own block, below the grower's measurements and visibly labelled
            as automatic. Rendering the two in one list would tell the reader
            that a machine and a human said the same kind of thing, which is
            precisely the confusion the two separate fields prevent. */}
        {environment.length > 0 && (
          <Box sx={{ mt: 1 }} data-testid="diary-entry-environment">
            <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mb: 0.5 }}>
              {t('pages.plantDiary.environment.entryTitle')}
            </Typography>
            <DiaryEnvironmentReadings readings={environment} testIdPrefix="diary-entry-environment" />
            {entry.environment_status === 'unavailable' && (
              <Typography
                variant="caption"
                color="text.secondary"
                sx={{ display: 'block', mt: 0.5 }}
                data-testid="diary-entry-environment-partial"
              >
                {t('pages.plantDiary.environment.partial')}
              </Typography>
            )}
          </Box>
        )}

        <DiaryPhotoStrip photoRefs={entry.photo_refs} />

        {/* ── Analysis ─────────────────────────────────────────────── */}
        <Box sx={{ mt: 2 }}>
          {state === 'requested' && (
            /* AK-27: "waiting", stated as a fact and nothing more. There is no
               progress bar here on purpose — the analysing agent runs outside
               this system, so nobody can promise when it will be done. */
            <Alert severity="info" icon={false} sx={{ mb: 1 }} data-testid="diary-analysis-waiting">
              {t('pages.plantDiary.analysis.waiting')}
            </Alert>
          )}

          {state === 'in_progress' && (
            <Alert severity="info" icon={false} sx={{ mb: 1 }} data-testid="diary-analysis-running">
              {entry.analysis_claimed_at
                ? t('pages.plantDiary.analysis.runningSince', {
                    time: formatDateTime(entry.analysis_claimed_at),
                  })
                : t('pages.plantDiary.analysis.running')}
            </Alert>
          )}

          {state === 'failed' && (
            <Alert severity="warning" sx={{ mb: 1 }} data-testid="diary-analysis-failed">
              <AlertTitle>{t('pages.plantDiary.analysis.failedTitle')}</AlertTitle>
              {entry.analysis_error || t('pages.plantDiary.analysis.failedUnknown')}
            </Alert>
          )}

          {state === 'completed' && entry.analysis && (
            <DiaryAnalysisResult analysis={entry.analysis} photoRefs={entry.photo_refs} />
          )}

          {/* The switch. Shown only when the server says this user may mark
              (AK-19) and only in a state the machine allows to leave. */}
          {mayMark && (
            <Box sx={{ mt: 1.5 }}>
              {state === 'none' && (
                <Button
                  variant="outlined"
                  startIcon={
                    analysisBusy ? <CircularProgress size={16} /> : <AutoAwesomeIcon />
                  }
                  disabled={analysisBusy}
                  onClick={() => onRequestAnalysis?.(entry)}
                  sx={{ minHeight: 44 }}
                  data-testid="diary-request-analysis"
                >
                  {t('pages.plantDiary.analysis.request')}
                </Button>
              )}

              {/* AK-03: withdrawing is offered only while the entry is still
                  unclaimed. In `in_progress` no control appears at all — the
                  server would refuse with a 409, and offering a button that
                  cannot work is worse than offering none. */}
              {state === 'requested' && (
                <Button
                  variant="outlined"
                  color="inherit"
                  startIcon={analysisBusy ? <CircularProgress size={16} /> : <UndoIcon />}
                  disabled={analysisBusy}
                  onClick={() => onCancelAnalysis?.(entry)}
                  sx={{ minHeight: 44 }}
                  data-testid="diary-cancel-analysis"
                >
                  {t('pages.plantDiary.analysis.cancel')}
                </Button>
              )}

              {(state === 'completed' || state === 'failed') && (
                <Button
                  variant="outlined"
                  startIcon={analysisBusy ? <CircularProgress size={16} /> : <ReplayIcon />}
                  disabled={analysisBusy}
                  onClick={() => onRequestAnalysis?.(entry)}
                  sx={{ minHeight: 44 }}
                  data-testid="diary-request-analysis"
                >
                  {t('pages.plantDiary.analysis.requestAgain')}
                </Button>
              )}

              {(state === 'completed' || state === 'failed') && (
                <Typography
                  variant="caption"
                  color="text.secondary"
                  sx={{ display: 'block', mt: 0.5 }}
                >
                  {t('pages.plantDiary.analysis.requestAgainHint')}
                </Typography>
              )}
            </Box>
          )}
        </Box>
      </CardContent>
    </Card>
  );
}
