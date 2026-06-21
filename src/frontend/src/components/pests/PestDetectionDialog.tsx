import { useCallback, useId, useMemo, useState } from 'react';
import { useTranslation } from 'react-i18next';
import { useNavigate } from 'react-router-dom';
import Dialog from '@mui/material/Dialog';
import DialogTitle from '@mui/material/DialogTitle';
import DialogContent from '@mui/material/DialogContent';
import DialogActions from '@mui/material/DialogActions';
import Box from '@mui/material/Box';
import Button from '@mui/material/Button';
import Alert from '@mui/material/Alert';
import Stack from '@mui/material/Stack';
import Typography from '@mui/material/Typography';
import Chip from '@mui/material/Chip';
import Divider from '@mui/material/Divider';
import CircularProgress from '@mui/material/CircularProgress';
import LinearProgress from '@mui/material/LinearProgress';
import Tooltip from '@mui/material/Tooltip';
import BugReportIcon from '@mui/icons-material/BugReport';
import FavoriteIcon from '@mui/icons-material/Favorite';
import ImageCapturePanel from '@/components/identification/ImageCapturePanel';
import { useExpertiseLevel } from '@/hooks/useExpertiseLevel';
import { useAppDispatch, useAppSelector } from '@/store/hooks';
import { isLightMode } from '@/config/mode';
import {
  createInspectionFromDetection,
  detectPests,
  fetchPestDetectionHistory,
  resetPestDetection,
  submitPestFeedback,
} from '@/store/slices/pestDetectionSlice';
import type { PestFinding } from '@/api/types';

interface PestDetectionDialogProps {
  open: boolean;
  onClose: () => void;
  plantKey: string;
}

/**
 * REQ-044 §7 — pest detection dialog with the two modes (direct + symptom).
 *
 * Renders bounding-box overlays for direct findings, a disclaimer banner that is
 * always visible, abstention and beneficial hints, a findings list (beginner:
 * top finding only) with HITL feedback, and a "create inspection" CTA. Never
 * triggers a treatment.
 */
export default function PestDetectionDialog({ open, onClose, plantKey }: PestDetectionDialogProps) {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const dispatch = useAppDispatch();
  const { level } = useExpertiseLevel();
  const status = useAppSelector((s) => s.pestDetection.status);
  const result = useAppSelector((s) => s.pestDetection.result);
  const detecting = useAppSelector((s) => s.pestDetection.detecting);
  const error = useAppSelector((s) => s.pestDetection.error);

  const [previewUrl, setPreviewUrl] = useState<string | null>(null);
  const [inspectionCreated, setInspectionCreated] = useState(false);

  // Stable IDs for aria-labelledby / aria-describedby
  const titleId = useId();
  const descId = useId();

  const available = status?.available ?? false;
  // Self-hosted / demo adapters work in light mode; only the cloud path (which
  // needs consent) is blocked there (§3.3).
  const active = status?.active_adapter;
  const activeRequiresConsent = active != null && status?.adapters?.[active]?.requires_consent != null;
  const cloudBlockedInLight = isLightMode && activeRequiresConsent;

  const handleClose = useCallback(() => {
    dispatch(resetPestDetection());
    setPreviewUrl(null);
    setInspectionCreated(false);
    onClose();
  }, [dispatch, onClose]);

  const handleImageReady = useCallback(
    (file: File, url: string) => {
      setPreviewUrl(url);
      setInspectionCreated(false);
      dispatch(detectPests({ plantKey, image: file }));
    },
    [dispatch, plantKey],
  );

  const handleRetake = useCallback(() => {
    dispatch(resetPestDetection());
    setPreviewUrl(null);
    setInspectionCreated(false);
  }, [dispatch]);

  const handleFeedback = useCallback(
    (finding: PestFinding, confirmed: boolean, wasBeneficial = false) => {
      if (!result?.key) return;
      dispatch(
        submitPestFeedback({
          detectionKey: result.key,
          findingLabel: finding.label,
          confirmed,
          wasBeneficial,
        }),
      );
    },
    [dispatch, result],
  );

  const handleCreateInspection = useCallback(async () => {
    if (!result?.key) return;
    const action = await dispatch(createInspectionFromDetection({ detectionKey: result.key, plantKey }));
    if (createInspectionFromDetection.fulfilled.match(action)) {
      setInspectionCreated(true);
      dispatch(fetchPestDetectionHistory({ plantKey }));
    }
  }, [dispatch, result, plantKey]);

  const handleViewPest = useCallback(
    (pestKey: string) => {
      handleClose();
      navigate(`/pflanzenschutz/pests/${pestKey}`);
    },
    [handleClose, navigate],
  );

  const directFindings = useMemo(
    () => (result?.findings ?? []).filter((f) => f.bounding_box != null),
    [result],
  );

  const visibleFindings = useMemo(() => {
    const findings = result?.findings ?? [];
    return level === 'beginner' ? findings.slice(0, 1) : findings;
  }, [result, level]);

  const hasBeneficial = useMemo(
    () => (result?.findings ?? []).some((f) => f.category === 'beneficial'),
    [result],
  );

  return (
    <Dialog
      open={open}
      onClose={handleClose}
      maxWidth="sm"
      fullWidth
      data-testid="pest-detection-dialog"
      aria-labelledby={titleId}
      aria-describedby={descId}
    >
      <DialogTitle id={titleId}>{t('pages.pests.title')}</DialogTitle>
      <DialogContent dividers>
        {/* Hidden accessible description for screen readers */}
        <Typography id={descId} sx={{ display: 'none' }}>
          {t('pages.pests.dialogDescription')}
        </Typography>

        {/* Disclaimer is ALWAYS visible (§7/§8). */}
        <Alert severity="info" sx={{ mb: 2 }} data-testid="pest-disclaimer">
          {result?.disclaimer || t('pages.pests.disclaimer')}
        </Alert>

        {cloudBlockedInLight ? (
          <Alert severity="info" data-testid="pest-light-mode">
            {t('pages.pests.lightModeBlocked')}
          </Alert>
        ) : !available ? (
          <Alert severity="info" data-testid="pest-not-available">
            {t('pages.pests.notConfigured')}
          </Alert>
        ) : (
          <>
            {!result && !detecting && (
              <ImageCapturePanel onImageReady={handleImageReady} level={level} disabled={detecting} />
            )}

            {detecting && (
              <Box sx={{ textAlign: 'center', py: 3 }} aria-live="polite" aria-busy="true">
                <CircularProgress aria-hidden="true" />
                <Typography sx={{ mt: 2 }}>{t('pages.pests.analyzing')}</Typography>
                <LinearProgress sx={{ mt: 2 }} aria-hidden="true" />
              </Box>
            )}

            {error && (
              <Alert severity="error" sx={{ mt: 2 }} data-testid="pest-error" role="alert">
                {error}
              </Alert>
            )}

            {result && (
              <Box sx={{ mt: 1 }} aria-live="polite">
                {/* Box overlay for direct findings (Mode 1). */}
                {previewUrl && (
                  <Box
                    sx={{ position: 'relative', mb: 2, lineHeight: 0 }}
                    data-testid="pest-preview"
                    role="img"
                    aria-label={t('pages.pests.previewAlt')}
                  >
                    <Box
                      component="img"
                      src={previewUrl}
                      alt=""
                      aria-hidden="true"
                      sx={{ width: '100%', borderRadius: 1, display: 'block' }}
                    />
                    {directFindings.map((f, i) => (
                      <Tooltip
                        key={`${f.label}-${i}`}
                        title={t('pages.pests.boundingBoxLabel', { name: f.common_name })}
                        placement="top"
                      >
                        <Box
                          data-testid="pest-bounding-box"
                          role="img"
                          aria-label={t('pages.pests.boundingBoxLabel', { name: f.common_name })}
                          tabIndex={0}
                          sx={{
                            position: 'absolute',
                            left: `${(f.bounding_box?.x ?? 0) * 100}%`,
                            top: `${(f.bounding_box?.y ?? 0) * 100}%`,
                            width: `${(f.bounding_box?.width ?? 0) * 100}%`,
                            height: `${(f.bounding_box?.height ?? 0) * 100}%`,
                            border: '2px solid',
                            borderColor: f.category === 'beneficial' ? 'success.main' : 'warning.main',
                            borderRadius: 0.5,
                            cursor: 'default',
                            '&:focus-visible': {
                              outline: '2px solid',
                              outlineColor: 'primary.main',
                              outlineOffset: '2px',
                            },
                          }}
                        >
                          {/* Text label in the top-left corner of the box — visible in addition to the border colour */}
                          <Typography
                            variant="caption"
                            sx={{
                              position: 'absolute',
                              top: 0,
                              left: 0,
                              px: 0.5,
                              lineHeight: 1.4,
                              bgcolor: f.category === 'beneficial' ? 'success.main' : 'warning.main',
                              color: 'common.white',
                              borderRadius: '0 0 4px 0',
                              maxWidth: '100%',
                              overflow: 'hidden',
                              whiteSpace: 'nowrap',
                              textOverflow: 'ellipsis',
                            }}
                          >
                            {f.common_name}
                          </Typography>
                        </Box>
                      </Tooltip>
                    ))}
                  </Box>
                )}

                {/* Abstention (§4.3 / Szenario 2). */}
                {!result.is_confident && (
                  <Alert severity="warning" sx={{ mb: 2 }} data-testid="pest-abstain">
                    {t('pages.pests.abstain')}
                  </Alert>
                )}

                {/* Beneficial hint (§9.1 / Szenario 3). */}
                {hasBeneficial && (
                  <Alert severity="success" icon={<FavoriteIcon />} sx={{ mb: 2 }} data-testid="pest-beneficial">
                    {t('pages.pests.beneficial')}
                  </Alert>
                )}

                {/* No findings (still not proof of pest-freeness, §7.1). */}
                {result.findings.length === 0 && (
                  <Alert severity="info" sx={{ mb: 2 }} data-testid="pest-no-findings">
                    {t('pages.pests.noFindings')}
                  </Alert>
                )}

                {visibleFindings.length > 0 && (
                  <Stack
                    spacing={1}
                    divider={<Divider flexItem />}
                    component="ul"
                    sx={{ listStyle: 'none', p: 0, m: 0 }}
                  >
                    {visibleFindings.map((f, i) => (
                      <Box
                        key={`${f.label}-${i}`}
                        component="li"
                        data-testid="pest-finding"
                        aria-label={t('pages.pests.findingAriaLabel', {
                          index: i + 1,
                          name: f.common_name,
                          category: t(`enums.pestCategory.${f.category}`),
                          confidence: Math.round(f.confidence * 100),
                        })}
                      >
                        <Stack
                          direction="row"
                          spacing={1}
                          sx={{ alignItems: 'center', flexWrap: 'wrap', mb: f.category !== 'beneficial' ? 1 : 0 }}
                        >
                          <Typography variant="subtitle2">{f.common_name}</Typography>
                          <Chip
                            size="small"
                            color={f.category === 'beneficial' ? 'success' : 'default'}
                            label={t(`enums.pestCategory.${f.category}`)}
                          />
                          <Chip size="small" variant="outlined" label={t(`enums.pestMode.${f.mode}`)} />
                          <Typography
                            variant="caption"
                            color="text.secondary"
                            aria-label={t('pages.pests.confidenceLabel', {
                              value: Math.round(f.confidence * 100),
                            })}
                          >
                            {t('pages.pests.confidence')}: {Math.round(f.confidence * 100)}&nbsp;%
                          </Typography>
                        </Stack>
                        {f.matched_pest_key && (
                          <Button
                            size="small"
                            variant="text"
                            onClick={() => handleViewPest(f.matched_pest_key as string)}
                            data-testid="pest-finding-detail-link"
                            sx={{ px: 0, mb: f.category !== 'beneficial' ? 1 : 0 }}
                          >
                            {t('pages.pests.viewPestDetail')}
                          </Button>
                        )}
                        {f.category !== 'beneficial' && (
                          <Stack direction="row" spacing={1} sx={{ flexWrap: 'wrap', gap: 1 }}>
                            <Button
                              size="small"
                              variant="outlined"
                              onClick={() => handleFeedback(f, true)}
                              data-testid="pest-feedback-confirm"
                              aria-label={t('pages.pests.feedbackConfirmAriaLabel')}
                              sx={{ minHeight: 44 }}
                            >
                              {t('pages.pests.feedbackConfirm')}
                            </Button>
                            <Button
                              size="small"
                              variant="outlined"
                              onClick={() => handleFeedback(f, false)}
                              data-testid="pest-feedback-wrong"
                              aria-label={t('pages.pests.feedbackWrongAriaLabel')}
                              sx={{ minHeight: 44 }}
                            >
                              {t('pages.pests.feedbackWrong')}
                            </Button>
                            <Button
                              size="small"
                              variant="outlined"
                              color="success"
                              onClick={() => handleFeedback(f, false, true)}
                              data-testid="pest-feedback-beneficial"
                              aria-label={t('pages.pests.feedbackBeneficialAriaLabel')}
                              sx={{ minHeight: 44 }}
                            >
                              {t('pages.pests.feedbackBeneficial')}
                            </Button>
                          </Stack>
                        )}
                      </Box>
                    ))}
                  </Stack>
                )}

                {/* Next-step CTA → IPM inspection (never a treatment, §0). */}
                {result.suggested_next_step === 'ipm_inspection' && !inspectionCreated && (
                  <Button
                    fullWidth
                    variant="contained"
                    startIcon={<BugReportIcon />}
                    sx={{ mt: 2, minHeight: 48 }}
                    onClick={handleCreateInspection}
                    data-testid="pest-create-inspection"
                  >
                    {t('pages.pests.createInspection')}
                  </Button>
                )}
                {inspectionCreated && (
                  <Alert severity="success" sx={{ mt: 2 }} data-testid="pest-inspection-created" role="status">
                    {t('pages.pests.inspectionCreated')}
                  </Alert>
                )}
              </Box>
            )}
          </>
        )}
      </DialogContent>
      <DialogActions>
        {result && !cloudBlockedInLight && available && (
          <Button onClick={handleRetake} data-testid="pest-retake" sx={{ minHeight: 44 }}>
            {t('pages.pests.retake')}
          </Button>
        )}
        <Button onClick={handleClose} sx={{ minHeight: 44 }}>
          {t('common.close')}
        </Button>
      </DialogActions>
    </Dialog>
  );
}
