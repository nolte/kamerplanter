import { useCallback, useState } from 'react';
import { useTranslation } from 'react-i18next';
import Box from '@mui/material/Box';
import Card from '@mui/material/Card';
import CardActionArea from '@mui/material/CardActionArea';
import AuthImage from '@/components/common/AuthImage';
import { diaryPhotoUri } from '@/api/endpoints/diary';
import DiaryPhotoLightbox from './DiaryPhotoLightbox';

interface DiaryPhotoStripProps {
  /** Attachment ids from the entry's `photo_refs`, in stored order. */
  photoRefs: string[];
}

/**
 * REQ-051 §6.1 — a diary entry's photos as previews with a lightbox.
 *
 * The grid loads the **512-px** rendition, as the specification requires; the
 * 1280-px one is fetched only when a photo is actually opened. Same discipline
 * as the gallery grid (REQ-034 AC-02): a list of ten entries with five photos
 * each would otherwise pull fifty full-size images to show fifty thumbnails.
 */
export default function DiaryPhotoStrip({ photoRefs }: DiaryPhotoStripProps) {
  const { t } = useTranslation();
  const [openIndex, setOpenIndex] = useState<number | null>(null);

  const handleClose = useCallback(() => setOpenIndex(null), []);

  if (photoRefs.length === 0) return null;

  return (
    <>
      <Box
        sx={{
          display: 'grid',
          // Mobile-first: three across on a phone, more as space allows.
          gridTemplateColumns: {
            xs: 'repeat(3, 1fr)',
            sm: 'repeat(4, 1fr)',
            md: 'repeat(5, 1fr)',
          },
          gap: { xs: 0.75, sm: 1 },
          mt: 1,
        }}
        data-testid="diary-photo-strip"
      >
        {photoRefs.map((attachmentId, index) => (
          <Card key={attachmentId} variant="outlined">
            <CardActionArea
              onClick={() => setOpenIndex(index)}
              aria-label={t('pages.plantDiary.photos.openPhoto', {
                index: index + 1,
                total: photoRefs.length,
              })}
              data-testid="diary-photo-thumb"
            >
              <AuthImage
                uri={diaryPhotoUri(attachmentId, 512)}
                /* The action area already carries the label; an identical alt
                   text would make screen readers announce it twice. */
                alt=""
                sx={{ width: '100%', aspectRatio: '1 / 1', bgcolor: 'action.hover' }}
                data-testid="diary-photo-image"
              />
            </CardActionArea>
          </Card>
        ))}
      </Box>

      <DiaryPhotoLightbox
        photoRefs={photoRefs}
        index={openIndex}
        onClose={handleClose}
        onNavigate={setOpenIndex}
      />
    </>
  );
}
