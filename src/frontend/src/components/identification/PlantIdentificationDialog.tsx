import { useCallback, useEffect, useRef, useState } from 'react';
import { useTranslation } from 'react-i18next';
import Dialog from '@mui/material/Dialog';
import DialogTitle from '@mui/material/DialogTitle';
import DialogContent from '@mui/material/DialogContent';
import DialogActions from '@mui/material/DialogActions';
import Box from '@mui/material/Box';
import Button from '@mui/material/Button';
import IconButton from '@mui/material/IconButton';
import Typography from '@mui/material/Typography';
import Alert from '@mui/material/Alert';
import Chip from '@mui/material/Chip';
import Stack from '@mui/material/Stack';
import Tooltip from '@mui/material/Tooltip';
import CircularProgress from '@mui/material/CircularProgress';
import useMediaQuery from '@mui/material/useMediaQuery';
import { useTheme } from '@mui/material/styles';
import CloseIcon from '@mui/icons-material/Close';
import ReplayIcon from '@mui/icons-material/Replay';
import InfoOutlinedIcon from '@mui/icons-material/InfoOutlined';
import { useAppDispatch, useAppSelector } from '@/store/hooks';
import {
  fetchIdentificationStatus,
  identifyPlant,
  resetIdentification,
  selectIdentificationResult,
} from '@/store/slices/identificationSlice';
import { useExpertiseLevel } from '@/hooks/useExpertiseLevel';
import { useNotification } from '@/hooks/useNotification';
import { useApiError } from '@/hooks/useApiError';
import { listConsents, grantConsent } from '@/api/endpoints/privacy';
import { parseApiError } from '@/api/errors';
import { isLightMode } from '@/config/mode';
import * as speciesApi from '@/api/endpoints/species';
import ImageCapturePanel from './ImageCapturePanel';
import SuggestionList from './SuggestionList';
import IdentificationConsentGate from './IdentificationConsentGate';
import type { PlantOrgan } from '@/api/types';

const CONSENT_PURPOSE = 'plant_identification';

/**
 * REQ-027 — Light-mode consent flag.
 *
 * In the Light mode there is no backend consent subsystem (the `privacy_router`
 * is not registered, so `GET /api/v1/privacy/consents` returns 404). The opt-in
 * for the Pl@ntNet third-country transfer is therefore kept client-side under
 * this localStorage key. The transparency notice still appears before the first
 * upload; only the persistence of the decision differs from the full mode.
 */
const LIGHT_CONSENT_STORAGE_KEY = 'plant_identification_consent';

function readLightConsent(): boolean {
  try {
    return window.localStorage.getItem(LIGHT_CONSENT_STORAGE_KEY) === 'granted';
  } catch {
    return false;
  }
}

function writeLightConsent(): void {
  try {
    window.localStorage.setItem(LIGHT_CONSENT_STORAGE_KEY, 'granted');
  } catch {
    /* localStorage unavailable (private mode, etc.) — silent no-op. */
  }
}

const ORGAN_OPTIONS: PlantOrgan[] = ['auto', 'leaf', 'flower', 'fruit', 'bark', 'habit'];

export interface IdentifiedSpecies {
  /** Existing or newly created species key to attach the plant to. */
  speciesKey: string;
  scientificName: string;
  /**
   * The photo the user captured/uploaded for identification (issue #447).
   * Handed back so the downstream "create plant" step can reuse it as the
   * gallery cover and, in DINOv2 mode, as a few-shot recognition reference.
   * `undefined` when the flow was completed without a retained capture.
   */
  photo?: File;
  /**
   * Key of the persisted identification request this selection came from (#630).
   * Handed back so the downstream "create plant" step can link the created
   * instance back onto the identification record. `undefined` when the flow had
   * no persisted request (e.g. a species linked without an identify round-trip).
   */
  requestKey?: string;
}

interface PlantIdentificationDialogProps {
  open: boolean;
  onClose: () => void;
  /**
   * Called once the user picked a candidate and a matching species exists or
   * was created. The caller wires this into the PlantInstance creation flow.
   * If omitted, the dialog falls back to a notification.
   */
  onSpeciesResolved?: (result: IdentifiedSpecies) => void;
  /** Link to manual species search (graceful fallback, REQ-029 §4.1). */
  onManualSearch?: () => void;
}

/**
 * REQ-029 §4.1 / REQ-029-A §10.1 — reusable plant identification dialog.
 *
 * Flow: status check → consent gate → capture (webcam / rear camera / upload)
 * → identify → explicit candidate selection → select(rank) → resolve species
 * (link existing or create from suggestion) → hand back to the caller's
 * "create plant" step. No silent auto-create of the top-1 candidate.
 *
 * Usability improvements over v1:
 * - aria-live status region announces loading/result state to screen readers (UI-NFR-002 R-011)
 * - Organ selector has an info-icon tooltip explaining "Pflanzenteil" in plain language (UI-NFR-011)
 * - "habit" organ chip label maps to a beginner-friendly term via i18n
 * - Identify button uses minHeight 48px (touch target, UI-NFR-001 R-011)
 * - Retake button gets an aria-label for screen readers
 * - Image preview is labelled with a visible caption (not just alt-text)
 * - "Not a plant" alert includes a retry button so user isn't stuck
 * - Manual search link has sufficient tap area via padding
 */
export default function PlantIdentificationDialog({
  open,
  onClose,
  onSpeciesResolved,
  onManualSearch,
}: PlantIdentificationDialogProps) {
  const theme = useTheme();
  const fullScreen = useMediaQuery(theme.breakpoints.down('sm'));
  const { t } = useTranslation();
  const dispatch = useAppDispatch();
  const { level, isFieldVisible } = useExpertiseLevel();
  const notification = useNotification();
  const { handleError } = useApiError();

  const status = useAppSelector((s) => s.identification.status);
  const statusLoading = useAppSelector((s) => s.identification.statusLoading);
  const result = useAppSelector((s) => s.identification.result);
  const identifying = useAppSelector((s) => s.identification.identifying);
  const selecting = useAppSelector((s) => s.identification.selecting);
  const error = useAppSelector((s) => s.identification.error);
  const errorCode = useAppSelector((s) => s.identification.errorCode);

  const [organ, setOrgan] = useState<PlantOrgan>('auto');
  const [preview, setPreview] = useState<{ file: File; url: string } | null>(null);
  const [selectedRank, setSelectedRank] = useState<number | null>(null);
  const [resolving, setResolving] = useState(false);

  // ── Consent state ────────────────────────────────────────────────
  const [consentGranted, setConsentGranted] = useState(false);
  const [consentLoading, setConsentLoading] = useState(false);
  const [consentGranting, setConsentGranting] = useState(false);
  const [consentError, setConsentError] = useState<string | null>(null);

  // aria-live status message ref — updated to announce state changes to screen readers
  const liveStatusRef = useRef<HTMLSpanElement>(null);

  const available = status?.available ?? false;
  // Organ chips: hidden for beginners (Auto only) — REQ-029 §4.3.
  const showOrganSelect = isFieldVisible('intermediate');

  const revokePreview = useCallback(() => {
    setPreview((prev) => {
      if (prev) URL.revokeObjectURL(prev.url);
      return null;
    });
  }, []);

  const loadConsent = useCallback(async () => {
    // Light mode: no backend consent endpoint exists — read the local flag and
    // never touch /privacy/consents (which would 404). Full mode: load the
    // backend consent record as before.
    if (isLightMode) {
      setConsentError(null);
      setConsentGranted(readLightConsent());
      setConsentLoading(false);
      return;
    }
    setConsentLoading(true);
    setConsentError(null);
    try {
      const consents = await listConsents();
      const record = consents.find((c) => c.purpose === CONSENT_PURPOSE);
      setConsentGranted(!!record?.granted);
    } catch (err) {
      setConsentError(parseApiError(err));
      setConsentGranted(false);
    } finally {
      setConsentLoading(false);
    }
  }, []);

  // On open: fetch feature status + consent state, reset local flow. The
  // consent load synchronizes React state with the backend (external system),
  // so the setState-in-effect is intentional and matches PrivacySettingsPage.
  useEffect(() => {
    if (!open) return;
    dispatch(fetchIdentificationStatus());
    // eslint-disable-next-line react-hooks/set-state-in-effect
    loadConsent();
    return () => {
      dispatch(resetIdentification());
      revokePreview();
      setSelectedRank(null);
      setOrgan('auto');
    };
  }, [open, dispatch, loadConsent, revokePreview]);

  const handleGrantConsent = useCallback(async () => {
    // Light mode: persist the opt-in client-side only — no backend call.
    if (isLightMode) {
      writeLightConsent();
      setConsentGranted(true);
      return;
    }
    setConsentGranting(true);
    setConsentError(null);
    try {
      await grantConsent(CONSENT_PURPOSE);
      setConsentGranted(true);
    } catch (err) {
      setConsentError(parseApiError(err));
    } finally {
      setConsentGranting(false);
    }
  }, []);

  const handleImageReady = useCallback(
    (file: File, previewUrl: string) => {
      revokePreview();
      setPreview({ file, url: previewUrl });
      setSelectedRank(null);
      dispatch(resetIdentification());
    },
    [dispatch, revokePreview],
  );

  const handleIdentify = useCallback(async () => {
    if (!preview) return;
    const action = await dispatch(
      identifyPlant({ image: preview.file, organ, language: 'de' }),
    );
    // If consent was revoked server-side meanwhile, re-show the gate.
    if (
      identifyPlant.rejected.match(action) &&
      action.payload?.code === 'CONSENT_REQUIRED'
    ) {
      setConsentGranted(false);
    }
  }, [preview, organ, dispatch]);

  const handleRetake = useCallback(() => {
    revokePreview();
    setSelectedRank(null);
    dispatch(resetIdentification());
  }, [dispatch, revokePreview]);

  const handleConfirmSelection = useCallback(async () => {
    if (!result?.request_key || selectedRank == null) return;
    setResolving(true);
    try {
      const selectionAction = await dispatch(
        selectIdentificationResult({
          requestKey: result.request_key,
          selectedRank,
        }),
      );
      if (!selectIdentificationResult.fulfilled.match(selectionAction)) return;
      const selection = selectionAction.payload;

      let speciesKey = selection.matched_species_key;
      if (!speciesKey) {
        // species_in_database === false → create the species from the suggestion.
        const created = await speciesApi.createSpecies({
          scientific_name: selection.scientific_name,
          common_names: selection.common_names,
          genus: selection.genus ?? undefined,
        });
        speciesKey = created.key;
        notification.success(t('pages.plantIdentification.speciesCreated'));
      }

      // Hand the captured photo back so the create-plant step can reuse it as
      // the gallery cover / few-shot reference (issue #447). We pass the File
      // itself; only the preview object-URL is revoked on cleanup, not the File.
      onSpeciesResolved?.({
        speciesKey,
        scientificName: selection.scientific_name,
        photo: preview?.file,
        // Carry the persisted request key so the create-plant step can link the
        // new instance back onto this identification record (#630).
        requestKey: result.request_key ?? undefined,
      });
      onClose();
    } catch (err) {
      handleError(err);
    } finally {
      setResolving(false);
    }
  }, [result, selectedRank, preview, dispatch, notification, t, onSpeciesResolved, onClose, handleError]);

  const selectedSuggestion = result?.suggestions.find((s) => s.rank === selectedRank);
  const busy = identifying || selecting || resolving;

  // Derive a polite live-region message for screen readers
  const liveMessage = identifying
    ? t('pages.plantIdentification.statusIdentifying')
    : result && result.is_plant && result.suggestions.length > 0
      ? t('pages.plantIdentification.statusResultsReady', { count: result.suggestions.length })
      : result && (!result.is_plant || result.suggestions.length === 0)
        ? t('pages.plantIdentification.statusNoResults')
        : '';

  return (
    <Dialog
      open={open}
      onClose={busy ? undefined : onClose}
      fullScreen={fullScreen}
      maxWidth="sm"
      fullWidth
      aria-labelledby="plant-identification-dialog-title"
      data-testid="plant-identification-dialog"
    >
      <DialogTitle
        id="plant-identification-dialog-title"
        sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', pr: 1 }}
      >
        {t('pages.plantIdentification.dialogTitle')}
        <IconButton
          onClick={onClose}
          disabled={busy}
          aria-label={t('common.close')}
          data-testid="identification-dialog-close"
          size="large"
        >
          <CloseIcon />
        </IconButton>
      </DialogTitle>

      {/* aria-live region: announces state changes to screen readers (UI-NFR-002 R-011).
          Uses clipPath instead of the deprecated clip property (WCAG 1.4.4). */}
      <Box
        component="span"
        ref={liveStatusRef}
        aria-live="polite"
        aria-atomic="true"
        sx={{
          position: 'absolute',
          width: 1,
          height: 1,
          overflow: 'hidden',
          clipPath: 'inset(50%)',
          whiteSpace: 'nowrap',
        }}
      >
        {liveMessage}
      </Box>

      <DialogContent dividers>
        {/* Feature availability (REQ-029 §3.7 / 503 FEATURE_NOT_CONFIGURED) */}
        {statusLoading ? (
          <Box sx={{ display: 'flex', justifyContent: 'center', py: 4 }}>
            <CircularProgress size={28} data-testid="status-loading" />
          </Box>
        ) : !available ? (
          <Alert severity="info" data-testid="feature-unavailable">
            {t('pages.plantIdentification.notConfigured')}
          </Alert>
        ) : !consentGranted ? (
          <IdentificationConsentGate
            granted={consentGranted}
            loading={consentLoading}
            granting={consentGranting}
            error={consentError}
            onGrant={handleGrantConsent}
            onDecline={onClose}
            // Light mode has no privacy settings tab → hide the dead link.
            showPrivacyLink={!isLightMode}
          />
        ) : (
          <>
            <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
              {t('pages.plantIdentification.intro')}
            </Typography>

            {/* Organ selection (intermediate+) */}
            {showOrganSelect && !preview && (
              <Box sx={{ mb: 2 }}>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5, mb: 1 }}>
                  <Typography variant="subtitle2">
                    {t('pages.plantIdentification.organLabel')}
                  </Typography>
                  {/*
                   * "Organ" is a botanical term that casual users won't know.
                   * Tooltip explains it in plain language (UI-NFR-011).
                   */}
                  <Tooltip
                    title={t('pages.plantIdentification.organHint')}
                    placement="top"
                    arrow
                  >
                    <InfoOutlinedIcon
                      sx={{ fontSize: 16, color: 'text.secondary', cursor: 'help' }}
                      aria-label={t('pages.plantIdentification.organHint')}
                      tabIndex={0}
                    />
                  </Tooltip>
                </Box>
                {/* role="radiogroup" + role="radio" per chip: screen readers announce
                    selection state correctly instead of just "chip" (UI-NFR-002 R-009). */}
                <Stack
                  direction="row"
                  spacing={1}
                  role="radiogroup"
                  aria-label={t('pages.plantIdentification.organLabel')}
                  sx={{ flexWrap: 'wrap', gap: 1 }}
                >
                  {ORGAN_OPTIONS.map((o) => (
                    <Chip
                      key={o}
                      label={t(`enums.plantOrgan.${o}`)}
                      color={organ === o ? 'primary' : 'default'}
                      variant={organ === o ? 'filled' : 'outlined'}
                      onClick={() => setOrgan(o)}
                      data-testid={`organ-chip-${o}`}
                      role="radio"
                      aria-checked={organ === o}
                      // Ensure adequate touch target height
                      sx={{ height: { xs: 40, sm: 32 } }}
                    />
                  ))}
                </Stack>
                {/* Extra plain-language hint for 'auto' selection */}
                {organ === 'auto' && (
                  <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mt: 0.5 }}>
                    {t('pages.plantIdentification.organHintAuto')}
                  </Typography>
                )}
              </Box>
            )}

            {/* Capture — hidden once an image is selected */}
            {!preview && (
              <ImageCapturePanel
                onImageReady={handleImageReady}
                level={level}
                disabled={busy}
              />
            )}

            {/* Selected image preview + identify trigger */}
            {preview && !result && (
              <Box data-testid="image-preview-block">
                <Box
                  component="img"
                  src={preview.url}
                  alt={t('pages.plantIdentification.selectedImageAlt')}
                  sx={{
                    width: '100%',
                    maxHeight: 320,
                    objectFit: 'contain',
                    borderRadius: 1,
                    bgcolor: 'action.hover',
                    display: 'block',
                  }}
                  data-testid="image-preview"
                />
                <Typography
                  variant="caption"
                  color="text.secondary"
                  sx={{ display: 'block', mt: 0.5, textAlign: 'center' }}
                >
                  {t('pages.plantIdentification.selectedImageAlt')}
                </Typography>
                <Stack
                  direction={{ xs: 'column', sm: 'row' }}
                  spacing={1}
                  sx={{ mt: 1.5 }}
                >
                  <Button
                    variant="contained"
                    onClick={handleIdentify}
                    disabled={identifying}
                    fullWidth
                    startIcon={identifying ? <CircularProgress size={16} /> : undefined}
                    data-testid="identify-submit"
                    sx={{ minHeight: { xs: 52, sm: 44 } }}
                  >
                    {identifying
                      ? t('pages.plantIdentification.analyzing')
                      : t('pages.plantIdentification.identifyButton')}
                  </Button>
                  <Button
                    variant="outlined"
                    color="inherit"
                    startIcon={<ReplayIcon />}
                    onClick={handleRetake}
                    disabled={identifying}
                    aria-label={t('pages.plantIdentification.retake')}
                    data-testid="image-retake"
                    sx={{ minHeight: { xs: 52, sm: 44 } }}
                  >
                    {t('pages.plantIdentification.retake')}
                  </Button>
                </Stack>
              </Box>
            )}

            {/* Error states (415/413/429/CONSENT) */}
            {error && errorCode !== 'CONSENT_REQUIRED' && (
              <Alert severity="error" sx={{ mt: 2 }} data-testid="identify-error">
                {error}
              </Alert>
            )}

            {/* No plant detected (is_plant === false) */}
            {result && !result.is_plant && (
              <Alert
                severity="warning"
                sx={{ mt: 2 }}
                data-testid="not-a-plant"
                action={
                  <Button
                    color="inherit"
                    size="small"
                    onClick={handleRetake}
                    startIcon={<ReplayIcon />}
                    data-testid="not-a-plant-retry"
                  >
                    {t('pages.plantIdentification.notAPlantRetry')}
                  </Button>
                }
              >
                {result.message || t('pages.plantIdentification.notAPlant')}
              </Alert>
            )}

            {/* Empty suggestion set */}
            {result && result.is_plant && result.suggestions.length === 0 && (
              <Alert severity="info" sx={{ mt: 2 }} data-testid="no-results">
                {t('pages.plantIdentification.noResults')}
              </Alert>
            )}

            {/* Candidate selection */}
            {result && result.is_plant && result.suggestions.length > 0 && (
              <Box sx={{ mt: 1 }}>
                <Typography variant="subtitle1" sx={{ mb: 1 }}>
                  {t('pages.plantIdentification.results')}
                </Typography>
                <SuggestionList
                  suggestions={result.suggestions}
                  selectedRank={selectedRank}
                  onSelect={setSelectedRank}
                  level={level}
                  disabled={busy}
                />
              </Box>
            )}

            {/* Manual fallback link — minHeight 44px ensures tap target on mobile
                (UI-NFR-001 R-011). Not `size="small"` because that caps height at ~36px. */}
            {onManualSearch && (
              <Button
                variant="text"
                onClick={onManualSearch}
                sx={{ mt: 2, minHeight: 44, px: 1 }}
                data-testid="manual-search-link"
              >
                {t('pages.plantIdentification.manualSearch')}
              </Button>
            )}
          </>
        )}
      </DialogContent>

      <DialogActions sx={{ px: 3, py: 2, gap: 1 }}>
        <Button
          onClick={onClose}
          disabled={busy}
          data-testid="identification-cancel"
          sx={{ minHeight: 44 }}
        >
          {t('common.cancel')}
        </Button>
        {result && result.is_plant && result.suggestions.length > 0 && (
          <Button
            variant="contained"
            onClick={handleConfirmSelection}
            disabled={selectedRank == null || busy}
            startIcon={busy ? <CircularProgress size={16} /> : undefined}
            data-testid="create-plant-from-selection"
            sx={{ minHeight: 44 }}
          >
            {selectedSuggestion?.species_in_database
              ? t('pages.plantIdentification.selectPlant')
              : t('pages.plantIdentification.createAndSelectPlant')}
          </Button>
        )}
      </DialogActions>
    </Dialog>
  );
}
