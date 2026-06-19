import { useCallback, useEffect, useMemo, useState } from 'react';
import { useTranslation } from 'react-i18next';
import Box from '@mui/material/Box';
import ImageList from '@mui/material/ImageList';
import ImageListItem from '@mui/material/ImageListItem';
import ImageListItemBar from '@mui/material/ImageListItemBar';
import Skeleton from '@mui/material/Skeleton';
import Tooltip from '@mui/material/Tooltip';
import Typography from '@mui/material/Typography';
import useMediaQuery from '@mui/material/useMediaQuery';
import { useTheme } from '@mui/material/styles';
import CollectionsIcon from '@mui/icons-material/Collections';
import InfoOutlinedIcon from '@mui/icons-material/InfoOutlined';
import { getSpeciesReferenceImages } from '@/api/endpoints/species';
import { stripHtml } from '@/utils/formatting';
import { usePlatformAdmin } from '@/hooks/usePlatformAdmin';
import { ReferenceImageCuration } from './ReferenceImageCuration';
import type { ReferenceImage } from '@/api/types';

interface ReferenceImageGalleryProps {
  speciesKey: string;
  /** Scientific name used for aria-label and image alt fallback. */
  scientificName?: string;
}

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
  const altText = [organLabel, scientificName].filter(Boolean).join(' – ') || t('pages.species.referenceImages.imageAlt');

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
              <Tooltip
                title={caption}
                enterTouchDelay={0}
                leaveTouchDelay={4000}
              >
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
            background: 'linear-gradient(to top, rgba(0,0,0,0.72) 0%, rgba(0,0,0,0.36) 60%, transparent 100%)',
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

/**
 * Reference-image gallery for the species detail page (REQ-029-A).
 *
 * Lazily fetches `GET /species/{key}/reference-images` on mount. An empty
 * response is a normal state (no acquisition run yet) and renders a discreet
 * hint — never an error. Per-image attribution + license captions satisfy the
 * legal CC-BY requirement; broken external images remove themselves silently.
 *
 * Responsive column count: 2 (xs), 3 (sm), 4 (md+) — fills available width.
 * Skeleton count mirrors the real column count to avoid layout shift.
 */
export function ReferenceImageGallery({ speciesKey, scientificName }: ReferenceImageGalleryProps) {
  const { t } = useTranslation();
  const theme = useTheme();
  const isPlatformAdmin = usePlatformAdmin();
  const isMobile = useMediaQuery(theme.breakpoints.down('sm'));
  const isTablet = useMediaQuery(theme.breakpoints.between('sm', 'md'));
  const [images, setImages] = useState<ReferenceImage[]>([]);
  const [loading, setLoading] = useState(true);

  const cols = useMemo(() => {
    if (isMobile) return 2;
    if (isTablet) return 3;
    return 4;
  }, [isMobile, isTablet]);

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const data = await getSpeciesReferenceImages(speciesKey);
      setImages(data.images ?? []);
    } catch {
      // A missing index / failed lookup is treated as "no images", not an error.
      setImages([]);
    } finally {
      setLoading(false);
    }
  }, [speciesKey]);

  useEffect(() => {
    // Admins get the curation view (below), which fetches all images itself.
    if (!isPlatformAdmin) void load();
  }, [load, isPlatformAdmin]);

  // Platform admins curate (deselect/re-include); everyone else sees the
  // read-only public gallery of active images only.
  if (isPlatformAdmin) {
    return <ReferenceImageCuration speciesKey={speciesKey} scientificName={scientificName} />;
  }

  return (
    <Box data-testid="reference-image-gallery">
      <Typography component="h2" variant="h6" sx={{ mb: 0.5 }}>
        {t('pages.species.referenceImages.title')}
      </Typography>
      <Typography variant="body2" color="text.secondary" sx={{ mb: 1.5 }}>
        {t('pages.species.referenceImages.galleryIntro')}
      </Typography>

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
              <Skeleton
                variant="rectangular"
                sx={{ width: '100%', aspectRatio: '1 / 1' }}
              />
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
            <Typography variant="body2">
              {t('pages.species.referenceImages.empty')}
            </Typography>
            <Typography variant="caption" color="text.disabled" sx={{ display: 'block', mt: 0.25 }}>
              {t('pages.species.referenceImages.emptyHint')}
            </Typography>
          </Box>
        </Box>
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
          {images.map((image, i) => (
            <GalleryTile
              key={`${image.source_url}-${i}`}
              image={image}
              scientificName={scientificName}
            />
          ))}
        </ImageList>
      )}
    </Box>
  );
}

export default ReferenceImageGallery;
