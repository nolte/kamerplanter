import { useCallback, useId, useState } from 'react';
import { useTranslation } from 'react-i18next';
import { useNavigate } from 'react-router-dom';
import Dialog from '@mui/material/Dialog';
import DialogTitle from '@mui/material/DialogTitle';
import DialogContent from '@mui/material/DialogContent';
import DialogActions from '@mui/material/DialogActions';
import Box from '@mui/material/Box';
import Button from '@mui/material/Button';
import Alert from '@mui/material/Alert';
import Typography from '@mui/material/Typography';
import CircularProgress from '@mui/material/CircularProgress';
import LinearProgress from '@mui/material/LinearProgress';
import BugReportIcon from '@mui/icons-material/BugReport';
import ImageCapturePanel from '@/components/identification/ImageCapturePanel';
import PestFindingsResult from '@/components/pests/PestFindingsResult';
import { useExpertiseLevel } from '@/hooks/useExpertiseLevel';
import { useNotification } from '@/hooks/useNotification';
import { useAppDispatch, useAppSelector } from '@/store/hooks';
import { isLightMode } from '@/config/mode';
import { contributePestImage } from '@/api/endpoints/ipm';
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
  const notification = useNotification();
  const { level } = useExpertiseLevel();
  const status = useAppSelector((s) => s.pestDetection.status);
  const result = useAppSelector((s) => s.pestDetection.result);
  const detecting = useAppSelector((s) => s.pestDetection.detecting);
  const error = useAppSelector((s) => s.pestDetection.error);

  const [previewUrl, setPreviewUrl] = useState<string | null>(null);
  const [inspectionCreated, setInspectionCreated] = useState(false);
  // REQ-044 §8 — the captured photo is NOT persisted by the detection path
  // (only its hash). We keep the in-browser File so the user can, on a
  // deliberate action, contribute it to the pest gallery (no auto-save).
  const [capturedFile, setCapturedFile] = useState<File | null>(null);
  // Pest keys whose photo has already been added to the gallery (one CTA per
  // matched pest), plus the pest key whose upload is currently in flight.
  const [addedPestKeys, setAddedPestKeys] = useState<string[]>([]);
  const [addingPestKey, setAddingPestKey] = useState<string | null>(null);

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
    setCapturedFile(null);
    setAddedPestKeys([]);
    setAddingPestKey(null);
    onClose();
  }, [dispatch, onClose]);

  const handleImageReady = useCallback(
    (file: File, url: string) => {
      setPreviewUrl(url);
      setInspectionCreated(false);
      // Hold the File so it can later be contributed to the gallery on a
      // deliberate user action (it is never auto-persisted, §8).
      setCapturedFile(file);
      setAddedPestKeys([]);
      setAddingPestKey(null);
      dispatch(detectPests({ plantKey, image: file }));
    },
    [dispatch, plantKey],
  );

  const handleRetake = useCallback(() => {
    dispatch(resetPestDetection());
    setPreviewUrl(null);
    setInspectionCreated(false);
    setCapturedFile(null);
    setAddedPestKeys([]);
    setAddingPestKey(null);
  }, [dispatch]);

  const handleAddToGallery = useCallback(
    async (pestKey: string) => {
      if (!capturedFile) return;
      setAddingPestKey(pestKey);
      try {
        await contributePestImage(pestKey, capturedFile);
        setAddedPestKeys((prev) => (prev.includes(pestKey) ? prev : [...prev, pestKey]));
        notification.success(t('pages.pests.addToGallerySuccess'));
      } catch {
        notification.error(t('pages.pests.addToGalleryError'));
      } finally {
        setAddingPestKey(null);
      }
    },
    [capturedFile, notification, t],
  );

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
                <PestFindingsResult
                  result={result}
                  previewUrl={previewUrl}
                  level={level}
                  onFeedback={handleFeedback}
                  onViewPest={handleViewPest}
                  addedPestKeys={addedPestKeys}
                  addingPestKey={addingPestKey}
                  onAddToGallery={handleAddToGallery}
                  canAddToGallery={Boolean(capturedFile) && !cloudBlockedInLight}
                />

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
