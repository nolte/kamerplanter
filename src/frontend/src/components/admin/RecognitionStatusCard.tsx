import { useEffect, useMemo, useRef, useState } from 'react';
import { useTranslation } from 'react-i18next';
import Card from '@mui/material/Card';
import CardContent from '@mui/material/CardContent';
import Typography from '@mui/material/Typography';
import Box from '@mui/material/Box';
import Chip from '@mui/material/Chip';
import Alert from '@mui/material/Alert';
import Divider from '@mui/material/Divider';
import LinearProgress from '@mui/material/LinearProgress';
import Skeleton from '@mui/material/Skeleton';
import Tooltip from '@mui/material/Tooltip';
import Button from '@mui/material/Button';
import CircularProgress from '@mui/material/CircularProgress';
import PlayArrowIcon from '@mui/icons-material/PlayArrow';
import InfoOutlinedIcon from '@mui/icons-material/InfoOutlined';
import CheckCircleIcon from '@mui/icons-material/CheckCircle';
import HourglassEmptyIcon from '@mui/icons-material/HourglassEmpty';
import WarningAmberIcon from '@mui/icons-material/WarningAmber';
import MemoryIcon from '@mui/icons-material/Memory';
import TaskAltIcon from '@mui/icons-material/TaskAlt';
import { visuallyHidden } from '@mui/utils';
import HelpTooltip from '@/components/common/HelpTooltip';
import { getRecognitionStatus, startRecognitionAcquisition } from '@/api/endpoints/adminSettings';
import type { RecognitionStatus } from '@/api/types';
import LoadingStatus from '@/components/common/LoadingStatus';

/** Responsive CSS grid-column value: a raw string or a per-breakpoint map. */
type GridColumnValue = string | Record<string, string>;

interface RecognitionStatusCardProps {
  /** Grid placement for the card, matching the surrounding settings grid. */
  gridColumn?: GridColumnValue;
}

/** Format a 0..1 confidence threshold as a percentage string (no decimals). */
function formatPercent(value: number): string {
  return `${Math.round(value * 100)}%`;
}

/**
 * REQ-029-A — read-only status panel for the self-hosted DINOv2 recognition.
 *
 * Rendered inside the smart-home/integrations tab for all signed-in users.
 * Fetches GET /admin/recognition/status on mount; when the feature is disabled
 * it shows only a discreet hint and never surfaces empty/error values.
 */
export function RecognitionStatusCard({ gridColumn }: RecognitionStatusCardProps) {
  const { t } = useTranslation();
  const [status, setStatus] = useState<RecognitionStatus | null>(null);
  const [loading, setLoading] = useState(true);
  const [failed, setFailed] = useState(false);
  // Bumped after a manual "start acquisition" click to re-run the fetch/poll
  // effect; also lets the effect poll from processed=0 right after a kick-off.
  const [reloadKey, setReloadKey] = useState(0);
  const [starting, setStarting] = useState(false);
  const [startError, setStartError] = useState(false);
  // True from a successful dispatch until the first species is processed, so the
  // card shows a distinct "starting up" state instead of staying on "not started"
  // (the run is queued but reference_image_jobs are not written yet).
  const [justStarted, setJustStarted] = useState(false);
  const liveRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    let active = true;
    let timer: ReturnType<typeof setTimeout> | undefined;

    // Recursive setTimeout (not setInterval): each tick decides whether to
    // re-poll, so there is no stale closure and no overlapping intervals.
    // We keep polling (every 5 s) while a run is in progress (some but not all
    // species processed), or right after the user kicked one off (reloadKey > 0,
    // processed may still be 0). Polling stops once all species are processed,
    // and idles when nothing was ever started.
    const tick = async () => {
      try {
        const data = await getRecognitionStatus();
        if (!active) return;
        setStatus(data);
        setFailed(false);
        const cov = data.coverage;
        const incomplete =
          data.feature_enabled &&
          data.inference_service.ready &&
          cov.total_species > 0 &&
          cov.processed_species < cov.total_species;
        const running = incomplete && (cov.processed_species > 0 || reloadKey > 0);
        if (running) timer = setTimeout(tick, 5000);
      } catch {
        if (active) setFailed(true);
      } finally {
        if (active) setLoading(false);
      }
    };

    tick();
    return () => {
      active = false;
      if (timer) clearTimeout(timer);
    };
  }, [reloadKey]);

  const handleStartAcquisition = async () => {
    setStarting(true);
    setStartError(false);
    try {
      await startRecognitionAcquisition();
      // Show the "starting up" state and re-run the effect so progress polling
      // begins immediately, even though processed is still 0.
      setJustStarted(true);
      setReloadKey((k) => k + 1);
    } catch {
      setStartError(true);
    } finally {
      setStarting(false);
    }
  };

  const inference = status?.inference_service;
  const coverage = status?.coverage;
  const config = status?.config;
  // Acquisition progress: how many species an acquisition run has processed.
  const processedPercent =
    coverage && coverage.total_species > 0
      ? Math.round((coverage.processed_species / coverage.total_species) * 100)
      : 0;
  const jobState: 'notStarted' | 'queued' | 'running' | 'complete' | null = !coverage
    ? null
    : coverage.processed_species === 0
      ? // After a successful kick-off the run is queued/starting up, but no
        // species has been processed yet — distinct from never having started.
        justStarted
        ? 'queued'
        : 'notStarted'
      : coverage.processed_species < coverage.total_species
        ? 'running'
        : 'complete';

  // Derived live-region message. It only changes when loading/jobState/startError
  // change, so the aria-live region announces on transition (not on every 5 s
  // polling tick) — no ref mutation during render, no redundant state update.
  // startError is included so screen readers hear the failure immediately.
  const liveMessage = useMemo(() => {
    if (loading) return t('pages.admin.recognition.loading');
    if (startError) return t('pages.admin.recognition.acquireError');
    if (jobState === 'queued') return t('pages.admin.recognition.jobQueuedAriaLabel');
    if (jobState === 'running') return t('pages.admin.recognition.jobRunningAriaLabel');
    if (jobState === 'complete') return t('pages.admin.recognition.jobCompleteAriaLabel');
    return '';
  }, [jobState, loading, startError, t]);

  return (
    <Card variant="outlined" sx={{ gridColumn }} data-testid="recognition-status-card">
      <CardContent
        component="fieldset"
        sx={{ border: 'none', p: 0, m: 0, '&:last-child': { pb: 2 }, px: 2, pt: 2 }}
      >
        {/* Card header */}
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, pt: 1.5, mb: 0.5 }}>
          <MemoryIcon color="action" aria-hidden="true" />
          <HelpTooltip term="dinov2">
            <Typography component="legend" variant="h6">
              {t('pages.admin.recognition.section')}
            </Typography>
          </HelpTooltip>
        </Box>
        <Typography variant="body2" color="text.secondary" sx={{ mb: 2.5 }}>
          {t('pages.admin.recognition.sectionHelper')}
        </Typography>

        {/* ARIA live region — announces job-state transitions, not every polling tick (UI-NFR-002 R-011). */}
        <Box
          ref={liveRef}
          role="status"
          aria-live="polite"
          aria-atomic="true"
          sx={visuallyHidden}
        >
          {liveMessage}
        </Box>

        {loading && (
          <Box
            sx={{ display: 'flex', flexDirection: 'column', gap: 1 }}
            aria-busy="true"
          >
            <LoadingStatus label={t('pages.admin.recognition.loading')} />
            <Skeleton variant="rounded" height={28} width={180} />
            <Skeleton variant="text" />
            <Skeleton variant="text" width="60%" />
          </Box>
        )}

        {!loading && failed && (
          <Alert severity="info" data-testid="recognition-status-unavailable">
            {t('pages.admin.recognition.statusUnavailable')}
          </Alert>
        )}

        {/* Feature disabled — discreet hint only, no empty values. */}
        {!loading && !failed && status && !status.feature_enabled && (
          <Alert severity="info" data-testid="recognition-disabled-hint">
            <Typography variant="body2" sx={{ fontWeight: 600 }}>
              {t('pages.admin.recognition.disabledTitle')}
            </Typography>
            <Typography variant="body2" sx={{ mt: 0.5 }}>
              {t('pages.admin.recognition.disabledHint')}
            </Typography>
          </Alert>
        )}

        {/* Feature enabled — full read-only status. */}
        {!loading && !failed && status?.feature_enabled && inference && coverage && config && (
          <Box
            sx={{ display: 'flex', flexDirection: 'column', gap: 2.5 }}
            data-testid="recognition-status-details"
          >
            {/* Status chips — color + icon + explicit aria-label to satisfy UI-NFR-002 R-018. */}
            <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1 }}>
              <Chip
                size="small"
                color="success"
                icon={<CheckCircleIcon aria-hidden="true" />}
                label={t('pages.admin.recognition.chipActive')}
                aria-label={t('pages.admin.recognition.chipActiveAriaLabel')}
                data-testid="recognition-chip-active"
              />
              {inference.ready ? (
                <Chip
                  size="small"
                  color="success"
                  icon={<CheckCircleIcon aria-hidden="true" />}
                  label={t('pages.admin.recognition.chipServiceReady')}
                  aria-label={t('pages.admin.recognition.chipServiceReadyAriaLabel')}
                  data-testid="recognition-chip-ready"
                />
              ) : (
                <Chip
                  size="small"
                  color="warning"
                  icon={<WarningAmberIcon aria-hidden="true" />}
                  label={t('pages.admin.recognition.chipServiceUnreachable')}
                  aria-label={t('pages.admin.recognition.chipServiceUnreachableAriaLabel')}
                  data-testid="recognition-chip-unreachable"
                />
              )}
              {inference.ready && inference.model && (
                <Chip
                  size="small"
                  variant="outlined"
                  icon={<MemoryIcon aria-hidden="true" />}
                  label={
                    inference.dim
                      ? `${inference.model} (${inference.dim})`
                      : inference.model
                  }
                  aria-label={t('pages.admin.recognition.chipModelAriaLabel', {
                    model: inference.dim
                      ? `${inference.model} (${inference.dim})`
                      : inference.model,
                  })}
                  data-testid="recognition-chip-model"
                />
              )}
            </Box>

            {!inference.ready && (
              <Alert severity="warning" data-testid="recognition-service-warning">
                {t('pages.admin.recognition.serviceWarning')}
              </Alert>
            )}

            <Divider />

            {/* Acquisition progress + coverage */}
            <Box>
              {/* Section header: title + job-state chip. The chip carries colour AND an icon
                  so status is never conveyed through colour alone (UI-NFR-002 R-018). */}
              <Box sx={{ display: 'flex', alignItems: 'center', flexWrap: 'wrap', gap: 1, mb: 0.5 }}>
                <Typography variant="subtitle2">
                  {t('pages.admin.recognition.coverageTitle')}
                </Typography>
                {jobState === 'notStarted' && (
                  <Chip
                    size="small"
                    color="default"
                    icon={<HourglassEmptyIcon aria-hidden="true" />}
                    label={t('pages.admin.recognition.jobNotStarted')}
                    aria-label={t('pages.admin.recognition.jobNotStartedAriaLabel')}
                    data-testid="recognition-job-not-started"
                  />
                )}
                {jobState === 'queued' && (
                  <Chip
                    size="small"
                    color="info"
                    icon={<HourglassEmptyIcon aria-hidden="true" />}
                    label={t('pages.admin.recognition.jobQueued')}
                    aria-label={t('pages.admin.recognition.jobQueuedAriaLabel')}
                    data-testid="recognition-job-queued"
                  />
                )}
                {jobState === 'running' && (
                  <Chip
                    size="small"
                    color="info"
                    icon={<HourglassEmptyIcon aria-hidden="true" />}
                    label={t('pages.admin.recognition.jobRunning')}
                    aria-label={t('pages.admin.recognition.jobRunningAriaLabel')}
                    data-testid="recognition-job-running"
                  />
                )}
                {jobState === 'complete' && (
                  <Chip
                    size="small"
                    color="success"
                    icon={<CheckCircleIcon aria-hidden="true" />}
                    label={t('pages.admin.recognition.jobComplete')}
                    aria-label={t('pages.admin.recognition.jobCompleteAriaLabel')}
                    data-testid="recognition-job-complete"
                  />
                )}
              </Box>

              {/* Intro text: clarifies what "processed" means vs. "recognizable" below.
                  Shown for all job states so the two concepts are always contextualised. */}
              <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
                {t('pages.admin.recognition.coverageIntro')}
              </Typography>

              {/* Processing progress — grows live during an acquisition run.
                  aria-live is intentionally NOT set here: the global live region (role="status"
                  above) handles state-change announcements so screen readers are not flooded
                  with updates on every 5 s polling tick. */}
              <Typography
                variant="body2"
                color="text.secondary"
                data-testid="recognition-processed-text"
              >
                {t('pages.admin.recognition.processedText', {
                  processed: coverage.processed_species,
                  total: coverage.total_species,
                })}
              </Typography>
              {/* aria-label alone is sufficient; aria-valuetext with identical text is redundant.
                  aria-valuemin/max are only set for determinate mode — in indeterminate mode
                  there is no concrete progress value, so exposing min/max would mislead
                  screen readers into announcing "0 of 100" when the actual value is unknown
                  (WCAG 4.1.2). */}
              <LinearProgress
                variant={jobState === 'queued' ? 'indeterminate' : 'determinate'}
                value={jobState === 'queued' ? undefined : processedPercent}
                sx={{ mt: 0.75, height: 8, borderRadius: 1 }}
                aria-label={
                  jobState === 'queued'
                    ? t('pages.admin.recognition.jobQueuedAriaLabel')
                    : t('pages.admin.recognition.processedBarAriaLabel', {
                        percent: processedPercent,
                        processed: coverage.processed_species,
                        total: coverage.total_species,
                      })
                }
                {...(jobState !== 'queued' && { 'aria-valuemin': 0, 'aria-valuemax': 100 })}
                data-testid="recognition-processed-bar"
              />

              {/* Result row — visually separated from the progress row above so users
                  can clearly distinguish "run progress" from "recognition outcome". */}
              <Box
                sx={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: 0.75,
                  mt: 1.5,
                  pt: 1,
                  borderTop: '1px solid',
                  borderColor: 'divider',
                }}
              >
                <TaskAltIcon
                  sx={{ fontSize: 16, color: jobState === 'complete' ? 'success.main' : 'text.disabled' }}
                  aria-hidden="true"
                />
                <Typography
                  variant="body2"
                  color="text.secondary"
                  data-testid="recognition-coverage-text"
                >
                  {t('pages.admin.recognition.coverageText', {
                    usable: coverage.usable_species,
                    total: coverage.total_species,
                  })}
                </Typography>
              </Box>

              {jobState === 'notStarted' && (
                <Alert severity="info" sx={{ mt: 1.5 }} data-testid="recognition-job-not-started-hint">
                  {t('pages.admin.recognition.jobNotStartedHint')}
                </Alert>
              )}

              {/* Confirmation after kick-off: the run is queued but no species
                  is processed yet, so reassure the user that it is under way. */}
              {jobState === 'queued' && (
                <Alert severity="success" sx={{ mt: 1.5 }} data-testid="recognition-job-queued-hint">
                  {t('pages.admin.recognition.jobQueuedHint')}
                </Alert>
              )}

              {/* The one action on this otherwise read-only card: kick off an
                  acquisition run. Only useful when the service is reachable.
                  aria-describedby links the button to the hint caption so screen
                  readers read the full description in addition to the button label.
                  aria-busy signals an in-progress operation without disabling the
                  element from the accessibility tree (WCAG 4.1.3). */}
              {inference.ready && (
                <Box sx={{ mt: 2 }}>
                  <Button
                    variant="outlined"
                    size="small"
                    startIcon={
                      starting ? (
                        <CircularProgress
                          size={16}
                          color="inherit"
                          aria-label={t('pages.admin.recognition.acquireStarting')}
                        />
                      ) : (
                        <PlayArrowIcon aria-hidden="true" />
                      )
                    }
                    onClick={handleStartAcquisition}
                    disabled={starting || jobState === 'queued' || jobState === 'running'}
                    aria-busy={starting}
                    aria-describedby="recognition-acquire-hint"
                    data-testid="recognition-acquire-button"
                  >
                    {starting
                      ? t('pages.admin.recognition.acquireStarting')
                      : jobState === 'queued' || jobState === 'running'
                        ? t('pages.admin.recognition.acquireRunning')
                        : t('pages.admin.recognition.acquireStart')}
                  </Button>
                  <Typography
                    id="recognition-acquire-hint"
                    variant="caption"
                    color="text.secondary"
                    sx={{ display: 'block', mt: 0.5 }}
                  >
                    {t('pages.admin.recognition.acquireHint')}
                  </Typography>
                  {startError && (
                    <Alert severity="error" sx={{ mt: 1 }} data-testid="recognition-acquire-error">
                      {t('pages.admin.recognition.acquireError')}
                    </Alert>
                  )}
                </Box>
              )}
            </Box>

            <Divider />

            {/* Read-only configuration */}
            <Box>
              <Typography variant="subtitle2" gutterBottom>
                {t('pages.admin.recognition.configTitle')}
              </Typography>
              <Box sx={{ display: 'flex', flexDirection: 'column', gap: 0.75 }}>
                <ConfigRow
                  label={t('pages.admin.recognition.configPrimaryAdapter')}
                  helpText={t('pages.admin.recognition.configPrimaryAdapterHelp')}
                  helpTerm="embedding_adapter"
                  value={config.primary_adapter}
                />
                <ConfigRow
                  label={t('pages.admin.recognition.configAutoAccept')}
                  helpText={t('pages.admin.recognition.configAutoAcceptHelp')}
                  helpTerm="confidence_score"
                  value={formatPercent(config.confidence_auto_accept)}
                />
                <ConfigRow
                  label={t('pages.admin.recognition.configMinShow')}
                  helpText={t('pages.admin.recognition.configMinShowHelp')}
                  helpTerm="confidence_score"
                  value={formatPercent(config.confidence_min_show)}
                />
                <ConfigRow
                  label={t('pages.admin.recognition.configMinReferenceImages')}
                  helpText={t('pages.admin.recognition.configMinReferenceImagesHelp')}
                  value={String(config.reference_image_min_usable)}
                />
                <ConfigRow
                  label={t('pages.admin.recognition.configWikimedia')}
                  helpText={t('pages.admin.recognition.configWikimediaHelp')}
                  value={
                    config.use_wikimedia
                      ? t('pages.admin.recognition.enabledValue')
                      : t('pages.admin.recognition.disabledValue')
                  }
                />
              </Box>
            </Box>

            <Typography variant="caption" color="text.secondary">
              {t('pages.admin.recognition.readOnlyNote')}
            </Typography>
          </Box>
        )}
      </CardContent>
    </Card>
  );
}

interface ConfigRowProps {
  label: string;
  /** Short plain-text explanation shown in a tooltip on the info icon. */
  helpText?: string;
  /** When set a HelpTooltip (glossary term) is rendered instead of the plain info icon. */
  helpTerm?: string;
  value: string;
}

/**
 * A single read-only label/value row in the configuration list.
 *
 * On narrow viewports (xs) the label and value wrap to separate lines so neither
 * clips — the value stays right-aligned relative to the label row.
 * On sm+ they remain on one line with a flex spacer between them.
 */
function ConfigRow({ label, helpText, helpTerm, value }: ConfigRowProps) {
  const { t } = useTranslation();

  const labelNode = (
    <Box
      sx={{
        display: 'flex',
        alignItems: 'center',
        gap: 0.5,
        minWidth: 0,
        flexShrink: 1,
      }}
    >
      <Typography variant="body2" color="text.secondary" sx={{ minWidth: 0 }}>
        {label}
      </Typography>
      {helpTerm ? (
        <HelpTooltip term={helpTerm} iconOnly />
      ) : helpText ? (
        <Tooltip
          title={helpText}
          placement="top"
          arrow
          enterDelay={300}
        >
          <Box
            component="span"
            tabIndex={0}
            aria-label={`${t('common.description')}: ${helpText}`}
            sx={{
              display: 'inline-flex',
              alignItems: 'center',
              cursor: 'help',
              minWidth: 24,
              minHeight: 24,
              p: '3px',
            }}
          >
            <InfoOutlinedIcon
              sx={{ fontSize: 14, color: 'text.secondary' }}
              aria-hidden="true"
            />
          </Box>
        </Tooltip>
      ) : null}
    </Box>
  );

  return (
    <Box
      sx={{
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'flex-start',
        gap: 1,
        flexWrap: { xs: 'wrap', sm: 'nowrap' },
      }}
    >
      {labelNode}
      <Typography
        variant="body2"
        sx={{
          fontWeight: 500,
          textAlign: 'right',
          flexShrink: 0,
          wordBreak: 'break-word',
        }}
      >
        {value}
      </Typography>
    </Box>
  );
}
