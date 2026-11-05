/**
 * The cover photo of a bed (REQ-053 GP-FR-051) in the bed head and the field-mode bed sheet: the 512 px rendition
 * of `cover_photo_ref`, fetched with the bearer token. Nothing is rendered without a cover - and nothing either when
 * the photo cannot be loaded (a cover whose attachment is gone, a rendition that never became ready): a broken frame
 * in the bed head says less than no photo.
 */
import { useCallback, useState } from 'react';
import { useTranslation } from 'react-i18next';
import Box from '@mui/material/Box';
import type { SxProps, Theme } from '@mui/material/styles';
import AuthImage from '@/components/common/AuthImage';
import { attachmentUri } from '@/api/endpoints/attachments';

interface BedCoverPhotoProps {
  coverPhotoRef: string | null | undefined;
  bedName: string;
  /** Size and placement of the frame; the photo fills it. */
  sx?: SxProps<Theme>;
  testId: string;
}

export default function BedCoverPhoto({ coverPhotoRef, bedName, sx, testId }: BedCoverPhotoProps) {
  const { t } = useTranslation();
  // The ref whose image failed, not a flag: choosing another cover tries again without a reset effect.
  const [failedRef, setFailedRef] = useState<string | null>(null);
  const handleError = useCallback(() => setFailedRef(coverPhotoRef ?? null), [coverPhotoRef]);
  if (!coverPhotoRef || failedRef === coverPhotoRef) return null;
  return (
    <Box
      sx={[
        { borderRadius: 1, overflow: 'hidden', flexShrink: 0, bgcolor: 'action.hover' },
        ...(Array.isArray(sx) ? sx : [sx]),
      ]}
      data-testid={testId}
    >
      <AuthImage
        uri={attachmentUri(coverPhotoRef, 512)}
        alt={t('pages.bed.photos.coverAlt', { bed: bedName })}
        data-testid={`${testId}-image`}
        onError={handleError}
      />
    </Box>
  );
}
