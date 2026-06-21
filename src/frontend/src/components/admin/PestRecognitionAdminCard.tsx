import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import { useTranslation } from 'react-i18next';
import Card from '@mui/material/Card';
import CardContent from '@mui/material/CardContent';
import Typography from '@mui/material/Typography';
import Box from '@mui/material/Box';
import Chip from '@mui/material/Chip';
import Alert from '@mui/material/Alert';
import Divider from '@mui/material/Divider';
import Skeleton from '@mui/material/Skeleton';
import Button from '@mui/material/Button';
import CircularProgress from '@mui/material/CircularProgress';
import Accordion from '@mui/material/Accordion';
import AccordionSummary from '@mui/material/AccordionSummary';
import AccordionDetails from '@mui/material/AccordionDetails';
import ImageList from '@mui/material/ImageList';
import ImageListItem from '@mui/material/ImageListItem';
import ImageListItemBar from '@mui/material/ImageListItemBar';
import IconButton from '@mui/material/IconButton';
import Tooltip from '@mui/material/Tooltip';
import Dialog from '@mui/material/Dialog';
import DialogTitle from '@mui/material/DialogTitle';
import DialogContent from '@mui/material/DialogContent';
import DialogContentText from '@mui/material/DialogContentText';
import DialogActions from '@mui/material/DialogActions';
import FormControl from '@mui/material/FormControl';
import InputLabel from '@mui/material/InputLabel';
import MenuItem from '@mui/material/MenuItem';
import Select from '@mui/material/Select';
import ExpandMoreIcon from '@mui/icons-material/ExpandMore';
import PlayArrowIcon from '@mui/icons-material/PlayArrow';
import CheckCircleIcon from '@mui/icons-material/CheckCircle';
import WarningAmberIcon from '@mui/icons-material/WarningAmber';
import PestControlIcon from '@mui/icons-material/PestControl';
import BugReportIcon from '@mui/icons-material/BugReport';
import VisibilityOffIcon from '@mui/icons-material/VisibilityOff';
import RestoreFromTrashIcon from '@mui/icons-material/RestoreFromTrash';
import {
  getPestClassImages,
  getPestRecognitionStatus,
  setPestImageActive,
  startPestAcquisition,
} from '@/api/endpoints/adminPestRecognition';
import { useNotification } from '@/hooks/useNotification';
import type { PestCoverageEntry, PestCurationImage, PestRecognitionStatus } from '@/api/types';

const PEST_EXCLUSION_REASONS = ['blurry', 'wrong_species', 'duplicate', 'irrelevant', 'manual'] as const;
type PestExclusionReason = (typeof PEST_EXCLUSION_REASONS)[number];

type GridColumnValue = string | Record<string, string>;

interface PestRecognitionAdminCardProps {
  gridColumn?: GridColumnValue;
}

/**
 * REQ-044 — admin panel for the few-shot pest-recognition index.
 *
 * Shows per-class coverage of the indexed reference images, lets the operator
 * start the cold-start acquisition job, and displays the acquired images per
 * class (provenance + attribution). Platform-admin only.
 */
export function PestRecognitionAdminCard({ gridColumn }: PestRecognitionAdminCardProps) {
  const { t } = useTranslation();
  const [status, setStatus] = useState<PestRecognitionStatus | null>(null);
  const [loading, setLoading] = useState(true);
  const [failed, setFailed] = useState(false);
  const [starting, setStarting] = useState(false);
  const [startError, setStartError] = useState(false);
  const [polling, setPolling] = useState(false);
  const lastCount = useRef<number>(-1);
  const stableTicks = useRef(0);

  const fetchStatus = useCallback(async (): Promise<PestRecognitionStatus | null> => {
    try {
      const data = await getPestRecognitionStatus();
      setStatus(data);
      setFailed(false);
      return data;
    } catch {
      setFailed(true);
      return null;
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    let active = true;
    const load = async () => {
      try {
        const data = await getPestRecognitionStatus();
        if (active) {
          setStatus(data);
          setFailed(false);
        }
      } catch {
        if (active) setFailed(true);
      } finally {
        if (active) setLoading(false);
      }
    };
    void load();
    return () => {
      active = false;
    };
  }, []);

  // While an acquisition job runs, poll every 5 s and stop once the index count
  // stops growing for two consecutive ticks (the job has no separate progress
  // store; the live count is the signal).
  useEffect(() => {
    if (!polling) return;
    let active = true;
    let timer: ReturnType<typeof setTimeout> | undefined;
    const tick = async () => {
      const data = await fetchStatus();
      if (!active) return;
      const count = data?.index_count ?? lastCount.current;
      if (count === lastCount.current) {
        stableTicks.current += 1;
      } else {
        stableTicks.current = 0;
        lastCount.current = count;
      }
      if (stableTicks.current >= 2) {
        setPolling(false);
        return;
      }
      timer = setTimeout(tick, 5000);
    };
    timer = setTimeout(tick, 5000);
    return () => {
      active = false;
      if (timer) clearTimeout(timer);
    };
  }, [polling, fetchStatus]);

  const handleStart = useCallback(async () => {
    setStarting(true);
    setStartError(false);
    try {
      await startPestAcquisition();
      lastCount.current = status?.index_count ?? 0;
      stableTicks.current = 0;
      setPolling(true);
    } catch {
      setStartError(true);
    } finally {
      setStarting(false);
    }
  }, [status]);

  // Derive a live-region message that only changes on meaningful state transitions
  // so screen readers are not flooded on every 5 s polling tick (UI-NFR-002 R-011).
  const liveMessage = useMemo(() => {
    if (loading) return t('pages.admin.pestRecognition.loading');
    if (startError) return t('pages.admin.pestRecognition.acquireError');
    if (polling) return t('pages.admin.pestRecognition.acquireRunningAriaLabel');
    return '';
  }, [loading, startError, polling, t]);

  return (
    <Card variant="outlined" sx={{ gridColumn }} data-testid="pest-recognition-admin-card">
      <CardContent sx={{ px: 2, pt: 2, '&:last-child': { pb: 2 } }}>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 0.5 }}>
          <PestControlIcon color="action" aria-hidden="true" />
          <Typography variant="h6">{t('pages.admin.pestRecognition.section')}</Typography>
        </Box>
        <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
          {t('pages.admin.pestRecognition.sectionHelper')}
        </Typography>

        {/* ARIA live region — announces job-state transitions to screen readers (UI-NFR-002 R-011). */}
        <Box
          role="status"
          aria-live="polite"
          aria-atomic="true"
          sx={{ position: 'absolute', width: 1, height: 1, overflow: 'hidden', clip: 'rect(0,0,0,0)' }}
        >
          {liveMessage}
        </Box>

        {loading && (
          <Box
            sx={{ display: 'flex', flexDirection: 'column', gap: 1 }}
            aria-busy="true"
            aria-label={t('pages.admin.pestRecognition.loading')}
          >
            <Skeleton variant="rounded" height={28} width={180} />
            <Skeleton variant="text" />
            <Skeleton variant="text" width="60%" />
          </Box>
        )}

        {!loading && failed && (
          <Alert severity="info" data-testid="pest-recognition-unavailable">
            {t('pages.admin.pestRecognition.statusUnavailable')}
          </Alert>
        )}

        {!loading && !failed && status && !status.feature_enabled && (
          <Alert severity="info" data-testid="pest-recognition-disabled">
            {t('pages.admin.pestRecognition.disabledHint')}
          </Alert>
        )}

        {!loading && !failed && status?.feature_enabled && (
          <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }} data-testid="pest-recognition-details">
            {/* Status chips — color + icon + explicit aria-label; info is never conveyed
                through colour alone (UI-NFR-002 R-018). */}
            <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1 }}>
              <Chip
                size="small"
                color="success"
                icon={<CheckCircleIcon aria-hidden="true" />}
                label={t('pages.admin.pestRecognition.chipActive')}
                aria-label={t('pages.admin.pestRecognition.chipActiveAriaLabel')}
              />
              {status.service_ready ? (
                <Chip
                  size="small"
                  color="success"
                  icon={<CheckCircleIcon aria-hidden="true" />}
                  label={t('pages.admin.pestRecognition.chipServiceReady')}
                  aria-label={t('pages.admin.pestRecognition.chipServiceReadyAriaLabel')}
                  data-testid="pest-recognition-chip-ready"
                />
              ) : (
                <Chip
                  size="small"
                  color="warning"
                  icon={<WarningAmberIcon aria-hidden="true" />}
                  label={t('pages.admin.pestRecognition.chipServiceUnreachable')}
                  aria-label={t('pages.admin.pestRecognition.chipServiceUnreachableAriaLabel')}
                  data-testid="pest-recognition-chip-unreachable"
                />
              )}
              <Chip
                size="small"
                variant="outlined"
                icon={<BugReportIcon aria-hidden="true" />}
                label={t('pages.admin.pestRecognition.chipIndexCount', { count: status.index_count })}
                aria-label={t('pages.admin.pestRecognition.chipIndexCountAriaLabel', { count: status.index_count })}
                data-testid="pest-recognition-chip-count"
              />
            </Box>

            {!status.service_ready && (
              <Alert severity="warning" data-testid="pest-recognition-service-warning">
                {t('pages.admin.pestRecognition.serviceWarning')}
              </Alert>
            )}

            <Box>
              <Button
                variant="outlined"
                size="small"
                startIcon={
                  starting || polling ? (
                    <CircularProgress size={16} color="inherit" aria-label={t('pages.admin.pestRecognition.acquireRunning')} />
                  ) : (
                    <PlayArrowIcon aria-hidden="true" />
                  )
                }
                onClick={handleStart}
                disabled={starting || polling || !status.service_ready}
                aria-busy={starting || polling}
                aria-describedby="pest-acquire-hint"
                sx={{ minHeight: 44 }}
                data-testid="pest-recognition-acquire-button"
              >
                {polling
                  ? t('pages.admin.pestRecognition.acquireRunning')
                  : t('pages.admin.pestRecognition.acquireStart')}
              </Button>
              <Typography
                id="pest-acquire-hint"
                variant="caption"
                color="text.secondary"
                sx={{ display: 'block', mt: 0.5 }}
              >
                {t('pages.admin.pestRecognition.acquireHint')}
              </Typography>
              {startError && (
                <Alert severity="error" sx={{ mt: 1 }} data-testid="pest-recognition-acquire-error">
                  {t('pages.admin.pestRecognition.acquireError')}
                </Alert>
              )}
            </Box>

            <Divider />

            <Box>
              <Typography variant="subtitle2" gutterBottom>
                {t('pages.admin.pestRecognition.coverageTitle')}
              </Typography>
              <Box sx={{ display: 'flex', flexDirection: 'column' }}>
                {status.classes.map((entry) => (
                  <PestClassRow key={entry.label} entry={entry} />
                ))}
              </Box>
            </Box>
          </Box>
        )}
      </CardContent>
    </Card>
  );
}

function PestClassRow({ entry }: { entry: PestCoverageEntry }) {
  const { t } = useTranslation();
  const notify = useNotification();
  const [images, setImages] = useState<PestCurationImage[] | null>(null);
  const [loadingImages, setLoadingImages] = useState(false);
  const [busyId, setBusyId] = useState<number | null>(null);
  const [deselectTarget, setDeselectTarget] = useState<PestCurationImage | null>(null);
  const [reason, setReason] = useState<PestExclusionReason>('blurry');

  const handleExpand = useCallback(
    async (_e: unknown, expanded: boolean) => {
      if (!expanded || images != null) return;
      setLoadingImages(true);
      try {
        const data = await getPestClassImages(entry.label);
        setImages(data.images);
      } catch {
        setImages([]);
      } finally {
        setLoadingImages(false);
      }
    },
    [entry.label, images],
  );

  // Toggle one image in/out of the few-shot index. Deselected images are kept
  // (audit trail) but excluded from matching, so a wrongly-acquired image no
  // longer affects detection (the inference kNN filters is_active = TRUE).
  const applyActive = useCallback(
    async (image: PestCurationImage, isActive: boolean, why?: PestExclusionReason) => {
      setBusyId(image.id);
      try {
        await setPestImageActive(entry.label, image.id, {
          is_active: isActive,
          reason: isActive ? null : (why ?? 'manual'),
        });
        setImages((prev) =>
          (prev ?? []).map((img) =>
            img.id === image.id
              ? { ...img, is_active: isActive, exclusion_reason: isActive ? null : (why ?? 'manual') }
              : img,
          ),
        );
        notify.success(
          isActive
            ? t('pages.admin.pestRecognition.reincludeSuccess')
            : t('pages.admin.pestRecognition.deselectSuccess'),
        );
      } catch {
        notify.error(t('pages.admin.pestRecognition.curationError'));
      } finally {
        setBusyId(null);
      }
    },
    [entry.label, notify, t],
  );

  const confirmDeselect = useCallback(async () => {
    if (!deselectTarget) return;
    const target = deselectTarget;
    setDeselectTarget(null);
    await applyActive(target, false, reason);
  }, [deselectTarget, reason, applyActive]);

  // Explicit usable status text for screen readers — never conveyed by colour alone (UI-NFR-002 R-018).
  const usableAriaLabel = entry.usable
    ? t('pages.admin.pestRecognition.classUsableAriaLabel', {
        name: entry.common_name,
        active: entry.active,
        target: entry.target,
      })
    : t('pages.admin.pestRecognition.classNotUsableAriaLabel', {
        name: entry.common_name,
        active: entry.active,
        target: entry.target,
      });

  return (
    <Accordion
      disableGutters
      elevation={0}
      square
      onChange={handleExpand}
      data-testid={`pest-class-${entry.label}`}
      sx={{ '&:before': { display: 'none' }, borderBottom: '1px solid', borderColor: 'divider' }}
    >
      {/* aria-label on AccordionSummary gives screen readers a meaningful name for the
          expand button instead of the raw button-role with no label (UI-NFR-002 R-007). */}
      <AccordionSummary
        expandIcon={<ExpandMoreIcon />}
        aria-label={t('pages.admin.pestRecognition.classExpandAriaLabel', { name: entry.common_name })}
        sx={{ px: 0 }}
      >
        <Box sx={{ display: 'flex', alignItems: 'center', flexWrap: 'wrap', gap: 1, width: '100%', pr: 1 }}>
          <Typography variant="body2" sx={{ fontWeight: 500, flexGrow: 1, minWidth: 120 }}>
            {entry.common_name}
          </Typography>
          <Chip
            size="small"
            variant="outlined"
            label={t(`enums.pestCategory.${entry.category}`)}
            color={entry.category === 'beneficial' ? 'success' : 'default'}
          />
          {/* Count text: visible colour cue + screen-reader accessible aria-label
              so the active/target ratio is never status-by-colour only. */}
          <Typography
            variant="caption"
            color={entry.usable ? 'success.main' : 'text.secondary'}
            aria-label={usableAriaLabel}
            data-testid={`pest-class-count-${entry.label}`}
          >
            {entry.active}/{entry.target}
          </Typography>
          {entry.usable ? (
            <CheckCircleIcon
              sx={{ fontSize: 16, color: 'success.main' }}
              aria-label={t('pages.admin.pestRecognition.usableLabel')}
            />
          ) : (
            <WarningAmberIcon
              sx={{ fontSize: 16, color: 'text.disabled' }}
              aria-label={t('pages.admin.pestRecognition.notUsableLabel')}
            />
          )}
        </Box>
      </AccordionSummary>
      <AccordionDetails sx={{ px: 0 }}>
        {loadingImages && (
          <Skeleton
            variant="rounded"
            height={80}
            aria-label={t('pages.admin.pestRecognition.galleryLoading')}
          />
        )}
        {!loadingImages && images != null && images.length === 0 && (
          <Typography variant="body2" color="text.secondary" data-testid={`pest-class-empty-${entry.label}`}>
            {t('pages.admin.pestRecognition.galleryEmpty')}
          </Typography>
        )}
        {!loadingImages && images != null && images.length > 0 && (
          // Responsive columns: 2 on mobile (xs), 3 on tablet+ (sm+).
          // 2 columns on xs gives larger tap targets (~48 % of card width each)
          // which comfortably exceeds the 44 px minimum (UI-NFR-001 R-004).
          <ImageList
            cols={3}
            gap={6}
            sx={{ m: 0, gridTemplateColumns: { xs: 'repeat(2, 1fr)', sm: 'repeat(3, 1fr)' } }}
            data-testid={`pest-class-gallery-${entry.label}`}
          >
            {images.map((img) => {
              const inactive = !img.is_active;
              return (
                <ImageListItem key={img.id} data-testid="pest-reference-image" data-active={img.is_active}>
                  <img
                    src={img.source_url}
                    alt={t('pages.admin.pestRecognition.imageAlt', { name: entry.common_name })}
                    loading="lazy"
                    referrerPolicy="no-referrer"
                    style={{
                      borderRadius: 4,
                      aspectRatio: '1 / 1',
                      objectFit: 'cover',
                      width: '100%',
                      // Deselected images are visibly muted so the active set is obvious.
                      filter: inactive ? 'grayscale(1)' : 'none',
                      opacity: inactive ? 0.45 : 1,
                    }}
                  />
                  {inactive && (
                    <Chip
                      size="small"
                      label={t('pages.admin.pestRecognition.excludedBadge')}
                      sx={{ position: 'absolute', top: 6, left: 6, bgcolor: 'rgba(0,0,0,0.7)', color: '#fff' }}
                    />
                  )}
                  <ImageListItemBar
                    subtitle={buildCaption(img)}
                    sx={{ '& .MuiImageListItemBar-subtitle': { fontSize: '0.65rem' } }}
                    actionIcon={
                      inactive ? (
                        <Tooltip title={t('pages.admin.pestRecognition.reinclude')}>
                          <span>
                            <IconButton
                              size="small"
                              disabled={busyId === img.id}
                              onClick={() => void applyActive(img, true)}
                              aria-label={t('pages.admin.pestRecognition.reincludeAria', { name: entry.common_name })}
                              data-testid="pest-reinclude-button"
                              sx={{ color: 'rgba(255,255,255,0.9)', p: { xs: 1.5, sm: 1 } }}
                            >
                              <RestoreFromTrashIcon fontSize="small" />
                            </IconButton>
                          </span>
                        </Tooltip>
                      ) : (
                        <Tooltip title={t('pages.admin.pestRecognition.deselect')}>
                          <span>
                            <IconButton
                              size="small"
                              disabled={busyId === img.id}
                              onClick={() => {
                                setReason('blurry');
                                setDeselectTarget(img);
                              }}
                              aria-label={t('pages.admin.pestRecognition.deselectAria', { name: entry.common_name })}
                              data-testid="pest-deselect-button"
                              sx={{ color: 'rgba(255,255,255,0.9)', p: { xs: 1.5, sm: 1 } }}
                            >
                              <VisibilityOffIcon fontSize="small" />
                            </IconButton>
                          </span>
                        </Tooltip>
                      )
                    }
                  />
                </ImageListItem>
              );
            })}
          </ImageList>
        )}
      </AccordionDetails>

      <Dialog
        open={!!deselectTarget}
        onClose={() => setDeselectTarget(null)}
        maxWidth="xs"
        fullWidth
        aria-labelledby={`pest-deselect-title-${entry.label}`}
        data-testid="pest-deselect-dialog"
      >
        <DialogTitle id={`pest-deselect-title-${entry.label}`}>
          {t('pages.admin.pestRecognition.deselectDialogTitle')}
        </DialogTitle>
        <DialogContent>
          <DialogContentText sx={{ mb: 2 }}>
            {t('pages.admin.pestRecognition.deselectDialogText')}
          </DialogContentText>
          <FormControl fullWidth size="small">
            <InputLabel id={`pest-deselect-reason-${entry.label}`}>
              {t('pages.admin.pestRecognition.reasonLabel')}
            </InputLabel>
            <Select
              labelId={`pest-deselect-reason-${entry.label}`}
              label={t('pages.admin.pestRecognition.reasonLabel')}
              value={reason}
              onChange={(e) => setReason(e.target.value as PestExclusionReason)}
              data-testid="pest-deselect-reason-select"
            >
              {PEST_EXCLUSION_REASONS.map((r) => (
                <MenuItem key={r} value={r}>
                  {t(`pages.admin.pestRecognition.reason.${r}`)}
                </MenuItem>
              ))}
            </Select>
          </FormControl>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setDeselectTarget(null)}>{t('common.cancel')}</Button>
          <Button onClick={() => void confirmDeselect()} color="error" variant="contained" data-testid="pest-deselect-confirm">
            {t('pages.admin.pestRecognition.deselect')}
          </Button>
        </DialogActions>
      </Dialog>
    </Accordion>
  );
}

function buildCaption(img: PestCurationImage): string {
  const parts: string[] = [];
  if (img.attribution) parts.push(`© ${img.attribution}`);
  if (img.license) parts.push(img.license);
  return parts.join(' · ');
}
