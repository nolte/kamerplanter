import { useEffect, useState } from 'react';
import { useTranslation } from 'react-i18next';
import { Link as RouterLink } from 'react-router-dom';
import Alert from '@mui/material/Alert';
import Box from '@mui/material/Box';
import Button from '@mui/material/Button';
import Card from '@mui/material/Card';
import CardContent from '@mui/material/CardContent';
import Chip from '@mui/material/Chip';
import Dialog from '@mui/material/Dialog';
import DialogActions from '@mui/material/DialogActions';
import DialogContent from '@mui/material/DialogContent';
import DialogContentText from '@mui/material/DialogContentText';
import DialogTitle from '@mui/material/DialogTitle';
import MenuItem from '@mui/material/MenuItem';
import TextField from '@mui/material/TextField';
import Typography from '@mui/material/Typography';
import AddIcon from '@mui/icons-material/Add';
import ArrowForwardIcon from '@mui/icons-material/ArrowForward';
import LoadingSkeleton from '@/components/common/LoadingSkeleton';
import EmptyState from '@/components/common/EmptyState';
import { useNotification } from '@/hooks/useNotification';
import { useApiError } from '@/hooks/useApiError';
import * as familiesApi from '@/api/endpoints/botanicalFamilies';
import * as rotationApi from '@/api/endpoints/cropRotation';
import type { BotanicalFamily, RotationSuccessor } from '@/api/types';
import { kamiMasterdata } from '@/assets/brand/illustrations';

interface SpeciesCropRotationTabProps {
  familyKey: string | null | undefined;
  fullScreen: boolean;
}

/**
 * Crop-rotation (Fruchtfolge) tab — expert-only (U-4). Self-contained: loads the
 * current family and its successors when it mounts (i.e. when the tab becomes
 * active) provided the species has a family, matching the former tab-activation
 * effect.
 */
export default function SpeciesCropRotationTab({
  familyKey,
  fullScreen,
}: SpeciesCropRotationTabProps) {
  const { t } = useTranslation();
  const notification = useNotification();
  const { handleError } = useApiError();

  const [currentFamily, setCurrentFamily] = useState<BotanicalFamily | null>(null);
  const [rotationSuccessors, setRotationSuccessors] = useState<RotationSuccessor[]>([]);
  const [rotationLoading, setRotationLoading] = useState(false);
  const [rotationDialogOpen, setRotationDialogOpen] = useState(false);
  const [rotationFamilies, setRotationFamilies] = useState<BotanicalFamily[]>([]);
  const [rotationFamiliesLoaded, setRotationFamiliesLoaded] = useState(false);
  const [rotationTargetKey, setRotationTargetKey] = useState('');
  const [rotationWaitYears, setRotationWaitYears] = useState(3);

  useEffect(() => {
    if (familyKey) {
      setRotationLoading(true);
      familiesApi
        .getBotanicalFamily(familyKey)
        .then(setCurrentFamily)
        .catch(() => {});
      rotationApi
        .getSuccessors(familyKey)
        .then(setRotationSuccessors)
        .catch((err) => handleError(err))
        .finally(() => setRotationLoading(false));
    }
  }, [familyKey, handleError]);

  const openRotationDialog = () => {
    if (!rotationFamiliesLoaded) {
      familiesApi
        .listAllBotanicalFamilies()
        .then((f) => {
          setRotationFamilies(f);
          setRotationFamiliesLoaded(true);
        })
        .catch(() => {});
    }
    setRotationDialogOpen(true);
  };

  const handleAddRotationSuccessor = async () => {
    if (!familyKey || !rotationTargetKey) return;
    try {
      await rotationApi.setSuccessor({
        from_family_key: familyKey,
        to_family_key: rotationTargetKey,
        wait_years: rotationWaitYears,
      });
      notification.success(t('common.create'));
      const updated = await rotationApi.getSuccessors(familyKey);
      setRotationSuccessors(updated);
    } catch (err) {
      handleError(err);
    }
    setRotationDialogOpen(false);
    setRotationTargetKey('');
  };

  return (
    <Box sx={{ maxWidth: 800 }}>
      {!familyKey ? (
        <Alert severity="info" data-testid="no-family-alert">
          {t('pages.species.noFamilyForCropRotation')}
        </Alert>
      ) : (
        <>
          <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
            {t('pages.species.cropRotationIntro')}
          </Typography>

          {/* Current family card — clickable */}
          <Card
            variant="outlined"
            component={RouterLink}
            to={`/stammdaten/botanical-families/${familyKey}`}
            sx={{
              mb: 3,
              display: 'block',
              textDecoration: 'none',
              transition: 'border-color 0.15s, box-shadow 0.15s',
              '&:hover': { borderColor: 'primary.main', boxShadow: 1 },
            }}
            data-testid="family-card-link"
          >
            <CardContent
              sx={{
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
                py: 1.5,
                '&:last-child': { pb: 1.5 },
              }}
            >
              <Box>
                <Typography
                  variant="caption"
                  color="text.secondary"
                  sx={{ textTransform: 'uppercase', letterSpacing: 0.6 }}
                >
                  {t('pages.species.family')}
                </Typography>
                <Typography variant="h6" color="text.primary" sx={{ mt: 0.25, lineHeight: 1.3 }}>
                  {currentFamily?.name ?? '…'}
                </Typography>
                {currentFamily?.common_name_de && (
                  <Typography variant="body2" color="text.secondary">
                    {currentFamily.common_name_de}
                  </Typography>
                )}
                {currentFamily?.rotation_category && (
                  <Chip
                    label={currentFamily.rotation_category}
                    size="small"
                    variant="outlined"
                    sx={{ mt: 0.75 }}
                  />
                )}
              </Box>
              <ArrowForwardIcon color="action" />
            </CardContent>
          </Card>

          {rotationLoading && <LoadingSkeleton variant="card" />}

          {!rotationLoading && (
            <Box>
              <Box
                sx={{
                  display: 'flex',
                  justifyContent: 'space-between',
                  alignItems: 'center',
                  mb: 2,
                }}
              >
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                  <Typography variant="subtitle2" color="text.secondary">
                    {t('pages.cropRotation.successorsTitle')}
                  </Typography>
                  {rotationSuccessors.length > 0 && (
                    <Chip label={rotationSuccessors.length} size="small" variant="outlined" />
                  )}
                </Box>
                <Button
                  variant="outlined"
                  size="small"
                  startIcon={<AddIcon />}
                  onClick={openRotationDialog}
                  data-testid="add-successor-button"
                >
                  {t('pages.cropRotation.addSuccessor')}
                </Button>
              </Box>

              {rotationSuccessors.length === 0 ? (
                <EmptyState
                  illustration={kamiMasterdata}
                  message={t('pages.cropRotation.noSuccessors')}
                  actionLabel={t('pages.cropRotation.addSuccessor')}
                  onAction={openRotationDialog}
                />
              ) : (
                <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1.5 }}>
                  {rotationSuccessors.map((s) => (
                    <Card
                      key={s.family_key}
                      variant="outlined"
                      component={RouterLink}
                      to={`/stammdaten/botanical-families/${s.family_key}`}
                      sx={{
                        display: 'block',
                        textDecoration: 'none',
                        transition: 'border-color 0.15s, box-shadow 0.15s',
                        '&:hover': { borderColor: 'primary.main', boxShadow: 1 },
                      }}
                    >
                      <CardContent
                        sx={{
                          display: 'flex',
                          alignItems: 'center',
                          justifyContent: 'space-between',
                          py: 1.25,
                          '&:last-child': { pb: 1.25 },
                        }}
                      >
                        <Box sx={{ flex: 1, minWidth: 0 }}>
                          <Typography variant="body1" color="text.primary" sx={{ fontWeight: 500 }}>
                            {s.name ?? s.family_key}
                          </Typography>
                          {s.benefit_reason && (
                            <Typography
                              variant="caption"
                              color="text.secondary"
                              sx={{ display: 'block', mt: 0.25 }}
                            >
                              {s.benefit_reason}
                            </Typography>
                          )}
                        </Box>
                        <Box
                          sx={{
                            display: 'flex',
                            alignItems: 'center',
                            gap: 1,
                            ml: 2,
                            flexShrink: 0,
                          }}
                        >
                          <Chip
                            label={`${s.wait_years} ${t('pages.cropRotation.waitYears')}`}
                            size="small"
                            color={
                              s.wait_years <= 1 ? 'success' : s.wait_years <= 3 ? 'warning' : 'error'
                            }
                            variant="outlined"
                          />
                          <ArrowForwardIcon fontSize="small" color="action" />
                        </Box>
                      </CardContent>
                    </Card>
                  ))}
                </Box>
              )}
            </Box>
          )}

          {/* Crop rotation dialog */}
          <Dialog
            fullScreen={fullScreen}
            open={rotationDialogOpen}
            onClose={() => setRotationDialogOpen(false)}
            maxWidth="sm"
            fullWidth
          >
            <DialogTitle>{t('pages.cropRotation.addSuccessor')}</DialogTitle>
            <DialogContent>
              <DialogContentText sx={{ mb: 2 }}>
                {t('pages.cropRotation.addSuccessorHint')}
              </DialogContentText>
              <TextField
                select
                fullWidth
                label={t('pages.cropRotation.toFamily')}
                value={rotationTargetKey}
                onChange={(e) => setRotationTargetKey(e.target.value)}
                helperText={t('pages.cropRotation.toFamilyHelper')}
                sx={{ mt: 1, mb: 2 }}
                data-testid="to-family-select"
              >
                {rotationFamilies
                  .filter((f) => f.key !== familyKey)
                  .map((f) => (
                    <MenuItem key={f.key} value={f.key}>
                      {f.name}
                    </MenuItem>
                  ))}
              </TextField>
              <TextField
                type="number"
                label={t('pages.cropRotation.waitYears')}
                value={rotationWaitYears}
                onChange={(e) => setRotationWaitYears(Number(e.target.value))}
                fullWidth
                helperText={t('pages.cropRotation.waitYearsHelper')}
                slotProps={{ htmlInput: { min: 1, max: 10 } }}
                data-testid="wait-years-input"
              />
            </DialogContent>
            <DialogActions>
              <Button onClick={() => setRotationDialogOpen(false)}>{t('common.cancel')}</Button>
              <Button
                variant="contained"
                onClick={handleAddRotationSuccessor}
                disabled={!rotationTargetKey}
              >
                {t('common.create')}
              </Button>
            </DialogActions>
          </Dialog>
        </>
      )}
    </Box>
  );
}
