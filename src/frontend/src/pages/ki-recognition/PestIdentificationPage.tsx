import { useCallback, useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import Box from '@mui/material/Box';
import Button from '@mui/material/Button';
import Alert from '@mui/material/Alert';
import Card from '@mui/material/Card';
import CardContent from '@mui/material/CardContent';
import Typography from '@mui/material/Typography';
import CircularProgress from '@mui/material/CircularProgress';
import LinearProgress from '@mui/material/LinearProgress';
import PageTitle from '@/components/layout/PageTitle';
import { useTenantPermissions } from '@/hooks/useTenantPermissions';
import LoadingSkeleton from '@/components/common/LoadingSkeleton';
import ImageCapturePanel from '@/components/identification/ImageCapturePanel';
import PestFindingsResult from '@/components/pests/PestFindingsResult';
import { useExpertiseLevel } from '@/hooks/useExpertiseLevel';
import { useNotification } from '@/hooks/useNotification';
import { useAppDispatch, useAppSelector } from '@/store/hooks';
import { isLightMode } from '@/config/mode';
import { contributePestImage } from '@/api/endpoints/ipm';
import {
  detectPestsGlobal,
  fetchPestDetectionStatus,
  resetPestDetection,
  submitPestFeedback,
} from '@/store/slices/pestDetectionSlice';
import type { PestFinding } from '@/api/types';

/**
 * REQ-044 §7 — standalone, plant-agnostic pest-detection page.
 *
 * Mirrors the plant identification page (own navigation entry, own flow) but for
 * pests: capture/upload a photo → global detect (no plant binding) → render the
 * shared {@link PestFindingsResult} (disclaimer always visible, abstention,
 * beneficial hint, findings with HITL feedback + bounding boxes, pest-detail
 * link, opt-in "add to gallery"). The plant-bound actions (create inspection,
 * history) are intentionally omitted; a hint points to the plant page for
 * documenting a finding on a specific plant. Never triggers a treatment.
 *
 * Gating mirrors PestScanButton: the feature must be available and, for
 * consent-bound cloud adapters, light mode blocks the page.
 */
export default function PestIdentificationPage() {
  const { t } = useTranslation();
  const dispatch = useAppDispatch();
  const navigate = useNavigate();
  const notification = useNotification();
  const { level } = useExpertiseLevel();

  const status = useAppSelector((s) => s.pestDetection.status);
  const statusLoading = useAppSelector((s) => s.pestDetection.statusLoading);
  const result = useAppSelector((s) => s.pestDetection.result);
  const detecting = useAppSelector((s) => s.pestDetection.detecting);
  const error = useAppSelector((s) => s.pestDetection.error);

  const [previewUrl, setPreviewUrl] = useState<string | null>(null);
  // REQ-044 §8 — the photo is never auto-persisted; we keep the File so the user
  // can deliberately contribute it to a matched pest's gallery.
  const [capturedFile, setCapturedFile] = useState<File | null>(null);
  const [addedPestKeys, setAddedPestKeys] = useState<string[]>([]);
  const [addingPestKey, setAddingPestKey] = useState<string | null>(null);

  useEffect(() => {
    // Fetch the feature status once (mirrors PestScanButton): if it was already
    // loaded elsewhere we keep it, so the page does not flash a loading state.
    if (status == null) {
      dispatch(fetchPestDetectionStatus());
    }
  }, [dispatch, status]);

  useEffect(() => {
    // Reset any in-flight result from a previous (plant-bound) flow on unmount.
    return () => {
      dispatch(resetPestDetection());
    };
  }, [dispatch]);

  const available = status?.available ?? false;
  // Self-hosted / demo adapters work in light mode; only the consent-bound cloud
  // path is blocked there (§3.3) — same logic as PestScanButton.
  const active = status?.active_adapter;
  const activeRequiresConsent = active != null && status?.adapters?.[active]?.requires_consent != null;
  const cloudBlockedInLight = isLightMode && activeRequiresConsent;
  // #1333 — the server now refuses `POST /pests/detect` below grower, so the
  // capture panel must not be reachable by a viewer. This is an *action-level*
  // gate rather than a `<RequireRole>` route wrapper on purpose: this page has
  // no read body at all (§7 omits history deliberately), so the wrapper's
  // restrict-only mode would hide the retake button, leave the capture panel
  // standing, and let a viewer walk into the 403 anyway — a guard that is
  // visible and inert, which `roleGuardedRoutes.ts` names as worse than none.
  // "No active tenant yet" is not a refusal (the same reading as `RequireRole`
  // and `useCanCreateCatalogEntry`): in light mode the status request resolves
  // before `loadMyTenants` does, and in full mode the stale-slug recovery nulls
  // the tenant for a moment — neither may flash the role notice at a lead.
  const { canEdit, hasTenant } = useTenantPermissions();
  const roleRestricted = hasTenant && !canEdit;
  const accessible = available && !cloudBlockedInLight && !roleRestricted;

  const handleImageReady = useCallback(
    (file: File, url: string) => {
      setPreviewUrl(url);
      setCapturedFile(file);
      setAddedPestKeys([]);
      setAddingPestKey(null);
      dispatch(detectPestsGlobal({ image: file }));
    },
    [dispatch],
  );

  const handleRetake = useCallback(() => {
    dispatch(resetPestDetection());
    setPreviewUrl(null);
    setCapturedFile(null);
    setAddedPestKeys([]);
    setAddingPestKey(null);
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

  const handleViewPest = useCallback(
    (pestKey: string) => {
      navigate(`/pflanzenschutz/pests/${pestKey}`);
    },
    [navigate],
  );

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

  return (
    <Box sx={{ p: { xs: 2, sm: 3 } }} data-testid="pest-identification-page">
      <PageTitle
        title={t('pages.pestIdentification.title')}
        action={
          accessible && result ? (
            <Button
              variant="outlined"
              onClick={handleRetake}
              data-testid="pest-identification-retake"
              sx={{ minHeight: { xs: 48, sm: 40 } }}
            >
              {t('pages.pests.retake')}
            </Button>
          ) : undefined
        }
      />

      {/* Page intro — explains what the feature does before any gating. */}
      <Typography variant="body1" color="text.secondary" sx={{ mb: 3, maxWidth: '72ch' }}>
        {t('pages.pestIdentification.pageIntro')}
      </Typography>

      {/* Disclaimer is ALWAYS visible (§7/§8). */}
      <Alert severity="info" sx={{ mb: 3 }} data-testid="pest-disclaimer">
        {result?.disclaimer || t('pages.pests.disclaimer')}
      </Alert>

      {statusLoading ? (
        <LoadingSkeleton variant="card" />
      ) : cloudBlockedInLight ? (
        <Alert severity="info" data-testid="pest-light-mode">
          {t('pages.pests.lightModeBlocked')}
        </Alert>
      ) : !available ? (
        <Alert severity="info" data-testid="page-feature-unavailable">
          {t('pages.pests.notConfigured')}
        </Alert>
      ) : roleRestricted ? (
        <Alert severity="info" data-testid="pest-identification-role-restricted">
          {t('pages.pests.roleRestricted')}
        </Alert>
      ) : (
        <Card variant="outlined">
          <CardContent>
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
              <>
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

                {/* Plant-bound documentation is intentionally out of scope here —
                    point the user to the per-plant entry point instead. */}
                <Alert severity="info" variant="outlined" sx={{ mt: 2 }} data-testid="pest-identification-plant-hint">
                  {t('pages.pestIdentification.plantHint')}
                </Alert>

                <Button
                  variant="text"
                  onClick={handleRetake}
                  data-testid="pest-identification-retake-inline"
                  sx={{ mt: 2, minHeight: 44 }}
                >
                  {t('pages.pests.retake')}
                </Button>
              </>
            )}
          </CardContent>
        </Card>
      )}
    </Box>
  );
}
