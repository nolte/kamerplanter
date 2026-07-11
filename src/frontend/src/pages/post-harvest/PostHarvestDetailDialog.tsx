import { useEffect, useMemo, useState } from 'react';
import { useTranslation } from 'react-i18next';
import Dialog from '@mui/material/Dialog';
import DialogTitle from '@mui/material/DialogTitle';
import DialogContent from '@mui/material/DialogContent';
import DialogActions from '@mui/material/DialogActions';
import Button from '@mui/material/Button';
import Box from '@mui/material/Box';
import Stack from '@mui/material/Stack';
import Chip from '@mui/material/Chip';
import Alert from '@mui/material/Alert';
import Typography from '@mui/material/Typography';
import LinearProgress from '@mui/material/LinearProgress';
import TextField from '@mui/material/TextField';
import useMediaQuery from '@mui/material/useMediaQuery';
import { useTheme } from '@mui/material/styles';
import { useAppDispatch, useAppSelector } from '@/store/hooks';
import {
  fetchPostHarvestBatch,
  advancePostHarvestStage,
  recordDryingProgress,
  clearCurrentDetail,
} from '@/store/slices/postHarvestSlice';
import { useNotification } from '@/hooks/useNotification';
import { useApiError } from '@/hooks/useApiError';
import type { PostHarvestStage } from '@/api/types';

const STAGE_ORDER: PostHarvestStage[] = ['drying', 'curing', 'stored', 'released'];

type ChipColor = 'default' | 'info' | 'success' | 'warning';

const STAGE_COLOR: Record<PostHarvestStage, ChipColor> = {
  drying: 'info',
  curing: 'warning',
  stored: 'success',
  released: 'default',
};

function nextStage(stage: PostHarvestStage): PostHarvestStage | null {
  const idx = STAGE_ORDER.indexOf(stage);
  return idx >= 0 && idx + 1 < STAGE_ORDER.length ? STAGE_ORDER[idx + 1] : null;
}

interface Props {
  batchKey: string | null;
  onClose: () => void;
  onChanged: () => void;
}

export default function PostHarvestDetailDialog({ batchKey, onClose, onChanged }: Props) {
  const theme = useTheme();
  const fullScreen = useMediaQuery(theme.breakpoints.down('sm'));
  const { t } = useTranslation();
  const dispatch = useAppDispatch();
  const notification = useNotification();
  const { handleError } = useApiError();
  const detail = useAppSelector((s) => s.postHarvest.currentDetail);
  const [currentWeight, setCurrentWeight] = useState('');
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    if (batchKey) {
      dispatch(fetchPostHarvestBatch(batchKey));
    } else {
      dispatch(clearCurrentDetail());
    }
  }, [batchKey, dispatch]);

  const batch = detail?.batch ?? null;
  const target = batch ? nextStage(batch.stage) : null;
  const isDrying = batch?.stage === 'drying';
  const advanceBlocked = useMemo(
    () => isDrying && target === 'curing' && !batch?.ready_for_curing,
    [isDrying, target, batch?.ready_for_curing],
  );

  const handleAdvance = async () => {
    if (!batch || !target) return;
    try {
      setBusy(true);
      await dispatch(advancePostHarvestStage({ key: batch.key, targetStage: target })).unwrap();
      notification.success(t('pages.postHarvest.advanceSuccess'));
      onChanged();
    } catch (err) {
      handleError(err);
    } finally {
      setBusy(false);
    }
  };

  const handleRecordWeight = async () => {
    if (!batch) return;
    const weight = Number(currentWeight);
    if (!Number.isFinite(weight) || weight <= 0) return;
    try {
      setBusy(true);
      await dispatch(
        recordDryingProgress({ key: batch.key, payload: { current_weight_g: weight } }),
      ).unwrap();
      notification.success(t('pages.postHarvest.progressRecorded'));
      setCurrentWeight('');
      onChanged();
    } catch (err) {
      handleError(err);
    } finally {
      setBusy(false);
    }
  };

  return (
    <Dialog
      fullScreen={fullScreen}
      open={batchKey !== null}
      onClose={onClose}
      maxWidth="sm"
      fullWidth
      aria-labelledby="post-harvest-detail-title"
      data-testid="post-harvest-detail-dialog"
    >
      <DialogTitle id="post-harvest-detail-title">
        {t('pages.postHarvest.detailTitle')}
      </DialogTitle>
      <DialogContent dividers>
        {!batch ? (
          <Typography color="text.secondary">{t('common.loading')}</Typography>
        ) : (
          <Stack spacing={2}>
            <Stack direction="row" spacing={1} sx={{ alignItems: 'center', flexWrap: 'wrap' }}>
              <Chip
                label={t(`enums.postHarvestStage.${batch.stage}`)}
                color={STAGE_COLOR[batch.stage]}
                data-testid="stage-chip"
              />
              <Chip
                label={t(`enums.dryingMethod.${batch.drying_method}`)}
                variant="outlined"
                size="small"
              />
              <Chip
                label={t(`enums.postHarvestSpeciesType.${batch.species_type}`)}
                variant="outlined"
                size="small"
              />
            </Stack>

            <Box>
              <Typography variant="body2" color="text.secondary" gutterBottom>
                {t('pages.postHarvest.drynessProgress')}:{' '}
                {batch.dryness_progress_percent.toFixed(1)}%
              </Typography>
              <LinearProgress
                variant="determinate"
                value={Math.min(100, Math.max(0, batch.dryness_progress_percent))}
                color={batch.ready_for_curing ? 'success' : 'info'}
                aria-label={t('pages.postHarvest.drynessProgress')}
              />
            </Box>

            {detail && detail.open_mold_alerts > 0 && (
              <Alert severity="warning" data-testid="mold-alert-banner">
                {t('pages.postHarvest.openMoldAlerts', { count: detail.open_mold_alerts })}
              </Alert>
            )}

            {batch.stage === 'drying' && (
              <Box>
                <Typography variant="subtitle2" gutterBottom>
                  {t('pages.postHarvest.recordWeight')}
                </Typography>
                <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
                  {t('pages.postHarvest.recordWeightIntro')}
                </Typography>
                <Stack direction="row" spacing={1}>
                  <TextField
                    label={t('pages.postHarvest.currentWeightG')}
                    value={currentWeight}
                    onChange={(e) => setCurrentWeight(e.target.value)}
                    type="number"
                    size="small"
                    slotProps={{
                      htmlInput: {
                        min: 0,
                        step: 'any',
                        'aria-label': t('pages.postHarvest.currentWeightG'),
                      },
                    }}
                    data-testid="current-weight-input"
                  />
                  <Button
                    onClick={handleRecordWeight}
                    variant="outlined"
                    disabled={busy || currentWeight === ''}
                    data-testid="record-weight-button"
                  >
                    {t('pages.postHarvest.record')}
                  </Button>
                </Stack>
              </Box>
            )}

            {advanceBlocked && (
              <Alert severity="info">{t('pages.postHarvest.notReadyForCuring')}</Alert>
            )}
          </Stack>
        )}
      </DialogContent>
      <DialogActions>
        <Button onClick={onClose}>{t('common.close')}</Button>
        {batch && target && (
          <Button
            variant="contained"
            onClick={handleAdvance}
            disabled={busy || advanceBlocked}
            data-testid="advance-stage-button"
          >
            {t('pages.postHarvest.advanceTo', {
              stage: t(`enums.postHarvestStage.${target}`),
            })}
          </Button>
        )}
      </DialogActions>
    </Dialog>
  );
}
