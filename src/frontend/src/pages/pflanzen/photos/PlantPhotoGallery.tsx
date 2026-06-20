import { useCallback, useEffect, useState } from 'react';
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

  if (loading) return <LoadingSkeleton variant="card" />;
  if (error) return <ErrorDisplay error={error} onRetry={load} />;

  return (
    <Box data-testid="plant-photo-gallery">
      <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: 2, mb: 2, flexWrap: 'wrap' }}>
        <Typography variant="body2" color="text.secondary">
          {t('pages.plantPhotos.intro')}
        </Typography>
        {canWrite && (
          <Button
            variant="contained"
            startIcon={<AddPhotoAlternateIcon />}
            onClick={() => setUploadOpen(true)}
            data-testid="plant-photo-add-button"
          >
            {t('pages.plantPhotos.addPhoto')}
          </Button>
        )}
      </Box>

      {photos.length === 0 ? (
        <EmptyState
          message={t('pages.plantPhotos.emptyTitle')}
          description={t('pages.plantPhotos.emptyDescription')}
          actionLabel={canWrite ? t('pages.plantPhotos.addPhoto') : undefined}
          onAction={canWrite ? () => setUploadOpen(true) : undefined}
        />
      ) : (
        <Box
          sx={{
            display: 'grid',
            gridTemplateColumns: {
              xs: 'repeat(2, 1fr)',
              sm: 'repeat(3, 1fr)',
              md: 'repeat(4, 1fr)',
            },
            gap: { xs: 1.5, sm: 2 },
          }}
        >
          {photos.map((photo) => {
            const thumb = photo.thumbnail_uris?.medium ?? photo.uri;
            return (
              <Card key={photo.attachment_id} sx={{ position: 'relative' }} data-testid="plant-photo-item">
                <CardActionArea
                  onClick={() => setLightboxPhoto(photo)}
                  aria-label={t('pages.plantPhotos.openPhoto')}
                  data-testid="plant-photo-thumb"
                >
                  <Box
                    component="img"
                    src={thumb}
                    alt={t('pages.plantPhotos.thumbAlt')}
                    loading="lazy"
                    sx={{
                      display: 'block',
                      width: '100%',
                      aspectRatio: '1 / 1',
                      objectFit: 'cover',
                      bgcolor: 'action.hover',
                    }}
                  />
                </CardActionArea>

                {photo.is_cover && (
                  <Chip
                    icon={<StarIcon />}
                    label={t('pages.plantPhotos.cover')}
                    color="primary"
                    size="small"
                    sx={{ position: 'absolute', top: 8, left: 8 }}
                    data-testid="plant-photo-cover-badge"
                  />
                )}

                {canWrite && (
                  <Box
                    sx={{
                      position: 'absolute',
                      bottom: 4,
                      right: 4,
                      display: 'flex',
                      gap: 0.5,
                      bgcolor: 'rgba(0, 0, 0, 0.45)',
                      borderRadius: 1,
                    }}
                  >
                    {!photo.is_cover && (
                      <Tooltip title={t('pages.plantPhotos.setCover')}>
                        <span>
                          <IconButton
                            size="small"
                            onClick={() => handleSetCover(photo)}
                            disabled={busyId === photo.attachment_id}
                            aria-label={t('pages.plantPhotos.setCover')}
                            sx={{ color: 'common.white' }}
                            data-testid="plant-photo-set-cover"
                          >
                            <StarBorderIcon fontSize="small" />
                          </IconButton>
                        </span>
                      </Tooltip>
                    )}
                    <Tooltip title={t('common.delete')}>
                      <span>
                        <IconButton
                          size="small"
                          onClick={() => setDeleteTarget(photo)}
                          disabled={busyId === photo.attachment_id}
                          aria-label={t('common.delete')}
                          sx={{ color: 'common.white' }}
                          data-testid="plant-photo-delete"
                        >
                          <DeleteIcon fontSize="small" />
                        </IconButton>
                      </span>
                    </Tooltip>
                  </Box>
                )}
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
      <PlantPhotoLightbox photo={lightboxPhoto} onClose={() => setLightboxPhoto(null)} />
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
