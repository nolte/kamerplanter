import { useState, useMemo, useCallback } from 'react';
import { useTranslation } from 'react-i18next';
import Box from '@mui/material/Box';
import Typography from '@mui/material/Typography';
import TextField from '@mui/material/TextField';
import Chip from '@mui/material/Chip';
import CircularProgress from '@mui/material/CircularProgress';
import SearchIcon from '@mui/icons-material/Search';
import StarIcon from '@mui/icons-material/Star';
import InputAdornment from '@mui/material/InputAdornment';
import ButtonBase from '@mui/material/ButtonBase';
import type { Species } from '@/api/types';

interface FavoriteSpeciesStepProps {
  allSpecies: Species[];
  allSpeciesLoading: boolean;
  favoriteSpeciesKeys: string[];
  onToggleFavoriteSpecies: (key: string) => void;
  kitSpeciesKeys: string[];
  existingFavoriteKeys: string[];
}

export default function FavoriteSpeciesStep({
  allSpecies,
  allSpeciesLoading,
  favoriteSpeciesKeys,
  onToggleFavoriteSpecies,
  kitSpeciesKeys,
  existingFavoriteKeys,
}: FavoriteSpeciesStepProps) {
  const { t } = useTranslation();
  const [search, setSearch] = useState('');

  const handleSearchChange = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    setSearch(e.target.value);
  }, []);

  const sortedAndFiltered = useMemo(() => {
    const lowerSearch = search.toLowerCase();
    const filtered = allSpecies.filter((sp) => {
      if (!lowerSearch) return true;
      const names = [sp.scientific_name, ...(sp.common_names ?? [])];
      return names.some((n) => n.toLowerCase().includes(lowerSearch));
    });

    const kitSet = new Set(kitSpeciesKeys);
    return filtered.sort((a, b) => {
      const aKit = kitSet.has(a.key) ? 0 : 1;
      const bKit = kitSet.has(b.key) ? 0 : 1;
      if (aKit !== bKit) return aKit - bKit;
      const aName = a.common_names?.[0] ?? a.scientific_name;
      const bName = b.common_names?.[0] ?? b.scientific_name;
      return aName.localeCompare(bName);
    });
  }, [allSpecies, search, kitSpeciesKeys]);

  const kitSet = useMemo(() => new Set(kitSpeciesKeys), [kitSpeciesKeys]);
  const existingSet = useMemo(() => new Set(existingFavoriteKeys), [existingFavoriteKeys]);

  return (
    <Box data-testid="onboarding-step-favorites">
      <Typography variant="h6" gutterBottom>
        {t('pages.onboarding.favorites.title')}
      </Typography>
      <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
        {t('pages.onboarding.favorites.subtitle')}
      </Typography>

      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
        <Typography variant="body2" sx={{ fontWeight: 600 }}>
          {t('pages.onboarding.favorites.selectedCount', { count: favoriteSpeciesKeys.length })}
        </Typography>
      </Box>

      <TextField
        fullWidth
        size="small"
        placeholder={t('pages.onboarding.favorites.searchPlaceholder')}
        value={search}
        onChange={handleSearchChange}
        slotProps={{
          input: {
            startAdornment: (
              <InputAdornment position="start">
                <SearchIcon fontSize="small" />
              </InputAdornment>
            ),
          },
        }}
        sx={{ mb: 2 }}
        data-testid="favorites-search"
      />

      {allSpeciesLoading ? (
        <Box sx={{ display: 'flex', justifyContent: 'center', py: 4 }}>
          <CircularProgress />
        </Box>
      ) : sortedAndFiltered.length === 0 ? (
        <Box
          sx={{
            p: 3,
            border: 1,
            borderColor: 'divider',
            borderRadius: 1,
            textAlign: 'center',
          }}
        >
          <Typography variant="body2" color="text.secondary">
            {t('pages.onboarding.favorites.noResults')}
          </Typography>
        </Box>
      ) : (
        <Box
          sx={{
            display: 'grid',
            gridTemplateColumns: {
              xs: 'repeat(2, 1fr)',
              sm: 'repeat(3, 1fr)',
              md: 'repeat(4, 1fr)',
            },
            gap: 1.5,
          }}
          role="group"
          aria-label={t('pages.onboarding.favorites.title')}
        >
          {sortedAndFiltered.map((sp) => {
            const isFavorited = favoriteSpeciesKeys.includes(sp.key);
            const isFromKit = kitSet.has(sp.key);
            const isExisting = existingSet.has(sp.key);
            const displayName = sp.common_names?.[0] ?? sp.scientific_name;

            return (
              <ButtonBase
                key={sp.key}
                onClick={() => onToggleFavoriteSpecies(sp.key)}
                aria-pressed={isFavorited}
                data-testid={`favorite-tile-${sp.key}`}
                sx={{
                  display: 'flex',
                  flexDirection: 'column',
                  alignItems: 'center',
                  justifyContent: 'center',
                  textAlign: 'center',
                  p: 1.5,
                  borderRadius: 2,
                  border: 2,
                  borderColor: isFavorited ? 'warning.main' : 'divider',
                  bgcolor: isFavorited ? 'warning.50' : 'background.paper',
                  transition: 'border-color 0.2s, background-color 0.2s, box-shadow 0.2s',
                  minHeight: 80,
                  position: 'relative',
                  '&:hover': {
                    borderColor: isFavorited ? 'warning.dark' : 'action.hover',
                    boxShadow: 1,
                  },
                  // Dark mode: use alpha-based highlight instead of warning.50
                  ...(isFavorited && {
                    bgcolor: (theme) =>
                      theme.palette.mode === 'dark'
                        ? 'rgba(255, 167, 38, 0.08)'
                        : undefined,
                  }),
                }}
              >
                {/* Favorite star indicator */}
                {isFavorited && (
                  <StarIcon
                    sx={{
                      position: 'absolute',
                      top: 6,
                      right: 6,
                      fontSize: 16,
                      color: 'warning.main',
                    }}
                    aria-hidden="true"
                  />
                )}

                {/* Badge chips */}
                {(isFromKit || (isExisting && !isFromKit)) && (
                  <Chip
                    label={
                      isFromKit
                        ? t('pages.onboarding.favorites.kitBadge')
                        : t('pages.onboarding.favorites.existingBadge')
                    }
                    color={isFromKit ? 'primary' : 'success'}
                    variant="outlined"
                    size="small"
                    sx={{ mb: 0.5, height: 20, fontSize: '0.675rem' }}
                  />
                )}

                <Typography
                  variant="body2"
                  noWrap
                  sx={{ fontWeight: isFavorited ? 600 : 400, maxWidth: '100%', px: 0.5 }}
                >
                  {displayName}
                </Typography>

                {sp.scientific_name !== displayName && (
                  <Typography
                    variant="caption"
                    color="text.secondary"
                    noWrap
                    sx={{ maxWidth: '100%', px: 0.5, fontStyle: 'italic' }}
                  >
                    {sp.scientific_name}
                  </Typography>
                )}
              </ButtonBase>
            );
          })}
        </Box>
      )}
    </Box>
  );
}
