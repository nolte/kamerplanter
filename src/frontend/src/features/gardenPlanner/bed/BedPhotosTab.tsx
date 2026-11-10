/**
 * The photo gallery of a bed (REQ-053 GP-FR-051): the bed's photos newest first, upload (camera or file), the
 * cover photo shown in the bed head and the field-mode sheet, and remove. Every member sees the photos; adding
 * and choosing the cover needs a write right, and remove is offered only where the server says `can_remove`
 * (an own upload from `grower`, any photo as `lead`). A bed holds at most 50 photos.
 *
 * Loaded as its own chunk when the tab opens. Photo URIs go to `AuthImage` only and are never logged.
 */
import { lazy, Suspense, useCallback, useEffect, useState } from 'react';
import { useTranslation } from 'react-i18next';
import Alert from '@mui/material/Alert';
import Box from '@mui/material/Box';
import Button from '@mui/material/Button';
import Card from '@mui/material/Card';
import CardActionArea from '@mui/material/CardActionArea';
import CardActions from '@mui/material/CardActions';
import Chip from '@mui/material/Chip';
import IconButton from '@mui/material/IconButton';
import Tooltip from '@mui/material/Tooltip';
import Typography from '@mui/material/Typography';
import AddPhotoAlternateIcon from '@mui/icons-material/AddPhotoAlternate';
import DeleteIcon from '@mui/icons-material/Delete';
import StarIcon from '@mui/icons-material/Star';
import StarBorderIcon from '@mui/icons-material/StarBorder';
import AuthImage from '@/components/common/AuthImage';
import ConfirmDialog from '@/components/common/ConfirmDialog';
import EmptyState from '@/components/common/EmptyState';
import ErrorDisplay from '@/components/common/ErrorDisplay';
import LoadingSkeleton from '@/components/common/LoadingSkeleton';
import { useApiError } from '@/hooks/useApiError';
import { useNotification } from '@/hooks/useNotification';
import { formatDate } from '@/utils/formatting';
import {
  addBedPhoto,
  listBedPhotos,
  removeBedPhoto,
  setBedCoverPhoto,
  type BedPhoto,
  type BedPhotoGallery,
} from './bedPhotoApi';
import { BED_PHOTO_LIMIT, bedPhotoUploadError } from './bedPhotoMessages';

const PlantPhotoUploadDialog = lazy(() => import('@/components/photos/PlantPhotoUploadDialog'));
const DiaryPhotoLightbox = lazy(() => import('@/components/diary/DiaryPhotoLightbox'));

/** WCAG 2.5.5 / UI-NFR-001: icon controls in the card bar are at least 44 px. */
const ICON_TARGET = 44;

interface BedPhotosTabProps {
  bedKey: string;
  bedName: string;
  /** The cover the bed head shows now; a gallery answer with another cover reloads the head. */
  coverPhotoRef: string | null;
  /** `grower` and up may add photos and choose the cover. */
  canEdit: boolean;
  /** The cover changed on the server; the bed head reloads. */
  onCoverChange: () => void;
}

type LoadState = { status: 'loading' } | { status: 'error' } | { status: 'ready'; gallery: BedPhotoGallery };

export default function BedPhotosTab({ bedKey, bedName, coverPhotoRef, canEdit, onCoverChange }: BedPhotosTabProps) {
  const { t } = useTranslation();
  const { handleError } = useApiError();
  const notification = useNotification();
  const [state, setState] = useState<LoadState>({ status: 'loading' });
  const [uploadOpen, setUploadOpen] = useState(false);
  const [lightboxIndex, setLightboxIndex] = useState<number | null>(null);
  const [removeTarget, setRemoveTarget] = useState<BedPhoto | null>(null);
  const [removing, setRemoving] = useState(false);
  const [busyId, setBusyId] = useState<string | null>(null);

  // `version` re-reads the gallery on retry; the key of the bed is fixed per mount (`BedView` keys the tab).
  const [version, setVersion] = useState(0);
  useEffect(() => {
    let cancelled = false;
    listBedPhotos(bedKey).then(
      (gallery) => {
        if (!cancelled) setState({ status: 'ready', gallery });
      },
      () => {
        if (!cancelled) setState({ status: 'error' });
      },
    );
    return () => {
      cancelled = true;
    };
  }, [bedKey, version]);

  const retry = () => {
    setState({ status: 'loading' });
    setVersion((value) => value + 1);
  };

  /** Show the server's answer; a changed cover reloads the bed head. */
  const apply = useCallback(
    (gallery: BedPhotoGallery) => {
      setState({ status: 'ready', gallery });
      if (gallery.cover_photo_ref !== coverPhotoRef) onCoverChange();
    },
    [coverPhotoRef, onCoverChange],
  );

  const upload = useCallback(async (file: File) => apply(await addBedPhoto(bedKey, file)), [apply, bedKey]);
  const uploadError = useCallback((error: unknown) => bedPhotoUploadError(t, error), [t]);

  const changeCover = async (photo: BedPhoto, attachmentId: string | null) => {
    setBusyId(photo.attachment_id);
    try {
      apply(await setBedCoverPhoto(bedKey, attachmentId));
      notification.success(t(attachmentId ? 'pages.bed.photos.coverSet' : 'pages.bed.photos.coverCleared'));
    } catch (error) {
      handleError(error);
    } finally {
      setBusyId(null);
    }
  };

  const confirmRemove = async () => {
    if (!removeTarget) return;
    setRemoving(true);
    try {
      apply(await removeBedPhoto(bedKey, removeTarget.attachment_id));
      notification.success(t('pages.bed.photos.removed'));
    } catch (error) {
      handleError(error);
    } finally {
      setRemoving(false);
      setRemoveTarget(null);
      setLightboxIndex(null);
    }
  };

  if (state.status === 'loading') return <LoadingSkeleton variant="card" />;
  if (state.status === 'error') return <ErrorDisplay error={t('pages.bed.photos.loadError')} onRetry={retry} />;

  const { photos } = state.gallery;
  const max = state.gallery.max_photos || BED_PHOTO_LIMIT;
  const full = photos.length >= max;
  const openUpload = () => setUploadOpen(true);

  return (
    <Box component="section" aria-labelledby="bed-photos-title" data-testid="bed-photos">
      <Box
        sx={{
          display: 'flex',
          flexDirection: { xs: 'column', sm: 'row' },
          alignItems: { xs: 'stretch', sm: 'flex-start' },
          justifyContent: 'space-between',
          gap: 2,
          mb: 2,
        }}
      >
        <Box sx={{ minWidth: 0 }}>
          <Typography id="bed-photos-title" component="h2" variant="subtitle1" sx={{ fontWeight: 600 }}>
            {t('pages.bed.photos.title')}
          </Typography>
          <Typography variant="body2" color="text.secondary">
            {t('pages.bed.photos.intro')}
          </Typography>
          {photos.length > 0 && (
            <Typography variant="caption" color="text.secondary" component="div" data-testid="bed-photos-count">
              {t('pages.bed.photos.count', { count: photos.length, max })}
            </Typography>
          )}
        </Box>
        {canEdit && (
          <Button
            variant="contained"
            startIcon={<AddPhotoAlternateIcon />}
            onClick={openUpload}
            disabled={full}
            sx={{ minHeight: ICON_TARGET, flexShrink: 0 }}
            data-testid="bed-photos-add"
          >
            {t('pages.bed.photos.add')}
          </Button>
        )}
      </Box>

      {full && (
        <Alert severity="info" sx={{ mb: 2 }} data-testid="bed-photos-limit">
          {t('pages.bed.photos.limitReached', { max })}
        </Alert>
      )}

      {photos.length === 0 ? (
        <EmptyState
          message={t('pages.bed.photos.emptyTitle')}
          description={t(canEdit ? 'pages.bed.photos.emptyDescriptionWrite' : 'pages.bed.photos.emptyDescriptionRead')}
          actionLabel={canEdit ? t('pages.bed.photos.addFirst') : undefined}
          onAction={canEdit ? openUpload : undefined}
        />
      ) : (
        <Box
          component="ul"
          aria-label={t('pages.bed.photos.listLabel', { bed: bedName })}
          sx={{
            listStyle: 'none',
            p: 0,
            m: 0,
            display: 'grid',
            gridTemplateColumns: { xs: 'repeat(2, 1fr)', sm: 'repeat(3, 1fr)', md: 'repeat(4, 1fr)' },
            gap: { xs: 1, sm: 1.5 },
          }}
        >
          {photos.map((photo, index) => {
            const busy = busyId === photo.attachment_id;
            const date = formatDate(photo.taken_on ?? photo.created_at);
            const showActions = canEdit || photo.can_remove;
            return (
              <Card
                component="li"
                key={photo.attachment_id}
                variant="outlined"
                sx={{ position: 'relative', display: 'flex', flexDirection: 'column' }}
                data-testid={`bed-photo-${photo.attachment_id}`}
              >
                <CardActionArea
                  onClick={() => setLightboxIndex(index)}
                  aria-label={t('pages.bed.photos.open', { date })}
                  data-testid={`bed-photo-open-${photo.attachment_id}`}
                >
                  <AuthImage
                    uri={photo.thumbnail_uris?.medium ?? photo.uri}
                    alt=""
                    sx={{ width: '100%', aspectRatio: '1 / 1' }}
                    height="auto"
                  />
                </CardActionArea>
                {photo.is_cover && (
                  <Chip
                    icon={<StarIcon />}
                    label={t('pages.bed.photos.cover')}
                    color="primary"
                    size="small"
                    sx={{ position: 'absolute', top: 6, left: 6, maxWidth: 'calc(100% - 12px)' }}
                    data-testid={`bed-photo-cover-${photo.attachment_id}`}
                  />
                )}
                <Box sx={{ px: 1, pt: 0.5 }}>
                  <Typography variant="caption" color="text.secondary">
                    {date}
                  </Typography>
                </Box>
                {showActions && (
                  <CardActions disableSpacing sx={{ justifyContent: 'flex-end', gap: 0.5, mt: 'auto', p: 0.5 }}>
                    {canEdit && (
                      <Tooltip title={t(photo.is_cover ? 'pages.bed.photos.clearCover' : 'pages.bed.photos.setCover')}>
                        <span>
                          <IconButton
                            onClick={() => void changeCover(photo, photo.is_cover ? null : photo.attachment_id)}
                            disabled={busy}
                            // A toggle button: a constant name, the state in `aria-pressed` (the tooltip says the action).
                            aria-label={t('pages.bed.photos.coverToggle')}
                            aria-pressed={photo.is_cover}
                            color={photo.is_cover ? 'primary' : 'default'}
                            sx={{ width: ICON_TARGET, height: ICON_TARGET }}
                            data-testid={`bed-photo-toggle-cover-${photo.attachment_id}`}
                          >
                            {photo.is_cover ? <StarIcon /> : <StarBorderIcon />}
                          </IconButton>
                        </span>
                      </Tooltip>
                    )}
                    {photo.can_remove && (
                      <Tooltip title={t('pages.bed.photos.remove')}>
                        <span>
                          <IconButton
                            onClick={() => setRemoveTarget(photo)}
                            disabled={busy}
                            aria-label={t('pages.bed.photos.remove')}
                            sx={{ width: ICON_TARGET, height: ICON_TARGET }}
                            data-testid={`bed-photo-remove-${photo.attachment_id}`}
                          >
                            <DeleteIcon />
                          </IconButton>
                        </span>
                      </Tooltip>
                    )}
                  </CardActions>
                )}
              </Card>
            );
          })}
        </Box>
      )}

      <ConfirmDialog
        open={removeTarget !== null}
        title={t('pages.bed.photos.removeTitle')}
        message={t('pages.bed.photos.removeMessage')}
        confirmLabel={t('pages.bed.photos.remove')}
        destructive
        loading={removing}
        onConfirm={() => void confirmRemove()}
        onCancel={() => setRemoveTarget(null)}
      />

      <Suspense fallback={null}>
        {uploadOpen && (
          <PlantPhotoUploadDialog
            open
            upload={upload}
            title={t('pages.bed.photos.uploadTitle', { bed: bedName })}
            errorMessage={uploadError}
            photoTips={false}
            onClose={() => setUploadOpen(false)}
            onUploaded={() => notification.success(t('pages.bed.photos.added'))}
          />
        )}
        {lightboxIndex !== null && (
          <DiaryPhotoLightbox
            photoRefs={photos.map((photo) => photo.attachment_id)}
            index={lightboxIndex}
            alt={t('pages.bed.photos.fullAlt', { bed: bedName })}
            onClose={() => setLightboxIndex(null)}
            onNavigate={setLightboxIndex}
          />
        )}
      </Suspense>
    </Box>
  );
}
