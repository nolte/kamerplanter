import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import { useTranslation } from 'react-i18next';
import Alert from '@mui/material/Alert';
import Box from '@mui/material/Box';
import Button from '@mui/material/Button';
import Chip from '@mui/material/Chip';
import Dialog from '@mui/material/Dialog';
import DialogActions from '@mui/material/DialogActions';
import DialogContent from '@mui/material/DialogContent';
import DialogContentText from '@mui/material/DialogContentText';
import DialogTitle from '@mui/material/DialogTitle';
import FormControl from '@mui/material/FormControl';
import FormControlLabel from '@mui/material/FormControlLabel';
import IconButton from '@mui/material/IconButton';
import ImageList from '@mui/material/ImageList';
import ImageListItem from '@mui/material/ImageListItem';
import ImageListItemBar from '@mui/material/ImageListItemBar';
import InputLabel from '@mui/material/InputLabel';
import MenuItem from '@mui/material/MenuItem';
import Select from '@mui/material/Select';
import Skeleton from '@mui/material/Skeleton';
import Switch from '@mui/material/Switch';
import Tooltip from '@mui/material/Tooltip';
import Typography from '@mui/material/Typography';
import useMediaQuery from '@mui/material/useMediaQuery';
import { useTheme } from '@mui/material/styles';
import CollectionsIcon from '@mui/icons-material/Collections';
import OpenInNewIcon from '@mui/icons-material/OpenInNew';
import VisibilityOffIcon from '@mui/icons-material/VisibilityOff';
import RestoreFromTrashIcon from '@mui/icons-material/RestoreFromTrash';
import {
  getReferenceImageCuration,
  setReferenceImageActive,
} from '@/api/endpoints/adminReferenceImages';
import { useNotification } from '@/hooks/useNotification';
import { stripHtml } from '@/utils/formatting';
import type { CurationImage, ReferenceExclusionReason } from '@/api/types';

/** Minimum active references for an art to stay recognizable (REQ-029-A §4.3). */
const MIN_USABLE_REFERENCES = 5;

const EXCLUSION_REASONS: ReferenceExclusionReason[] = [
  'blurry',
  'wrong_organ',
  'wrong_species',
  'duplicate',
  'irrelevant',
  'manual',
];

interface ReferenceImageCurationProps {
  speciesKey: string;
  /** Scientific name used for aria-label and image alt fallback. */
  scientificName?: string;
}

function buildCaption(image: CurationImage): string {
  const parts: string[] = [];
  // Attributions from Wikimedia can contain HTML markup — strip it to text.
  const attribution = stripHtml(image.attribution);
  if (attribution) parts.push(`© ${attribution}`);
  if (image.license) parts.push(image.license);
  return parts.join(' · ');
}

interface CurationTileProps {
  image: CurationImage;
  scientificName?: string;
  busy: boolean;
  onDeselect: (image: CurationImage, triggerEl: HTMLButtonElement) => void;
  onReinclude: (image: CurationImage) => void;
}

/** Single curatable tile: greyed-out + badged when the image is deselected. */
function CurationTile({ image, scientificName, busy, onDeselect, onReinclude }: CurationTileProps) {
  const { t } = useTranslation();
  const [failed, setFailed] = useState(false);
  const deselectBtnRef = useRef<HTMLButtonElement>(null);

  if (failed) return null;

  const caption = buildCaption(image);
  const organLabel = image.organ
    ? t(`pages.species.referenceImages.organ.${image.organ}`, { defaultValue: image.organ })
    : undefined;
  const altText =
    [organLabel, scientificName].filter(Boolean).join(' – ') ||
    t('pages.species.referenceImages.imageAlt');
  const inactive = !image.is_active;

  return (
    <ImageListItem data-testid="curation-image-item" data-active={image.is_active}>
      <img
        src={image.source_url}
        alt={altText}
        loading="lazy"
        referrerPolicy="no-referrer"
        onError={() => setFailed(true)}
        style={{
          objectFit: 'cover',
          width: '100%',
          height: '100%',
          // Deselected images are visibly muted so the active set is obvious.
          filter: inactive ? 'grayscale(1)' : 'none',
          opacity: inactive ? 0.45 : 1,
        }}
      />
      {inactive && (
        <Chip
          size="small"
          color="default"
          label={t('pages.species.referenceImages.curation.excludedBadge')}
          sx={{
            position: 'absolute',
            top: 6,
            left: 6,
            bgcolor: 'rgba(0,0,0,0.7)',
            color: '#fff',
          }}
        />
      )}
      <ImageListItemBar
        title={organLabel}
        subtitle={caption || undefined}
        actionIcon={
          <Box sx={{ display: 'flex', alignItems: 'center' }}>
            {image.source_url && (
              <Tooltip title={t('pages.species.referenceImages.curation.openSource')}>
                <IconButton
                  component="a"
                  href={image.source_url}
                  target="_blank"
                  rel="noopener noreferrer"
                  size="small"
                  aria-label={t('pages.species.referenceImages.curation.openSourceAria', {
                    name: scientificName ?? '',
                  })}
                  data-testid="reference-source-link"
                  // xs: p:1.5 = ~42px touch-target (WCAG 2.5.5 / UI-NFR-001 R-011)
                  sx={{ color: 'rgba(255,255,255,0.9)', p: { xs: 1.5, sm: 1 } }}
                >
                  <OpenInNewIcon fontSize="small" />
                </IconButton>
              </Tooltip>
            )}
            {inactive ? (
              <Tooltip title={t('pages.species.referenceImages.curation.reinclude')}>
                <span>
                  <IconButton
                    size="small"
                    disabled={busy}
                    onClick={() => onReinclude(image)}
                    aria-label={t('pages.species.referenceImages.curation.reincludeAria', {
                      name: scientificName ?? '',
                    })}
                    data-testid="reference-reinclude-button"
                    sx={{ color: 'rgba(255,255,255,0.9)', p: { xs: 1.5, sm: 1 } }}
                  >
                    <RestoreFromTrashIcon fontSize="small" />
                  </IconButton>
                </span>
              </Tooltip>
            ) : (
              <Tooltip title={t('pages.species.referenceImages.curation.deselect')}>
                <span>
                  <IconButton
                    ref={deselectBtnRef}
                    size="small"
                    disabled={busy}
                    onClick={() => {
                      if (deselectBtnRef.current) onDeselect(image, deselectBtnRef.current);
                    }}
                    aria-label={t('pages.species.referenceImages.curation.deselectAria', {
                      name: scientificName ?? '',
                    })}
                    data-testid="reference-deselect-button"
                    sx={{ color: 'rgba(255,255,255,0.9)', p: { xs: 1.5, sm: 1 } }}
                  >
                    <VisibilityOffIcon fontSize="small" />
                  </IconButton>
                </span>
              </Tooltip>
            )}
          </Box>
        }
        sx={{
          background:
            'linear-gradient(to top, rgba(0,0,0,0.72) 0%, rgba(0,0,0,0.36) 60%, transparent 100%)',
          '& .MuiImageListItemBar-title': { fontSize: '0.75rem', lineHeight: 1.3 },
          '& .MuiImageListItemBar-subtitle': {
            fontSize: '0.68rem',
            lineHeight: 1.2,
            whiteSpace: 'normal',
            overflow: 'visible',
          },
        }}
      />
    </ImageListItem>
  );
}

/**
 * Admin curation view for a species' reference images (REQ-029-A).
 *
 * Unlike the public {@link ReferenceImageGallery}, this fetches ALL images —
 * including deselected ones — and lets a platform admin deselect images that
 * fail the visual test (with a reason) or re-include them. Deselected images
 * are removed from recognition (filtered out of /match) but kept for the audit
 * trail. A warning surfaces when the active set drops below the
 * recognizability threshold (REQ-029-A §4.3).
 */
export function ReferenceImageCuration({ speciesKey, scientificName }: ReferenceImageCurationProps) {
  const { t } = useTranslation();
  const theme = useTheme();
  const notify = useNotification();
  const isMobile = useMediaQuery(theme.breakpoints.down('sm'));
  const isTablet = useMediaQuery(theme.breakpoints.between('sm', 'md'));
  const [images, setImages] = useState<CurationImage[]>([]);
  const [loading, setLoading] = useState(true);
  const [busyId, setBusyId] = useState<number | null>(null);
  const [deselectTarget, setDeselectTarget] = useState<CurationImage | null>(null);
  const [reason, setReason] = useState<ReferenceExclusionReason>('blurry');
  const [hideDeselected, setHideDeselected] = useState(false);
  // Ref to the button that triggered the deselect dialog — focus returns here on close.
  const deselectTriggerRef = useRef<HTMLButtonElement | null>(null);

  const cols = useMemo(() => {
    if (isMobile) return 2;
    if (isTablet) return 3;
    return 4;
  }, [isMobile, isTablet]);

  const activeCount = useMemo(() => images.filter((img) => img.is_active).length, [images]);
  const hasDeselected = useMemo(() => images.some((img) => !img.is_active), [images]);
  // Images actually shown — deselected ones are hidden when the toggle is on.
  const visibleImages = useMemo(
    () => (hideDeselected ? images.filter((img) => img.is_active) : images),
    [images, hideDeselected],
  );

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const data = await getReferenceImageCuration(speciesKey);
      setImages(data.images ?? []);
    } catch {
      setImages([]);
    } finally {
      setLoading(false);
    }
  }, [speciesKey]);

  useEffect(() => {
    void load();
  }, [load]);

  const applyActive = useCallback(
    async (image: CurationImage, isActive: boolean, why?: ReferenceExclusionReason) => {
      setBusyId(image.id);
      try {
        await setReferenceImageActive(speciesKey, image.id, {
          is_active: isActive,
          reason: isActive ? null : (why ?? 'manual'),
        });
        setImages((prev) =>
          prev.map((img) =>
            img.id === image.id
              ? { ...img, is_active: isActive, exclusion_reason: isActive ? null : (why ?? 'manual') }
              : img,
          ),
        );
        notify.success(
          isActive
            ? t('pages.species.referenceImages.curation.reincludeSuccess')
            : t('pages.species.referenceImages.curation.deselectSuccess'),
        );
      } catch {
        notify.error(t('pages.species.referenceImages.curation.actionError'));
      } finally {
        setBusyId(null);
      }
    },
    [speciesKey, notify, t],
  );

  const confirmDeselect = useCallback(async () => {
    if (!deselectTarget) return;
    const target = deselectTarget;
    const trigger = deselectTriggerRef.current;
    setDeselectTarget(null);
    // Restore focus to the trigger element after the dialog closes (WCAG 2.4.3).
    // RAF ensures the dialog has finished closing before focus moves.
    if (trigger) requestAnimationFrame(() => trigger.focus());
    await applyActive(target, false, reason);
  }, [deselectTarget, reason, applyActive]);

  const openDeselect = useCallback((image: CurationImage, triggerEl: HTMLButtonElement) => {
    deselectTriggerRef.current = triggerEl;
    setReason('blurry');
    setDeselectTarget(image);
  }, []);

  const closeDeselect = useCallback(() => {
    const trigger = deselectTriggerRef.current;
    setDeselectTarget(null);
    if (trigger) requestAnimationFrame(() => trigger.focus());
  }, []);

  return (
    <Box data-testid="reference-image-curation">
      <Typography component="h2" variant="h6" sx={{ mb: 0.5 }}>
        {t('pages.species.referenceImages.title')}
      </Typography>
      <Typography variant="body2" color="text.secondary" sx={{ mb: 1.5 }}>
        {t('pages.species.referenceImages.curation.intro')}
      </Typography>

      {!loading && hasDeselected && (
        <FormControlLabel
          control={
            <Switch
              checked={hideDeselected}
              onChange={(e) => setHideDeselected(e.target.checked)}
              size="small"
              data-testid="curation-hide-deselected-toggle"
            />
          }
          label={t('pages.species.referenceImages.curation.hideDeselected')}
          sx={{ mb: 1, ml: 0 }}
        />
      )}

      {!loading && images.length > 0 && activeCount < MIN_USABLE_REFERENCES && (
        <Alert
          severity="warning"
          role="alert"
          sx={{ mb: 1.5 }}
          data-testid="curation-coverage-warning"
        >
          {t('pages.species.referenceImages.curation.lowCoverageWarning', {
            count: activeCount,
            min: MIN_USABLE_REFERENCES,
          })}
        </Alert>
      )}

      {loading ? (
        <ImageList
          cols={cols}
          gap={8}
          sx={{ m: 0 }}
          aria-label={t('pages.species.referenceImages.galleryLoadingLabel')}
          aria-busy="true"
        >
          {Array.from({ length: cols }).map((_, i) => (
            <ImageListItem key={i} aria-hidden="true">
              <Skeleton variant="rectangular" sx={{ width: '100%', aspectRatio: '1 / 1' }} />
            </ImageListItem>
          ))}
        </ImageList>
      ) : images.length === 0 ? (
        <Box
          sx={{
            display: 'flex',
            alignItems: 'flex-start',
            gap: 1,
            py: 2,
            px: 1.5,
            borderRadius: 1,
            bgcolor: 'action.hover',
            color: 'text.secondary',
          }}
          data-testid="reference-image-empty"
          role="status"
        >
          <CollectionsIcon fontSize="small" aria-hidden="true" sx={{ mt: 0.25, flexShrink: 0 }} />
          <Box>
            <Typography variant="body2">{t('pages.species.referenceImages.empty')}</Typography>
            <Typography
              variant="caption"
              color="text.secondary"
              sx={{ display: 'block', mt: 0.25 }}
            >
              {t('pages.species.referenceImages.emptyHint')}
            </Typography>
          </Box>
        </Box>
      ) : visibleImages.length === 0 ? (
        <Typography
          variant="body2"
          color="text.secondary"
          sx={{ py: 2 }}
          role="status"
          data-testid="curation-all-hidden"
        >
          {t('pages.species.referenceImages.curation.allHidden')}
        </Typography>
      ) : (
        <ImageList
          cols={cols}
          gap={8}
          sx={{ m: 0 }}
          aria-label={
            scientificName
              ? t('pages.species.referenceImages.galleryAriaLabel', { name: scientificName })
              : t('pages.species.referenceImages.title')
          }
        >
          {visibleImages.map((image) => (
            <CurationTile
              key={image.id}
              image={image}
              scientificName={scientificName}
              busy={busyId === image.id}
              onDeselect={openDeselect}
              onReinclude={(img) => void applyActive(img, true)}
            />
          ))}
        </ImageList>
      )}

      <Dialog
        open={!!deselectTarget}
        onClose={closeDeselect}
        maxWidth="xs"
        fullWidth
        aria-labelledby="deselect-dialog-title"
        data-testid="deselect-dialog"
      >
        <DialogTitle id="deselect-dialog-title">
          {t('pages.species.referenceImages.curation.deselectDialogTitle')}
        </DialogTitle>
        <DialogContent>
          <DialogContentText sx={{ mb: 2 }}>
            {t('pages.species.referenceImages.curation.deselectDialogText')}
          </DialogContentText>
          <FormControl fullWidth size="small">
            <InputLabel id="deselect-reason-label">
              {t('pages.species.referenceImages.curation.reasonLabel')}
            </InputLabel>
            <Select
              labelId="deselect-reason-label"
              label={t('pages.species.referenceImages.curation.reasonLabel')}
              value={reason}
              onChange={(e) => setReason(e.target.value as ReferenceExclusionReason)}
              data-testid="deselect-reason-select"
              inputProps={{ autoFocus: true }}
            >
              {EXCLUSION_REASONS.map((r) => (
                <MenuItem key={r} value={r}>
                  {t(`pages.species.referenceImages.curation.reason.${r}`)}
                </MenuItem>
              ))}
            </Select>
          </FormControl>
        </DialogContent>
        <DialogActions>
          <Button onClick={closeDeselect}>{t('common.cancel')}</Button>
          <Button
            onClick={() => void confirmDeselect()}
            color="error"
            variant="contained"
            data-testid="deselect-confirm"
          >
            {t('pages.species.referenceImages.curation.deselect')}
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
}
