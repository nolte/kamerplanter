import { useCallback, useEffect, useMemo, useState } from 'react';
import { useTranslation } from 'react-i18next';
import { useNotification } from '@/hooks/useNotification';
import { usePlatformAdmin } from '@/hooks/usePlatformAdmin';
import Box from '@mui/material/Box';
import Button from '@mui/material/Button';
import Chip from '@mui/material/Chip';
import FormControlLabel from '@mui/material/FormControlLabel';
import IconButton from '@mui/material/IconButton';
import Skeleton from '@mui/material/Skeleton';
import Switch from '@mui/material/Switch';
import Tooltip from '@mui/material/Tooltip';
import Typography from '@mui/material/Typography';
import AddAPhotoIcon from '@mui/icons-material/AddAPhoto';
import DeleteOutlineIcon from '@mui/icons-material/DeleteOutlined';
import PublicIcon from '@mui/icons-material/Public';
import SearchIcon from '@mui/icons-material/Search';
import AutoAwesomeIcon from '@mui/icons-material/AutoAwesome';
import VisibilityOffOutlinedIcon from '@mui/icons-material/VisibilityOffOutlined';
import VisibilityOutlinedIcon from '@mui/icons-material/VisibilityOutlined';
import AuthImage from '@/components/common/AuthImage';
import ConfirmDialog from '@/components/common/ConfirmDialog';
import PestImageContributeDialog from './PestImageContributeDialog';
import { listPestImages, deletePestImage } from '@/api/endpoints/ipm';
import { setPestContributionActive, setPestImageActive } from '@/api/endpoints/adminPestRecognition';
import type { PestImage } from '@/api/types';
import LoadingStatus from '@/components/common/LoadingStatus';

interface PestImageGalleryProps {
  pestKey: string;
  pestName: string;
  /**
   * The pest's few-shot recognition class slug (`Pest.detection_slug`), needed
   * for the platform-admin deselect/re-include action on `recognition` tiles
   * (the inference-service curation endpoint is keyed by label). `null` when the
   * pest is not part of the recognition taxonomy — recognition tiles then carry
   * no curation control.
   */
  detectionSlug?: string | null;
}

/** Parse the numeric prototype id out of a `recognition:{id}` tile id. */
function parseRecognitionId(tileId: string): number | null {
  const raw = tileId.startsWith('recognition:') ? tileId.slice('recognition:'.length) : '';
  const parsed = Number.parseInt(raw, 10);
  return Number.isInteger(parsed) ? parsed : null;
}

/**
 * REQ-010 — gallery of reference images for a pest.
 *
 * Shows the tenant's own photos (and, once promoted, globally shared ones), the
 * read-only photos of the tenant's inspections, and the global recognition
 * reference images. A normal user may contribute / delete their own photos and
 * only ever sees *active* images (read-only otherwise).
 *
 * A platform admin additionally gets curation controls: a "show deselected"
 * toggle (loads inactive tiles too, dimmed) and a per-image deselect /
 * re-include button for `contribution` and `recognition` tiles. Deselecting an
 * image hides it from everyone's gallery without deleting it (audit / reversible)
 * — and never touches the recognition index (pure visibility).
 */
export default function PestImageGallery({ pestKey, pestName, detectionSlug = null }: PestImageGalleryProps) {
  const { t } = useTranslation();
  const notification = useNotification();
  const isPlatformAdmin = usePlatformAdmin();
  const [images, setImages] = useState<PestImage[]>([]);
  const [loading, setLoading] = useState(true);
  const [dialogOpen, setDialogOpen] = useState(false);
  /** Admin-only: when true, deselected (inactive) tiles are loaded too. */
  const [showDeselected, setShowDeselected] = useState(false);
  /** Tile ids with an in-flight curation toggle (disables the button). */
  const [togglingIds, setTogglingIds] = useState<Set<string>>(() => new Set());
  /** ID of the image pending deletion — null means the dialog is closed. */
  const [pendingDeleteId, setPendingDeleteId] = useState<string | null>(null);
  const [deleting, setDeleting] = useState(false);
  /**
   * Ids of recognition tiles whose external (CC-licensed) image failed to load
   * (dead link / hotlink-blocked). Such tiles are hidden so a broken image is
   * never shown — the externally-hosted URL has no local fallback.
   */
  const [brokenIds, setBrokenIds] = useState<Set<string>>(() => new Set());

  const handleImageError = useCallback((imageId: string) => {
    setBrokenIds((prev) => {
      if (prev.has(imageId)) return prev;
      const next = new Set(prev);
      next.add(imageId);
      return next;
    });
  }, []);

  // Admins may opt into the inactive view; everyone else always loads active-only.
  const includeInactive = isPlatformAdmin && showDeselected;

  const load = useCallback(async () => {
    setLoading(true);
    setBrokenIds(new Set());
    try {
      // Keep the default request a plain single-arg call (active-only); only the
      // admin curation view passes the options object.
      const loaded = includeInactive
        ? await listPestImages(pestKey, { includeInactive: true })
        : await listPestImages(pestKey);
      setImages(loaded);
    } catch {
      setImages([]);
    } finally {
      setLoading(false);
    }
  }, [pestKey, includeInactive]);

  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect
    load();
  }, [load]);

  const handleDeleteRequest = useCallback((imageId: string) => {
    setPendingDeleteId(imageId);
  }, []);

  const handleDeleteConfirm = useCallback(async () => {
    if (!pendingDeleteId) return;
    setDeleting(true);
    try {
      await deletePestImage(pestKey, pendingDeleteId);
      setImages((prev) => prev.filter((img) => img.id !== pendingDeleteId));
      notification.success(t('pages.pestDetail.imageDeleteSuccess'));
    } finally {
      setDeleting(false);
      setPendingDeleteId(null);
    }
  }, [pestKey, pendingDeleteId, notification, t]);

  const handleDeleteCancel = useCallback(() => {
    setPendingDeleteId(null);
  }, []);

  const markToggling = useCallback((tileId: string, busy: boolean) => {
    setTogglingIds((prev) => {
      const next = new Set(prev);
      if (busy) next.add(tileId);
      else next.delete(tileId);
      return next;
    });
  }, []);

  /**
   * Platform-admin curation: deselect (hide) or re-include a tile.
   *
   * - `contribution` → PATCH the admin contributions endpoint (`is_active`);
   * - `recognition`  → PATCH the inference-service prototype (`set_active`),
   *   keyed by the pest's `detectionSlug` + the prototype id from the tile id;
   * - `inspection`   → not curatable (belongs to an inspection), no control shown.
   *
   * On success the local list is updated: when the inactive view is hidden the
   * tile is removed; otherwise its `is_active` flag is flipped in place (so it
   * stays visible but dimmed).
   */
  const handleToggleActive = useCallback(
    async (img: PestImage, nextActive: boolean) => {
      markToggling(img.id, true);
      try {
        if (img.source === 'recognition') {
          const prototypeId = parseRecognitionId(img.id);
          if (detectionSlug === null || prototypeId === null) {
            notification.error(t('pages.pestDetail.imageDeselectError'));
            return;
          }
          await setPestImageActive(detectionSlug, prototypeId, {
            is_active: nextActive,
            reason: nextActive ? null : 'curated-out via pest detail',
          });
        } else {
          // contribution
          await setPestContributionActive(pestKey, img.id, nextActive);
        }

        setImages((prev) => {
          if (!includeInactive && !nextActive) {
            // Deselected while only active tiles are shown → drop it.
            return prev.filter((item) => item.id !== img.id);
          }
          return prev.map((item) => (item.id === img.id ? { ...item, is_active: nextActive } : item));
        });
        notification.success(
          nextActive ? t('pages.pestDetail.imageReactivated') : t('pages.pestDetail.imageDeselected'),
        );
      } catch {
        notification.error(t('pages.pestDetail.imageDeselectError'));
      } finally {
        markToggling(img.id, false);
      }
    },
    [pestKey, detectionSlug, includeInactive, markToggling, notification, t],
  );

  const handleShowDeselectedChange = useCallback((_e: unknown, checked: boolean) => {
    setShowDeselected(checked);
  }, []);

  // Stable grid skeletons during initial load — avoid layout shift.
  const skeletonItems = useMemo(() => Array.from({ length: 4 }, (_, i) => i), []);

  return (
    <Box>
      <Box
        sx={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          gap: 1,
          mb: 1.5,
          flexWrap: 'wrap',
        }}
      >
        <Typography variant="body2" color="text.secondary">
          {t('pages.pestDetail.sectionImagesIntro')}
        </Typography>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, flexWrap: 'wrap' }}>
          {isPlatformAdmin && (
            <FormControlLabel
              control={
                <Switch
                  checked={showDeselected}
                  onChange={handleShowDeselectedChange}
                  size="small"
                  slotProps={{
                    input: {
                      'aria-label': t('pages.pestDetail.showDeselected'),
                      // Stable hook for the test / e2e; MUI forwards arbitrary
                      // attributes on the underlying input element.
                      'data-testid': 'pest-gallery-show-deselected',
                    } as React.InputHTMLAttributes<HTMLInputElement>,
                  }}
                />
              }
              label={t('pages.pestDetail.showDeselected')}
              sx={{ mr: 0, minHeight: 44 }}
            />
          )}
          <Button
            size="small"
            variant="outlined"
            startIcon={<AddAPhotoIcon />}
            onClick={() => setDialogOpen(true)}
            data-testid="pest-contribute-button"
            sx={{ minHeight: 44, flexShrink: 0 }}
          >
            {t('pages.pestDetail.contributeButton')}
          </Button>
        </Box>
      </Box>

      {/* Loading skeleton — prevents layout shift and signals busy state */}
      {loading && (
        <Box
          sx={{
            display: 'grid',
            gridTemplateColumns: { xs: 'repeat(2, 1fr)', sm: 'repeat(3, 1fr)', md: 'repeat(4, 1fr)' },
            gap: 1,
          }}
          aria-busy="true"
        >
          {/* The section title used to sit here as `aria-label`, which was wrong
              twice over (#1324): a `<div>` maps to `generic`, so the name was
              dropped, and naming a loading placeholder after the section rather
              than after its state would have announced the wrong thing anyway. */}
          <LoadingStatus />
          {skeletonItems.map((i) => (
            <Skeleton key={i} variant="rectangular" height={140} sx={{ borderRadius: 1 }} />
          ))}
        </Box>
      )}

      {/* Loaded gallery */}
      {!loading && images.length > 0 && (
        <Box
          sx={{
            display: 'grid',
            gridTemplateColumns: { xs: 'repeat(2, 1fr)', sm: 'repeat(3, 1fr)', md: 'repeat(4, 1fr)' },
            gap: 1,
          }}
          data-testid="pest-detail-gallery"
          role="list"
          aria-label={t('pages.pestDetail.sectionImages')}
          aria-live="polite"
        >
          {images.map((img) => {
            // Inspection-sourced photos are read-only: no delete, a dedicated
            // provenance badge instead of the global/own contribution chrome.
            const isInspection = img.source === 'inspection';
            // Recognition tiles are GLOBAL, read-only reference images hosted
            // externally (CC-licensed source_url) — rendered via a native <img>
            // (no auth, no local pixel), with an attribution/license caption.
            const isRecognition = img.source === 'recognition';
            const isActive = img.is_active ?? true;
            // Deselected tiles are only ever loaded for admins; dim + badge them.
            const isDeselected = !isActive;
            // Admin curation is offered for contribution + recognition tiles
            // (inspection photos belong to an inspection and are not curatable).
            // A recognition tile needs a resolvable detection slug to act on.
            const canCurate =
              isPlatformAdmin &&
              !isInspection &&
              (!isRecognition || detectionSlug !== null);
            const toggling = togglingIds.has(img.id);

            if (isRecognition) {
              // A dead / hotlink-blocked external image is hidden entirely so a
              // broken image is never shown (no local fallback exists).
              if (brokenIds.has(img.id)) return null;
              const captionParts = [img.attribution, img.license].filter(
                (part): part is string => Boolean(part),
              );
              return (
                <Box
                  key={img.id}
                  role="listitem"
                  sx={{ position: 'relative', opacity: isDeselected ? 0.45 : 1 }}
                  data-testid="pest-image-tile"
                >
                  <Box
                    component="img"
                    src={img.uri}
                    alt={t('pages.pestDetail.imageFromRecognitionAlt', { name: pestName })}
                    loading="lazy"
                    referrerPolicy="no-referrer"
                    onError={() => handleImageError(img.id)}
                    data-testid="pest-image-recognition"
                    sx={{
                      borderRadius: 1,
                      width: '100%',
                      height: 140,
                      objectFit: 'cover',
                      display: 'block',
                    }}
                  />
                  <Tooltip title={t('pages.pestDetail.imageFromRecognition')}>
                    <Chip
                      icon={<AutoAwesomeIcon />}
                      size="small"
                      color="secondary"
                      variant="outlined"
                      label={t('pages.pestDetail.imageFromRecognitionShort')}
                      aria-label={t('pages.pestDetail.imageFromRecognition')}
                      sx={{
                        position: 'absolute',
                        top: 4,
                        left: 4,
                        cursor: 'default',
                        bgcolor: 'background.paper',
                      }}
                    />
                  </Tooltip>
                  {isDeselected && <DeselectedBadge label={t('pages.pestDetail.imageDeselectedBadge')} />}
                  {canCurate && (
                    <CurationButton
                      active={isActive}
                      busy={toggling}
                      onToggle={() => handleToggleActive(img, !isActive)}
                      deselectLabel={t('pages.pestDetail.imageDeselect')}
                      reactivateLabel={t('pages.pestDetail.imageReactivate')}
                    />
                  )}
                  {captionParts.length > 0 && (
                    <Typography
                      variant="caption"
                      color="text.secondary"
                      component="p"
                      data-testid="pest-image-attribution"
                      sx={{
                        mt: 0.25,
                        lineHeight: 1.2,
                        wordBreak: 'break-word',
                        display: 'block',
                      }}
                    >
                      {captionParts.join(' · ')}
                    </Typography>
                  )}
                </Box>
              );
            }

            return (
              <Box
                key={img.id}
                role="listitem"
                sx={{ position: 'relative', opacity: isDeselected ? 0.45 : 1 }}
                data-testid="pest-image-tile"
              >
                <AuthImage
                  uri={img.thumbnail_uri ?? img.uri}
                  alt={
                    isInspection
                      ? t('pages.pestDetail.imageFromInspectionAlt', { name: pestName })
                      : img.caption || t('pages.pestDetail.imageAlt', { name: pestName })
                  }
                  height={140}
                  sx={{ borderRadius: 1, width: '100%', objectFit: 'cover' }}
                  data-testid="pest-detail-image"
                />
                {isInspection && (
                  <Tooltip title={t('pages.pestDetail.imageFromInspection')}>
                    <Chip
                      icon={<SearchIcon />}
                      size="small"
                      color="info"
                      variant="outlined"
                      label={t('pages.pestDetail.imageFromInspectionShort')}
                      aria-label={t('pages.pestDetail.imageFromInspection')}
                      sx={{
                        position: 'absolute',
                        top: 4,
                        left: 4,
                        cursor: 'default',
                        bgcolor: 'background.paper',
                      }}
                      data-testid="pest-image-inspection"
                    />
                  </Tooltip>
                )}
                {!isInspection && img.status === 'promoted' && (
                  <Tooltip title={t('pages.pestDetail.imageGlobal')}>
                    <Chip
                      icon={<PublicIcon />}
                      size="small"
                      color="success"
                      label={t('pages.pestDetail.imageGlobalShort')}
                      aria-label={t('pages.pestDetail.imageGlobal')}
                      sx={{ position: 'absolute', top: 4, left: 4, cursor: 'default' }}
                      data-testid="pest-image-global"
                    />
                  </Tooltip>
                )}
                {isDeselected && <DeselectedBadge label={t('pages.pestDetail.imageDeselectedBadge')} />}
                {/*
                 * Action buttons (top-right). The owner's delete and the admin
                 * curation toggle are mutually exclusive per tile: own
                 * contributions keep the delete affordance; foreign / recognition
                 * tiles get the admin curation toggle instead.
                 */}
                {!isInspection && img.is_own && (
                  <Tooltip title={t('pages.pestDetail.imageDelete')}>
                    <IconButton
                      size="small"
                      onClick={() => handleDeleteRequest(img.id)}
                      aria-label={t('pages.pestDetail.imageDelete')}
                      data-testid="pest-image-delete"
                      sx={{
                        position: 'absolute',
                        top: 4,
                        right: 4,
                        // Minimum 48×48px touch target per UI-NFR-001 R-011.
                        minWidth: 48,
                        minHeight: 48,
                        bgcolor: 'background.paper',
                        '&:hover': { bgcolor: 'background.paper' },
                        // Ensure the focus ring is visible over the image (UI-NFR-002 R-005).
                        '&:focus-visible': {
                          outline: '2px solid',
                          outlineColor: 'primary.main',
                          outlineOffset: 2,
                        },
                      }}
                    >
                      <DeleteOutlineIcon fontSize="small" />
                    </IconButton>
                  </Tooltip>
                )}
                {!img.is_own && canCurate && (
                  <CurationButton
                    active={isActive}
                    busy={toggling}
                    onToggle={() => handleToggleActive(img, !isActive)}
                    deselectLabel={t('pages.pestDetail.imageDeselect')}
                    reactivateLabel={t('pages.pestDetail.imageReactivate')}
                  />
                )}
              </Box>
            );
          })}
        </Box>
      )}

      {/* Empty state */}
      {!loading && images.length === 0 && (
        <Typography
          variant="body2"
          color="text.secondary"
          data-testid="pest-detail-no-images"
          aria-live="polite"
        >
          {t('pages.pestDetail.noImages')}
        </Typography>
      )}

      {/* Deletion confirmation — uses the project-standard ConfirmDialog */}
      <ConfirmDialog
        open={pendingDeleteId !== null}
        title={t('pages.pestDetail.imageDeleteConfirmTitle')}
        message={t('pages.pestDetail.imageDeleteConfirmMessage')}
        onConfirm={handleDeleteConfirm}
        onCancel={handleDeleteCancel}
        destructive
        loading={deleting}
      />

      <PestImageContributeDialog
        open={dialogOpen}
        onClose={() => setDialogOpen(false)}
        pestKey={pestKey}
        onUploaded={load}
      />
    </Box>
  );
}

/** A "deselected" provenance badge for an inactive (admin-only) tile. */
function DeselectedBadge({ label }: { label: string }) {
  return (
    <Tooltip title={label}>
      <Chip
        icon={<VisibilityOffOutlinedIcon />}
        size="small"
        color="warning"
        variant="outlined"
        label={label}
        aria-label={label}
        data-testid="pest-image-deselected-badge"
        sx={{ position: 'absolute', bottom: 4, left: 4, cursor: 'default', bgcolor: 'background.paper' }}
      />
    </Tooltip>
  );
}

interface CurationButtonProps {
  active: boolean;
  busy: boolean;
  onToggle: () => void;
  deselectLabel: string;
  reactivateLabel: string;
}

/** Platform-admin deselect / re-include toggle for one tile. */
function CurationButton({ active, busy, onToggle, deselectLabel, reactivateLabel }: CurationButtonProps) {
  const label = active ? deselectLabel : reactivateLabel;
  return (
    <Tooltip title={label}>
      <span style={{ position: 'absolute', top: 4, right: 4 }}>
        <IconButton
          size="small"
          onClick={onToggle}
          disabled={busy}
          aria-label={label}
          data-testid="pest-image-deselect"
          sx={{
            // Minimum 48×48px touch target per UI-NFR-001 R-011.
            minWidth: 48,
            minHeight: 48,
            bgcolor: 'background.paper',
            '&:hover': { bgcolor: 'background.paper' },
            '&:focus-visible': {
              outline: '2px solid',
              outlineColor: 'primary.main',
              outlineOffset: 2,
            },
          }}
        >
          {active ? (
            <VisibilityOffOutlinedIcon fontSize="small" />
          ) : (
            <VisibilityOutlinedIcon fontSize="small" />
          )}
        </IconButton>
      </span>
    </Tooltip>
  );
}
