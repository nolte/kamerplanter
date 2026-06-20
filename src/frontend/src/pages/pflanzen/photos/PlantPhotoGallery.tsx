import { useCallback, useEffect, useMemo, useState } from 'react';
import { useTranslation } from 'react-i18next';
import Box from '@mui/material/Box';
import Button from '@mui/material/Button';
import Card from '@mui/material/Card';
import CardActionArea from '@mui/material/CardActionArea';
import Chip from '@mui/material/Chip';
import IconButton from '@mui/material/IconButton';
import Tooltip from '@mui/material/Tooltip';
import Typography from '@mui/material/Typography';
import AddPhotoAlternateIcon from '@mui/icons-material/AddPhotoAlternate';
import StarIcon from '@mui/icons-material/Star';
import StarBorderIcon from '@mui/icons-material/StarBorder';
import DeleteIcon from '@mui/icons-material/Delete';
import EditIcon from '@mui/icons-material/Edit';
import { formatDate } from '@/utils/formatting';
import AuthImage from '@/components/common/AuthImage';
import EmptyState from '@/components/common/EmptyState';
import LoadingSkeleton from '@/components/common/LoadingSkeleton';
import ErrorDisplay from '@/components/common/ErrorDisplay';
import ConfirmDialog from '@/components/common/ConfirmDialog';
import { useNotification } from '@/hooks/useNotification';
import { useApiError } from '@/hooks/useApiError';
import { useTenantPermissions } from '@/hooks/useTenantPermissions';
import {
  listPlantPhotos,
  setCoverPhoto,
  deletePlantPhoto,
  type PlantPhoto,
} from '@/api/endpoints/plantPhotos';
import PlantPhotoUploadDialog from './PlantPhotoUploadDialog';
import PlantPhotoLightbox from './PlantPhotoLightbox';
import PlantPhotoEditDialog from './PlantPhotoEditDialog';

interface PlantPhotoGalleryProps {
  plantInstanceKey: string;
  /** Disable write actions when the instance is removed/read-only. */
  readOnly?: boolean;
  /** Notify the parent page when the cover photo may have changed (info-tab preview). */
  onCoverChange?: () => void;
}

/**
 * REQ-034 §2.3 — the "Photos" gallery tab of a plant instance.
 *
 * Renders a thumbnail grid from the medium (512px) renditions only (AC-02); the
 * original is loaded exclusively in the lightbox. Upload reuses the recognition
 * capture flow; each photo can be set as cover or deleted (with confirmation).
 * Write actions are hidden for viewers (AC-13) — the backend additionally
 * enforces a 403.
 */
export default function PlantPhotoGallery({
  plantInstanceKey,
  readOnly = false,
  onCoverChange,
}: PlantPhotoGalleryProps) {
  const { t } = useTranslation();
  const notification = useNotification();
  const { handleError } = useApiError();
  const { canEdit } = useTenantPermissions();
  const canWrite = canEdit && !readOnly;

  const [photos, setPhotos] = useState<PlantPhoto[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [uploadOpen, setUploadOpen] = useState(false);
  const [lightboxPhoto, setLightboxPhoto] = useState<PlantPhoto | null>(null);
  const [editTarget, setEditTarget] = useState<PlantPhoto | null>(null);
  const [deleteTarget, setDeleteTarget] = useState<PlantPhoto | null>(null);
  const [deleting, setDeleting] = useState(false);
  const [busyId, setBusyId] = useState<string | null>(null);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const result = await listPlantPhotos(plantInstanceKey);
      setPhotos(result.photos);
    } catch (err) {
      setError(String(err));
    } finally {
      setLoading(false);
    }
  }, [plantInstanceKey]);

  useEffect(() => {
    load();
  }, [load]);

  const handleUploaded = useCallback(() => {
    load();
    onCoverChange?.();
  }, [load, onCoverChange]);

  const handleSetCover = useCallback(
    async (photo: PlantPhoto) => {
      setBusyId(photo.attachment_id);
      try {
        const result = await setCoverPhoto(plantInstanceKey, photo.attachment_id);
        setPhotos(result.photos);
        notification.success(t('pages.plantPhotos.coverSet'));
        onCoverChange?.();
      } catch (err) {
        handleError(err);
      } finally {
        setBusyId(null);
      }
    },
    [plantInstanceKey, notification, handleError, t, onCoverChange],
  );

  const handleMetadataSaved = useCallback(
    (updated: PlantPhoto) => {
      // Patch the edited photo in place — caption/taken_on do not affect order
      // or cover, so a full reload is unnecessary.
      setPhotos((prev) =>
        prev.map((p) => (p.attachment_id === updated.attachment_id ? { ...p, ...updated } : p)),
      );
      // Keep an open lightbox in sync with the freshly saved metadata.
      setLightboxPhoto((prev) =>
        prev && prev.attachment_id === updated.attachment_id ? { ...prev, ...updated } : prev,
      );
      notification.success(t('pages.plantPhotos.metadataSaved'));
    },
    [notification, t],
  );

  const handleConfirmDelete = useCallback(async () => {
    if (!deleteTarget) return;
    setDeleting(true);
    try {
      await deletePlantPhoto(plantInstanceKey, deleteTarget.attachment_id);
      notification.success(t('pages.plantPhotos.deleted'));
      setDeleteTarget(null);
      await load();
      onCoverChange?.();
    } catch (err) {
      handleError(err);
    } finally {
      setDeleting(false);
    }
  }, [deleteTarget, plantInstanceKey, notification, handleError, t, load, onCoverChange]);

  // Stable computed value — useMemo obligation per FRONTEND.md hook conventions.
  const emptyDescription = useMemo(
    () =>
      canWrite
        ? t('pages.plantPhotos.emptyDescriptionWrite')
        : t('pages.plantPhotos.emptyDescriptionRead'),
    [canWrite, t],
  );

  if (loading) return <LoadingSkeleton variant="card" />;
  if (error) return <ErrorDisplay error={error} onRetry={load} />;

  return (
    <Box data-testid="plant-photo-gallery">
      {/* Section heading + intro (UI-NFR-008 R-038) */}
      <Box
        sx={{
          display: 'flex',
          alignItems: { xs: 'flex-start', sm: 'center' },
          justifyContent: 'space-between',
          gap: 2,
          mb: 2,
          flexWrap: 'wrap',
        }}
      >
        <Box>
          <Typography variant="subtitle1" sx={{ fontWeight: 600 }}>
            {t('pages.plantPhotos.sectionTitle')}
          </Typography>
          <Typography variant="body2" color="text.secondary">
            {t('pages.plantPhotos.intro')}
          </Typography>
        </Box>
        {canWrite && (
          <Button
            variant="contained"
            startIcon={<AddPhotoAlternateIcon />}
            onClick={() => setUploadOpen(true)}
            data-testid="plant-photo-add-button"
            /* Minimum 44×44 touch target (UI-NFR-001 R-008) — contained Button
               height is 36px by default; sx padding compensates on mobile. */
            sx={{ minHeight: 44, px: { xs: 2.5, sm: 2 } }}
          >
            {t('pages.plantPhotos.addPhoto')}
          </Button>
        )}
      </Box>

      {photos.length === 0 ? (
        <EmptyState
          message={t('pages.plantPhotos.emptyTitle')}
          description={emptyDescription}
          actionLabel={canWrite ? t('pages.plantPhotos.addPhotoFirst') : undefined}
          onAction={canWrite ? () => setUploadOpen(true) : undefined}
        />
      ) : (
        <Box
          sx={{
            display: 'grid',
            // Mobile-first: 2 columns on xs, 3 on sm, 4 on md, 5 on lg (UI-NFR-001)
            gridTemplateColumns: {
              xs: 'repeat(2, 1fr)',
              sm: 'repeat(3, 1fr)',
              md: 'repeat(4, 1fr)',
              lg: 'repeat(5, 1fr)',
            },
            gap: { xs: 1, sm: 1.5, md: 2 },
          }}
        >
          {photos.map((photo) => {
            const thumb = photo.thumbnail_uris?.medium ?? photo.uri;
            const isBusy = busyId === photo.attachment_id;
            // Display date: explicit capture date, else the upload date (§2.1).
            const displayDate = formatDate(photo.taken_on ?? photo.created_at);
            return (
              <Card
                key={photo.attachment_id}
                sx={{ position: 'relative' }}
                data-testid="plant-photo-item"
              >
                <CardActionArea
                  onClick={() => setLightboxPhoto(photo)}
                  aria-label={t('pages.plantPhotos.openPhoto')}
                  data-testid="plant-photo-thumb"
                  /* Keyboard: Enter/Space activates — CardActionArea handles this. */
                >
                  {/* Authenticated blob fetch — a native <img src> cannot send the
                      JWT Bearer header the attachment endpoint requires (AC-02:
                      grid loads the medium rendition only, never the original). */}
                  <AuthImage
                    uri={thumb}
                    alt={t('pages.plantPhotos.thumbAlt')}
                    sx={{
                      width: '100%',
                      aspectRatio: '1 / 1',
                      bgcolor: 'action.hover',
                    }}
                    data-testid="plant-photo-image"
                  />
                </CardActionArea>

                {photo.is_cover && (
                  <Chip
                    icon={<StarIcon />}
                    label={t('pages.plantPhotos.cover')}
                    color="primary"
                    size="small"
                    sx={{
                      position: 'absolute',
                      top: 6,
                      left: 6,
                      // Ensure badge text never overflows narrow cards
                      maxWidth: 'calc(100% - 12px)',
                    }}
                    data-testid="plant-photo-cover-badge"
                  />
                )}

                {canWrite && (
                  <Box
                    sx={{
                      position: 'absolute',
                      bottom: 0,
                      right: 0,
                      left: 0,
                      display: 'flex',
                      justifyContent: 'flex-end',
                      gap: 0.25,
                      // Semi-transparent bar — always visible on touch devices,
                      // fades slightly on desktop hover for a cleaner look.
                      bgcolor: 'rgba(0, 0, 0, 0.50)',
                      borderBottomLeftRadius: 'inherit',
                      borderBottomRightRadius: 'inherit',
                      px: 0.5,
                      py: 0.25,
                    }}
                  >
                    {!photo.is_cover && (
                      <Tooltip title={t('pages.plantPhotos.setCover')}>
                        <span>
                          <IconButton
                            /* 40×40 effective touch target inside the 48px bar */
                            size="medium"
                            onClick={(e) => {
                              e.stopPropagation();
                              handleSetCover(photo);
                            }}
                            disabled={isBusy}
                            aria-label={t('pages.plantPhotos.setCover')}
                            sx={{ color: 'common.white', p: 0.75 }}
                            data-testid="plant-photo-set-cover"
                          >
                            <StarBorderIcon />
                          </IconButton>
                        </span>
                      </Tooltip>
                    )}
                    <Tooltip title={t('pages.plantPhotos.editPhoto')}>
                      <span>
                        <IconButton
                          size="medium"
                          onClick={(e) => {
                            e.stopPropagation();
                            setEditTarget(photo);
                          }}
                          disabled={isBusy}
                          aria-label={t('pages.plantPhotos.editPhoto')}
                          sx={{ color: 'common.white', p: 0.75 }}
                          data-testid="plant-photo-edit"
                        >
                          <EditIcon />
                        </IconButton>
                      </span>
                    </Tooltip>
                    <Tooltip title={t('pages.plantPhotos.deletePhoto')}>
                      <span>
                        <IconButton
                          size="medium"
                          onClick={(e) => {
                            e.stopPropagation();
                            setDeleteTarget(photo);
                          }}
                          disabled={isBusy}
                          aria-label={t('pages.plantPhotos.deletePhoto')}
                          sx={{ color: 'common.white', p: 0.75 }}
                          data-testid="plant-photo-delete"
                        >
                          <DeleteIcon />
                        </IconButton>
                      </span>
                    </Tooltip>
                  </Box>
                )}

                {/* Metadata under the thumbnail: capture date + 1-line caption
                    preview (§2.1). Always rendered (read-only for viewers). */}
                <Box sx={{ px: 1, py: 0.75 }} data-testid="plant-photo-meta">
                  <Typography
                    variant="caption"
                    color="text.secondary"
                    sx={{ display: 'block' }}
                    data-testid="plant-photo-date"
                  >
                    {displayDate}
                  </Typography>
                  {photo.caption && (
                    <Typography
                      variant="body2"
                      sx={{
                        // 1-line truncation — full text lives in the lightbox.
                        overflow: 'hidden',
                        textOverflow: 'ellipsis',
                        whiteSpace: 'nowrap',
                      }}
                      title={photo.caption}
                      data-testid="plant-photo-caption"
                    >
                      {photo.caption}
                    </Typography>
                  )}
                </Box>
              </Card>
            );
          })}
        </Box>
      )}

      <PlantPhotoUploadDialog
        open={uploadOpen}
        plantInstanceKey={plantInstanceKey}
        onClose={() => setUploadOpen(false)}
        onUploaded={handleUploaded}
      />
      <PlantPhotoLightbox
        photo={lightboxPhoto}
        onClose={() => setLightboxPhoto(null)}
        canWrite={canWrite}
        onSetCover={handleSetCover}
        onEdit={(photo) => setEditTarget(photo)}
        onDelete={(photo) => setDeleteTarget(photo)}
      />
      <PlantPhotoEditDialog
        photo={editTarget}
        plantInstanceKey={plantInstanceKey}
        onClose={() => setEditTarget(null)}
        onSaved={handleMetadataSaved}
      />
      <ConfirmDialog
        open={deleteTarget !== null}
        title={t('pages.plantPhotos.deleteTitle')}
        message={t('pages.plantPhotos.deleteConfirm')}
        confirmLabel={t('common.delete')}
        destructive
        loading={deleting}
        onConfirm={handleConfirmDelete}
        onCancel={() => setDeleteTarget(null)}
      />
    </Box>
  );
}
