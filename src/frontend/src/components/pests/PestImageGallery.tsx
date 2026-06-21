import { useCallback, useEffect, useMemo, useState } from 'react';
import { useTranslation } from 'react-i18next';
import { useNotification } from '@/hooks/useNotification';
import Box from '@mui/material/Box';
import Button from '@mui/material/Button';
import Chip from '@mui/material/Chip';
import IconButton from '@mui/material/IconButton';
import Skeleton from '@mui/material/Skeleton';
import Tooltip from '@mui/material/Tooltip';
import Typography from '@mui/material/Typography';
import AddAPhotoIcon from '@mui/icons-material/AddAPhoto';
import DeleteOutlineIcon from '@mui/icons-material/DeleteOutlined';
import PublicIcon from '@mui/icons-material/Public';
import AuthImage from '@/components/common/AuthImage';
import ConfirmDialog from '@/components/common/ConfirmDialog';
import PestImageContributeDialog from './PestImageContributeDialog';
import { listPestImages, deletePestImage } from '@/api/endpoints/ipm';
import type { PestImage } from '@/api/types';

interface PestImageGalleryProps {
  pestKey: string;
  pestName: string;
}

/**
 * REQ-010 — gallery of user-contributed reference images for a pest.
 *
 * Shows the tenant's own photos (and, once promoted, globally shared ones),
 * lets the user contribute an own photo (upload or camera) and delete their
 * own. Tenant-scoped; in light mode (no tenant) contribution is unavailable.
 */
export default function PestImageGallery({ pestKey, pestName }: PestImageGalleryProps) {
  const { t } = useTranslation();
  const notification = useNotification();
  const [images, setImages] = useState<PestImage[]>([]);
  const [loading, setLoading] = useState(true);
  const [dialogOpen, setDialogOpen] = useState(false);
  /** ID of the image pending deletion — null means the dialog is closed. */
  const [pendingDeleteId, setPendingDeleteId] = useState<string | null>(null);
  const [deleting, setDeleting] = useState(false);

  const load = useCallback(async () => {
    setLoading(true);
    try {
      setImages(await listPestImages(pestKey));
    } catch {
      setImages([]);
    } finally {
      setLoading(false);
    }
  }, [pestKey]);

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

      {/* Loading skeleton — prevents layout shift and signals busy state */}
      {loading && (
        <Box
          sx={{
            display: 'grid',
            gridTemplateColumns: { xs: 'repeat(2, 1fr)', sm: 'repeat(3, 1fr)', md: 'repeat(4, 1fr)' },
            gap: 1,
          }}
          aria-busy="true"
          aria-label={t('pages.pestDetail.sectionImages')}
        >
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
          {images.map((img) => (
            <Box key={img.id} role="listitem" sx={{ position: 'relative' }}>
              <AuthImage
                uri={img.thumbnail_uri ?? img.uri}
                alt={img.caption || t('pages.pestDetail.imageAlt', { name: pestName })}
                height={140}
                sx={{ borderRadius: 1, width: '100%', objectFit: 'cover' }}
                data-testid="pest-detail-image"
              />
              {img.status === 'promoted' && (
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
              {img.is_own && (
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
            </Box>
          ))}
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
