import { useMemo, useState } from 'react';
import { useTranslation } from 'react-i18next';
import ImageList from '@mui/material/ImageList';
import ImageListItem from '@mui/material/ImageListItem';
import ImageListItemBar from '@mui/material/ImageListItemBar';
import Tooltip from '@mui/material/Tooltip';
import useMediaQuery from '@mui/material/useMediaQuery';
import { useTheme } from '@mui/material/styles';
import InfoOutlinedIcon from '@mui/icons-material/InfoOutlined';
import { stripHtml } from '@/utils/formatting';
import type { ReferenceImage } from '@/api/types';

/** Builds the "© {attribution} · {license}" caption, omitting empty parts. */
function buildCaption(image: ReferenceImage): string {
  const parts: string[] = [];
  // Attributions from Wikimedia can contain HTML markup — strip it to text.
  const attribution = stripHtml(image.attribution);
  if (attribution) parts.push(`© ${attribution}`);
  if (image.license) parts.push(image.license);
  return parts.join(' · ');
}

interface GalleryTileProps {
  image: ReferenceImage;
  /** Scientific name used as the accessible image alt when no organ label is available. */
  scientificName?: string;
}

/** Single gallery tile that hides itself when its external image fails to load. */
function GalleryTile({ image, scientificName }: GalleryTileProps) {
  const { t } = useTranslation();
  const [failed, setFailed] = useState(false);

  if (failed) return null;

  const caption = buildCaption(image);
  const organLabel = image.organ
    ? t(`pages.species.referenceImages.organ.${image.organ}`, { defaultValue: image.organ })
    : undefined;

  // Build a meaningful alt: "Organ – Scientific name" or fallback to generic.
  const altText =
    [organLabel, scientificName].filter(Boolean).join(' – ') ||
    t('pages.species.referenceImages.imageAlt');

  return (
    <ImageListItem data-testid="reference-image-item">
      <img
        src={image.source_url}
        alt={altText}
        loading="lazy"
        referrerPolicy="no-referrer"
        onError={() => setFailed(true)}
        style={{ objectFit: 'cover', width: '100%', height: '100%' }}
      />
      {(caption || organLabel) && (
        <ImageListItemBar
          title={organLabel}
          subtitle={caption || undefined}
          actionIcon={
            caption ? (
              <Tooltip title={caption} enterTouchDelay={0} leaveTouchDelay={4000}>
                <InfoOutlinedIcon
                  fontSize="small"
                  aria-label={t('pages.species.referenceImages.attributionIconLabel')}
                  tabIndex={0}
                  sx={{ color: 'rgba(255,255,255,0.7)', mr: 0.5, cursor: 'default', fontSize: 16 }}
                />
              </Tooltip>
            ) : undefined
          }
          sx={{
            // Dark gradient ensures text is readable over any image.
            background:
              'linear-gradient(to top, rgba(0,0,0,0.72) 0%, rgba(0,0,0,0.36) 60%, transparent 100%)',
            '& .MuiImageListItemBar-title': { fontSize: '0.75rem', lineHeight: 1.3 },
            '& .MuiImageListItemBar-subtitle': {
              fontSize: '0.68rem',
              lineHeight: 1.2,
              whiteSpace: 'normal',
              // Ensure multi-word attributions wrap, not clip.
              overflow: 'visible',
            },
          }}
        />
      )}
    </ImageListItem>
  );
}

interface ReferenceImageGridProps {
  images: ReferenceImage[];
  /** Scientific name used for aria-label and image alt fallback. */
  scientificName?: string;
  /** Accessible label for the ImageList (defaults to the reference-image title). */
  ariaLabel?: string;
}

/**
 * Read-only grid of external CC-BY/CC0 reference images (REQ-029-A).
 *
 * Shared between the species detail page and the plant-instance photo gallery so
 * the tile/attribution rendering (organ label, CC-BY caption, self-hiding broken
 * tiles) lives in exactly one place. Purely presentational: fetching, empty-state
 * and loading are the caller's responsibility. Never mutates images.
 *
 * Responsive column count: 2 (xs), 3 (sm), 4 (md+) — fills available width.
 */
export default function ReferenceImageGrid({
  images,
  scientificName,
  ariaLabel,
}: ReferenceImageGridProps) {
  const { t } = useTranslation();
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down('sm'));
  const isTablet = useMediaQuery(theme.breakpoints.between('sm', 'md'));

  const cols = useMemo(() => {
    if (isMobile) return 2;
    if (isTablet) return 3;
    return 4;
  }, [isMobile, isTablet]);

  const resolvedAriaLabel =
    ariaLabel ??
    (scientificName
      ? t('pages.species.referenceImages.galleryAriaLabel', { name: scientificName })
      : t('pages.species.referenceImages.title'));

  return (
    <ImageList
      cols={cols}
      gap={8}
      sx={{ m: 0 }}
      aria-label={resolvedAriaLabel}
      data-testid="reference-image-grid"
    >
      {images.map((image, i) => (
        <GalleryTile key={`${image.source_url}-${i}`} image={image} scientificName={scientificName} />
      ))}
    </ImageList>
  );
}
