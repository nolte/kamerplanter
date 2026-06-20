import { useCallback, useEffect, useMemo, useState } from 'react';
import { useTranslation } from 'react-i18next';
import Dialog from '@mui/material/Dialog';
import DialogTitle from '@mui/material/DialogTitle';
import DialogContent from '@mui/material/DialogContent';
import DialogActions from '@mui/material/DialogActions';
import Box from '@mui/material/Box';
import Button from '@mui/material/Button';
import Radio from '@mui/material/Radio';
import RadioGroup from '@mui/material/RadioGroup';
import FormControlLabel from '@mui/material/FormControlLabel';
import FormControl from '@mui/material/FormControl';
import FormLabel from '@mui/material/FormLabel';
import Typography from '@mui/material/Typography';
import Alert from '@mui/material/Alert';
import Divider from '@mui/material/Divider';
import List from '@mui/material/List';
import ListItem from '@mui/material/ListItem';
import ListItemText from '@mui/material/ListItemText';
import CircularProgress from '@mui/material/CircularProgress';
import useMediaQuery from '@mui/material/useMediaQuery';
import { useTheme } from '@mui/material/styles';
import { useNotification } from '@/hooks/useNotification';
import { useApiError } from '@/hooks/useApiError';
import {
  assessPhotoQuality,
  getAssessmentAdapters,
  type AssessmentAdapter,
  type PlantPhoto,
} from '@/api/endpoints/plantPhotos';
import QualityRatingBadge from './QualityRatingBadge';

interface PlantPhotoAssessDialogProps {
  /** The photo being assessed, or `null` when the dialog is closed. */
  photo: PlantPhoto | null;
  plantInstanceKey: string;
  onClose: () => void;
  /** Called with the updated photo after a successful assessment (persisted). */
  onAssessed: (updated: PlantPhoto) => void;
}

type AdapterKey = 'plantnet' | 'local_embedding';

/**
 * REQ-034 §4a — on-demand image-quality check for a gallery photo.
 *
 * The user picks the recognition path (Pl@ntNet / DINOv2). The DINOv2 option is
 * shown greyed-out with a hint until the self-hosted inference service is
 * enabled (Phase 2) — no dead/hidden code (§4a.1). Choosing the external
 * Pl@ntNet path shows a privacy notice (the photo is sent to a third party,
 * §4a.3). After running, the Ampel verdict + the top suggestions are shown and
 * the result is persisted on the photo.
 */
export default function PlantPhotoAssessDialog({
  photo,
  plantInstanceKey,
  onClose,
  onAssessed,
}: PlantPhotoAssessDialogProps) {
  const { t } = useTranslation();
  const theme = useTheme();
  const fullScreen = useMediaQuery(theme.breakpoints.down('sm'));
  const notification = useNotification();
  const { handleError } = useApiError();

  const [adapters, setAdapters] = useState<AssessmentAdapter[]>([]);
  const [adaptersLoading, setAdaptersLoading] = useState(false);
  const [selected, setSelected] = useState<AdapterKey>('plantnet');
  const [running, setRunning] = useState(false);
  const [result, setResult] = useState<PlantPhoto | null>(null);

  const open = photo !== null;

  // Load the selectable adapters whenever the dialog opens. The fresh-result
  // reset is derived from the open photo (see ``assessment`` below) rather than
  // a synchronous setState in the effect body, so no cascading render occurs.
  useEffect(() => {
    if (!open) return;
    let cancelled = false;
    setAdaptersLoading(true);
    getAssessmentAdapters(plantInstanceKey)
      .then((list) => {
        if (cancelled) return;
        setAdapters(list);
        // Default to the first available adapter, else keep plantnet.
        const firstAvailable = list.find((a) => a.available);
        if (firstAvailable) setSelected(firstAvailable.key as AdapterKey);
      })
      .catch((err) => {
        if (!cancelled) handleError(err);
      })
      .finally(() => {
        if (!cancelled) setAdaptersLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, [open, plantInstanceKey, handleError]);

  const adapterByKey = useMemo(() => {
    const map = new Map<string, AssessmentAdapter>();
    adapters.forEach((a) => map.set(a.key, a));
    return map;
  }, [adapters]);

  const selectedAdapter = adapterByKey.get(selected);
  const canRun = !!selectedAdapter?.available && !running;
  const showExternalNotice =
    selected === 'plantnet' && (adapterByKey.get('plantnet')?.external ?? true);

  const handleRun = useCallback(async () => {
    if (!photo) return;
    setRunning(true);
    try {
      const updated = await assessPhotoQuality(plantInstanceKey, photo.attachment_id, selected);
      setResult(updated);
      onAssessed(updated);
      notification.success(t('pages.plantPhotos.quality.assessed'));
    } catch (err) {
      handleError(err);
    } finally {
      setRunning(false);
    }
  }, [photo, plantInstanceKey, selected, onAssessed, notification, handleError, t]);

  // Stable list of the pickable adapters in a fixed display order.
  const orderedAdapters = useMemo<{ key: AdapterKey; adapter?: AssessmentAdapter }[]>(
    () => [
      { key: 'plantnet', adapter: adapterByKey.get('plantnet') },
      { key: 'local_embedding', adapter: adapterByKey.get('local_embedding') },
    ],
    [adapterByKey],
  );

  // Only show a result that belongs to the photo currently open — when the
  // dialog reopens for a different photo the stale result is ignored (no effect
  // reset needed). ``runLabel`` likewise treats a stale result as "not yet run".
  const freshResult =
    result && photo && result.attachment_id === photo.attachment_id ? result : null;
  const assessment = freshResult?.quality_assessment ?? null;

  return (
    <Dialog
      open={open}
      onClose={onClose}
      fullScreen={fullScreen}
      maxWidth="sm"
      fullWidth
      aria-labelledby="assess-dialog-title"
      data-testid="plant-photo-assess-dialog"
    >
      <DialogTitle id="assess-dialog-title">
        {t('pages.plantPhotos.quality.dialogTitle')}
      </DialogTitle>
      <DialogContent dividers>
        <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
          {t('pages.plantPhotos.quality.dialogIntro')}
        </Typography>

        {adaptersLoading ? (
          <Box sx={{ display: 'flex', justifyContent: 'center', py: 3 }}>
            <CircularProgress size={28} aria-label={t('common.loading')} />
          </Box>
        ) : (
          <FormControl component="fieldset" sx={{ width: '100%' }}>
            <FormLabel id="assess-adapter-label">
              {t('pages.plantPhotos.quality.chooseMethod')}
            </FormLabel>
            <RadioGroup
              aria-labelledby="assess-adapter-label"
              value={selected}
              onChange={(e) => setSelected(e.target.value as AdapterKey)}
            >
              {orderedAdapters.map(({ key, adapter }) => {
                const available = adapter?.available ?? false;
                return (
                  <FormControlLabel
                    key={key}
                    value={key}
                    disabled={!available}
                    control={<Radio data-testid={`assess-adapter-${key}`} />}
                    label={
                      <Box>
                        <Typography variant="body2">
                          {t(`pages.plantPhotos.quality.adapter.${key}`)}
                        </Typography>
                        <Typography variant="caption" color="text.secondary">
                          {available
                            ? t(`pages.plantPhotos.quality.adapterHint.${key}`)
                            : t(`pages.plantPhotos.quality.adapterUnavailable.${key}`)}
                        </Typography>
                      </Box>
                    }
                  />
                );
              })}
            </RadioGroup>
          </FormControl>
        )}

        {showExternalNotice && (
          <Alert severity="warning" sx={{ mt: 2 }} data-testid="assess-external-notice">
            {t('pages.plantPhotos.quality.externalNotice')}
          </Alert>
        )}

        {assessment && (
          <Box sx={{ mt: 3 }} data-testid="assess-result">
            <Divider sx={{ mb: 2 }} />
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.5, mb: 1 }}>
              <QualityRatingBadge rating={assessment.rating} size="medium" />
              <Typography variant="subtitle2">
                {t(`pages.plantPhotos.quality.resultHeadline.${assessment.rating}`)}
              </Typography>
            </Box>
            <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
              {t(`pages.plantPhotos.quality.ratingHint.${assessment.rating}`)}
            </Typography>
            {(assessment.rating === 'poor' || assessment.rating === 'fair') && (
              <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
                {t(`pages.plantPhotos.quality.ratingAction.${assessment.rating}`)}
              </Typography>
            )}
            {assessment.suggestions.length > 0 ? (
              <>
                <Typography variant="caption" color="text.secondary">
                  {t('pages.plantPhotos.quality.suggestionsLabel')}
                </Typography>
                <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mb: 0.5 }}>
                  {t('pages.plantPhotos.quality.confidenceExplained')}
                </Typography>
                <List dense disablePadding data-testid="assess-suggestions">
                  {assessment.suggestions.map((s, idx) => (
                    <ListItem key={`${s.scientific_name}-${idx}`} disableGutters>
                      <ListItemText
                        primary={s.scientific_name}
                        secondary={t('pages.plantPhotos.quality.confidence', {
                          percent: Math.round(s.confidence * 100),
                        })}
                      />
                    </ListItem>
                  ))}
                </List>
              </>
            ) : (
              <Typography variant="body2" color="text.secondary">
                {t('pages.plantPhotos.quality.noSuggestions')}
              </Typography>
            )}
          </Box>
        )}
      </DialogContent>
      <DialogActions>
        <Button onClick={onClose} data-testid="assess-close">
          {freshResult ? t('common.close') : t('common.cancel')}
        </Button>
        <Button
          variant="contained"
          onClick={handleRun}
          disabled={!canRun}
          startIcon={running ? <CircularProgress size={16} color="inherit" /> : undefined}
          sx={{ minHeight: 44 }}
          data-testid="assess-run"
        >
          {running
            ? t('pages.plantPhotos.quality.running')
            : freshResult
              ? t('pages.plantPhotos.quality.runAgain')
              : t('pages.plantPhotos.quality.run')}
        </Button>
      </DialogActions>
    </Dialog>
  );
}
