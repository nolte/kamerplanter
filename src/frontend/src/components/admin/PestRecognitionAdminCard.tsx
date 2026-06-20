import { useCallback, useEffect, useRef, useState } from 'react';
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
import ExpandMoreIcon from '@mui/icons-material/ExpandMore';
import PlayArrowIcon from '@mui/icons-material/PlayArrow';
import CheckCircleIcon from '@mui/icons-material/CheckCircle';
import WarningAmberIcon from '@mui/icons-material/WarningAmber';
import PestControlIcon from '@mui/icons-material/PestControl';
import BugReportIcon from '@mui/icons-material/BugReport';
import {
  getPestClassImages,
  getPestRecognitionStatus,
  startPestAcquisition,
} from '@/api/endpoints/adminPestRecognition';
import type { PestCoverageEntry, PestCurationImage, PestRecognitionStatus } from '@/api/types';

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

        {loading && (
          <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1 }} aria-busy="true">
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
            <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1 }}>
              <Chip
                size="small"
                color="success"
                icon={<CheckCircleIcon aria-hidden="true" />}
                label={t('pages.admin.pestRecognition.chipActive')}
              />
              {status.service_ready ? (
                <Chip
                  size="small"
                  color="success"
                  icon={<CheckCircleIcon aria-hidden="true" />}
                  label={t('pages.admin.pestRecognition.chipServiceReady')}
                  data-testid="pest-recognition-chip-ready"
                />
              ) : (
                <Chip
                  size="small"
                  color="warning"
                  icon={<WarningAmberIcon aria-hidden="true" />}
                  label={t('pages.admin.pestRecognition.chipServiceUnreachable')}
                  data-testid="pest-recognition-chip-unreachable"
                />
              )}
              <Chip
                size="small"
                variant="outlined"
                icon={<BugReportIcon aria-hidden="true" />}
                label={t('pages.admin.pestRecognition.chipIndexCount', { count: status.index_count })}
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
                    <CircularProgress size={16} color="inherit" />
                  ) : (
                    <PlayArrowIcon aria-hidden="true" />
                  )
                }
                onClick={handleStart}
                disabled={starting || polling || !status.service_ready}
                aria-busy={starting || polling}
                sx={{ minHeight: 44 }}
                data-testid="pest-recognition-acquire-button"
              >
                {polling
                  ? t('pages.admin.pestRecognition.acquireRunning')
                  : t('pages.admin.pestRecognition.acquireStart')}
              </Button>
              <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mt: 0.5 }}>
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
  const [images, setImages] = useState<PestCurationImage[] | null>(null);
  const [loadingImages, setLoadingImages] = useState(false);

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

  return (
    <Accordion
      disableGutters
      elevation={0}
      square
      onChange={handleExpand}
      data-testid={`pest-class-${entry.label}`}
      sx={{ '&:before': { display: 'none' }, borderBottom: '1px solid', borderColor: 'divider' }}
    >
      <AccordionSummary expandIcon={<ExpandMoreIcon />} sx={{ px: 0 }}>
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
          <Typography
            variant="caption"
            color={entry.usable ? 'success.main' : 'text.secondary'}
            data-testid={`pest-class-count-${entry.label}`}
          >
            {entry.active}/{entry.target}
          </Typography>
          {entry.usable ? (
            <CheckCircleIcon sx={{ fontSize: 16, color: 'success.main' }} aria-hidden="true" />
          ) : (
            <WarningAmberIcon sx={{ fontSize: 16, color: 'text.disabled' }} aria-hidden="true" />
          )}
        </Box>
      </AccordionSummary>
      <AccordionDetails sx={{ px: 0 }}>
        {loadingImages && <Skeleton variant="rounded" height={80} />}
        {!loadingImages && images != null && images.length === 0 && (
          <Typography variant="body2" color="text.secondary" data-testid={`pest-class-empty-${entry.label}`}>
            {t('pages.admin.pestRecognition.galleryEmpty')}
          </Typography>
        )}
        {!loadingImages && images != null && images.length > 0 && (
          <ImageList cols={3} gap={6} sx={{ m: 0 }} data-testid={`pest-class-gallery-${entry.label}`}>
            {images.map((img) => (
              <ImageListItem key={img.id} data-testid="pest-reference-image">
                <img
                  src={img.source_url}
                  alt={t('pages.admin.pestRecognition.imageAlt', { name: entry.common_name })}
                  loading="lazy"
                  referrerPolicy="no-referrer"
                  style={{ borderRadius: 4, aspectRatio: '1 / 1', objectFit: 'cover' }}
                />
                <ImageListItemBar
                  subtitle={buildCaption(img)}
                  sx={{ '& .MuiImageListItemBar-subtitle': { fontSize: '0.65rem' } }}
                />
              </ImageListItem>
            ))}
          </ImageList>
        )}
      </AccordionDetails>
    </Accordion>
  );
}

function buildCaption(img: PestCurationImage): string {
  const parts: string[] = [];
  if (img.attribution) parts.push(`© ${img.attribution}`);
  if (img.license) parts.push(img.license);
  return parts.join(' · ');
}
