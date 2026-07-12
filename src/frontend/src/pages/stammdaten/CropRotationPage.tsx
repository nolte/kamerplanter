import { useCallback, useEffect, useMemo, useState } from 'react';
import { useTranslation } from 'react-i18next';
import Box from '@mui/material/Box';
import TextField from '@mui/material/TextField';
import MenuItem from '@mui/material/MenuItem';
import Autocomplete from '@mui/material/Autocomplete';
import Button from '@mui/material/Button';
import IconButton from '@mui/material/IconButton';
import List from '@mui/material/List';
import ListItem from '@mui/material/ListItem';
import ListItemText from '@mui/material/ListItemText';
import Chip from '@mui/material/Chip';
import Dialog from '@mui/material/Dialog';
import useMediaQuery from '@mui/material/useMediaQuery';
import { useTheme } from '@mui/material/styles';
import { visuallyHidden } from '@mui/utils';
import DialogTitle from '@mui/material/DialogTitle';
import DialogContent from '@mui/material/DialogContent';
import DialogContentText from '@mui/material/DialogContentText';
import DialogActions from '@mui/material/DialogActions';
import Typography from '@mui/material/Typography';
import AddIcon from '@mui/icons-material/Add';
import AutorenewIcon from '@mui/icons-material/Autorenew';
import StarIcon from '@mui/icons-material/Star';
import StarBorderIcon from '@mui/icons-material/StarBorder';
import PageTitle from '@/components/layout/PageTitle';
import LoadingSkeleton from '@/components/common/LoadingSkeleton';
import EmptyState from '@/components/common/EmptyState';
import { useNotification } from '@/hooks/useNotification';
import { useApiError } from '@/hooks/useApiError';
import { useFamilyFavorites } from '@/hooks/useFamilyFavorites';
import * as rotationApi from '@/api/endpoints/cropRotation';
import * as familiesApi from '@/api/endpoints/botanicalFamilies';
import type { BotanicalFamily, RotationCountsMap, RotationSuccessor } from '@/api/types';
import { kamiMasterdata } from '@/assets/brand/illustrations';

type NutrientDemandFilter = '' | 'heavy' | 'medium' | 'light';

const HARDY_FROST_TOLERANCES = new Set(['hardy', 'very_hardy']);

export default function CropRotationPage() {
  const theme = useTheme();
  const fullScreen = useMediaQuery(theme.breakpoints.down('sm'));
  const { t } = useTranslation();
  const notification = useNotification();
  const { handleError } = useApiError();
  const { toggleFavorite, isFavorite } = useFamilyFavorites();
  const [families, setFamilies] = useState<BotanicalFamily[]>([]);
  const [rotationCounts, setRotationCounts] = useState<RotationCountsMap>({});
  const [selectedKey, setSelectedKey] = useState('');
  // Tracks the option the user is currently browsing with the arrow keys (or
  // hovering with the mouse) so the Shift+F keyboard shortcut below knows which
  // family to favorite. MUI's combobox popup keeps real DOM focus on the input
  // the whole time (aria-activedescendant model) — the nested per-option star
  // button is therefore never reachable via Tab, so favoriting needs its own
  // keyboard path independent of focus (UI-NFR-002 keyboard-operability).
  const [highlightedFamilyKey, setHighlightedFamilyKey] = useState<string | null>(null);
  const [successors, setSuccessors] = useState<RotationSuccessor[]>([]);
  const [loading, setLoading] = useState(false);
  const [dialogOpen, setDialogOpen] = useState(false);
  const [targetKey, setTargetKey] = useState('');
  const [waitYears, setWaitYears] = useState(3);

  // Filter state — favorites / has-rotation / nitrogen-fixing / frost-hardy are
  // ANDed toggles; nutrient demand ("Zehrer" — the 4-year rotation model) is a
  // single-select because its values are mutually exclusive.
  const [favoritesOnly, setFavoritesOnly] = useState(false);
  const [hasRotationOnly, setHasRotationOnly] = useState(false);
  const [nitrogenFixingOnly, setNitrogenFixingOnly] = useState(false);
  const [frostHardyOnly, setFrostHardyOnly] = useState(false);
  const [nutrientDemand, setNutrientDemand] = useState<NutrientDemandFilter>('');

  useEffect(() => {
    // Load ALL families (paginated, not the default limit=50 cap) so the dropdown
    // is never truncated, plus the whole-catalogue successor counts in a single
    // aggregate request (no N+1) to badge every option before selection.
    familiesApi.listAllBotanicalFamilies().then(setFamilies).catch(() => {});
    rotationApi.getRotationCounts().then(setRotationCounts).catch(() => {});
  }, []);

  useEffect(() => {
    if (!selectedKey) return;
    // eslint-disable-next-line react-hooks/set-state-in-effect -- set loading before async fetch
    setLoading(true);
    rotationApi
      .getSuccessors(selectedKey)
      .then(setSuccessors)
      .catch((err) => handleError(err))
      .finally(() => setLoading(false));
  }, [selectedKey]); // eslint-disable-line react-hooks/exhaustive-deps

  const successorCountOf = useCallback(
    (familyKey: string): number => rotationCounts[familyKey] ?? 0,
    [rotationCounts],
  );

  // Shift+F toggles the favorite of the currently highlighted option — the
  // keyboard-accessible counterpart to the mouse/touch-only star button inside
  // each option (see highlightedFamilyKey above). A modifier combo is required
  // so normal search typing (e.g. "Fabaceae") is never intercepted; captured in
  // the capture phase on the wrapping Box so it never competes with MUI's own
  // Enter/Arrow handling on the input.
  const handleFavoriteShortcut = useCallback(
    (e: React.KeyboardEvent) => {
      if (!e.shiftKey || e.key.toLowerCase() !== 'f' || !highlightedFamilyKey) return;
      e.preventDefault();
      e.stopPropagation();
      toggleFavorite(highlightedFamilyKey);
    },
    [highlightedFamilyKey, toggleFavorite],
  );

  // Filtered + sorted options — memoised so the Autocomplete keeps a stable
  // option reference (custom-object convention, FRONTEND.md). Favorites bubble
  // up, then families that actually have rotation data, then alphabetical.
  const filteredFamilies = useMemo(() => {
    const filtered = families.filter((f) => {
      if (favoritesOnly && !isFavorite(f.key)) return false;
      if (hasRotationOnly && successorCountOf(f.key) === 0) return false;
      if (nitrogenFixingOnly && !f.nitrogen_fixing) return false;
      if (frostHardyOnly && !HARDY_FROST_TOLERANCES.has(f.frost_tolerance)) return false;
      if (nutrientDemand && f.typical_nutrient_demand !== nutrientDemand) return false;
      return true;
    });
    return [...filtered].sort((a, b) => {
      const favDiff = Number(isFavorite(b.key)) - Number(isFavorite(a.key));
      if (favDiff !== 0) return favDiff;
      const rotDiff = Number(successorCountOf(b.key) > 0) - Number(successorCountOf(a.key) > 0);
      if (rotDiff !== 0) return rotDiff;
      return a.name.localeCompare(b.name);
    });
  }, [
    families,
    favoritesOnly,
    hasRotationOnly,
    nitrogenFixingOnly,
    frostHardyOnly,
    nutrientDemand,
    isFavorite,
    successorCountOf,
  ]);

  const selectedFamily = useMemo(
    () => families.find((f) => f.key === selectedKey) ?? null,
    [families, selectedKey],
  );

  const activeFilterCount =
    Number(favoritesOnly) +
    Number(hasRotationOnly) +
    Number(nitrogenFixingOnly) +
    Number(frostHardyOnly) +
    Number(nutrientDemand !== '');

  const clearAllFilters = () => {
    setFavoritesOnly(false);
    setHasRotationOnly(false);
    setNitrogenFixingOnly(false);
    setFrostHardyOnly(false);
    setNutrientDemand('');
  };

  const handleAdd = async () => {
    if (!selectedKey || !targetKey) return;
    try {
      await rotationApi.setSuccessor({
        from_family_key: selectedKey,
        to_family_key: targetKey,
        wait_years: waitYears,
      });
      notification.success(t('common.create'));
      const [updated, counts] = await Promise.all([
        rotationApi.getSuccessors(selectedKey),
        rotationApi.getRotationCounts(),
      ]);
      setSuccessors(updated);
      setRotationCounts(counts);
    } catch (err) {
      handleError(err);
    }
    setDialogOpen(false);
    setTargetKey('');
  };

  return (
    <>
      <PageTitle title={t('pages.cropRotation.title')} />

      <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
        {t('pages.cropRotation.intro')}
      </Typography>

      {/* Filter bar — mobile-first: chips wrap on narrow viewports, every control
          is >=48px tall for touch. */}
      <Box
        sx={{ display: 'flex', flexWrap: 'wrap', gap: 1, alignItems: 'center', mb: 2 }}
        role="group"
        aria-label={t('pages.cropRotation.filtersLabel')}
      >
        <Chip
          icon={favoritesOnly ? <StarIcon /> : <StarBorderIcon />}
          label={t('pages.cropRotation.filterFavorites')}
          onClick={() => setFavoritesOnly((v) => !v)}
          color={favoritesOnly ? 'warning' : 'default'}
          variant={favoritesOnly ? 'filled' : 'outlined'}
          aria-pressed={favoritesOnly}
          sx={{ minHeight: 48 }}
          data-testid="filter-favorites"
        />
        <Chip
          icon={<AutorenewIcon />}
          label={t('pages.cropRotation.filterHasRotation')}
          onClick={() => setHasRotationOnly((v) => !v)}
          color={hasRotationOnly ? 'primary' : 'default'}
          variant={hasRotationOnly ? 'filled' : 'outlined'}
          aria-pressed={hasRotationOnly}
          sx={{ minHeight: 48 }}
          data-testid="filter-has-rotation"
        />
        <Chip
          label={t('pages.cropRotation.filterNitrogenFixing')}
          onClick={() => setNitrogenFixingOnly((v) => !v)}
          color={nitrogenFixingOnly ? 'success' : 'default'}
          variant={nitrogenFixingOnly ? 'filled' : 'outlined'}
          aria-pressed={nitrogenFixingOnly}
          sx={{ minHeight: 48 }}
          data-testid="filter-nitrogen-fixing"
        />
        <Chip
          label={t('pages.cropRotation.filterFrostHardy')}
          onClick={() => setFrostHardyOnly((v) => !v)}
          color={frostHardyOnly ? 'info' : 'default'}
          variant={frostHardyOnly ? 'filled' : 'outlined'}
          aria-pressed={frostHardyOnly}
          sx={{ minHeight: 48 }}
          data-testid="filter-frost-hardy"
        />
        <TextField
          select
          size="small"
          label={t('pages.cropRotation.filterNutrientDemand')}
          value={nutrientDemand}
          onChange={(e) => setNutrientDemand(e.target.value as NutrientDemandFilter)}
          sx={{ minWidth: 180, '& .MuiInputBase-root': { minHeight: 48 } }}
          data-testid="filter-nutrient-demand"
        >
          <MenuItem value="">{t('pages.cropRotation.filterAll')}</MenuItem>
          <MenuItem value="heavy">{t('enums.nutrientDemand.heavy')}</MenuItem>
          <MenuItem value="medium">{t('enums.nutrientDemand.medium')}</MenuItem>
          <MenuItem value="light">{t('enums.nutrientDemand.light')}</MenuItem>
        </TextField>
        {activeFilterCount > 0 && (
          <Button size="small" onClick={clearAllFilters} data-testid="clear-filters">
            {t('pages.cropRotation.resetFilters')}
          </Button>
        )}
      </Box>

      {/* onKeyDownCapture runs before MUI's own Enter/Arrow handling on the input
          (capture phase, so it can never be shadowed by an internal stopPropagation),
          giving the Shift+F favorite shortcut a safe, non-interfering hook. */}
      <Box onKeyDownCapture={handleFavoriteShortcut}>
        <Autocomplete
          fullWidth
          options={filteredFamilies}
          value={selectedFamily}
          onChange={(_e, option) => setSelectedKey(option?.key ?? '')}
          onHighlightChange={(_e, option) => setHighlightedFamilyKey(option?.key ?? null)}
          getOptionLabel={(option) => option.name}
          isOptionEqualToValue={(option, value) => option.key === value.key}
          noOptionsText={t('pages.cropRotation.noFamiliesFound')}
          sx={{ maxWidth: 480, mb: 1 }}
          renderOption={({ key: optionKey, ...optionProps }, option) => {
            const count = successorCountOf(option.key);
            const hasRotation = count > 0;
            const favorited = isFavorite(option.key);
            return (
              <Box
                component="li"
                key={optionKey}
                {...optionProps}
                sx={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: 1,
                  justifyContent: 'space-between',
                  minHeight: 48,
                }}
                data-testid={`family-option-${option.key}`}
                data-has-rotation={hasRotation}
              >
                {/* De-emphasis uses a plain secondary text colour, never
                    `text.disabled` — the 0-successor families stay fully selectable
                    and keyboard-reachable, so they must not read as disabled
                    (UI-NFR-002). The count chip stays at full opacity: an explicit
                    "0" is useful information and must stay legible. */}
                <Typography
                  variant="body2"
                  noWrap
                  color={hasRotation ? 'text.primary' : 'text.secondary'}
                  sx={{ flex: 1, minWidth: 0 }}
                >
                  {option.name}
                </Typography>
                {/* Star toggles the family favorite without selecting the option
                    (stopPropagation) so the dropdown doubles as a favoriting
                    surface for the favorites filter. Sized to the 48x48px touch
                    target minimum (UI-NFR-001 R-011) even though the icon itself
                    stays small/dense; keyboard users reach the same toggle via the
                    Shift+F shortcut since MUI's combobox never moves real DOM
                    focus into the popup (see handleFavoriteShortcut above). */}
                <IconButton
                  size="small"
                  aria-label={t(
                    favorited ? 'pages.cropRotation.removeFavorite' : 'pages.cropRotation.addFavorite',
                    { name: option.name },
                  )}
                  aria-pressed={favorited}
                  onClick={(e) => {
                    e.stopPropagation();
                    toggleFavorite(option.key);
                  }}
                  sx={{ minWidth: 48, minHeight: 48 }}
                  data-testid={`family-favorite-${option.key}`}
                >
                  {favorited ? (
                    <StarIcon fontSize="small" color="warning" />
                  ) : (
                    <StarBorderIcon fontSize="small" />
                  )}
                </IconButton>
                {/* Visual badge: icon + number (not colour alone). Hidden from the
                    a11y tree — the readable summary below carries the same info as
                    text for screen readers. */}
                <Chip
                  icon={<AutorenewIcon />}
                  label={count}
                  size="small"
                  color={hasRotation ? 'primary' : 'default'}
                  variant="outlined"
                  aria-hidden
                  data-testid={`family-option-count-${option.key}`}
                />
                <Box component="span" sx={visuallyHidden}>
                  {t('pages.cropRotation.successorCount', { count })}
                </Box>
              </Box>
            );
          }}
          renderInput={(params) => (
            <TextField
              {...params}
              label={t('pages.cropRotation.fromFamily')}
              helperText={t('pages.cropRotation.fromFamilyHelper')}
              slotProps={{
                ...params.slotProps,
                htmlInput: {
                  ...params.slotProps.htmlInput,
                  'aria-keyshortcuts': 'Shift+F',
                },
              }}
              data-testid="from-family-select"
            />
          )}
        />
      </Box>

      {/* Persistent legend (touch-friendly, not hover-dependent) explaining the
          count badge and the Shift+F favorite shortcut for non-expert users
          (UI-NFR-011 descriptive-text). */}
      <Box sx={{ display: 'flex', flexDirection: 'column', gap: 0.5, mb: 3 }}>
        <Box sx={{ display: 'flex', flexWrap: 'wrap', alignItems: 'center', gap: 0.5 }}>
          <AutorenewIcon fontSize="small" color="primary" />
          <Typography variant="caption" color="text.secondary">
            {t('pages.cropRotation.countLegend')}
          </Typography>
        </Box>
        <Typography variant="caption" color="text.secondary">
          {t('pages.cropRotation.favoriteShortcutHint')}
        </Typography>
      </Box>

      {loading && <LoadingSkeleton variant="card" />}

      {selectedKey && !loading && (
        <Box>
          <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
            <Typography variant="subtitle2" color="text.secondary">
              {t('pages.cropRotation.successorsTitle')}
            </Typography>
            <Button
              variant="outlined"
              size="small"
              startIcon={<AddIcon />}
              onClick={() => setDialogOpen(true)}
              data-testid="add-successor-button"
            >
              {t('pages.cropRotation.addSuccessor')}
            </Button>
          </Box>
          {successors.length === 0 ? (
            <EmptyState
              illustration={kamiMasterdata}
              message={t('pages.cropRotation.noSuccessors')}
              actionLabel={t('pages.cropRotation.addSuccessor')}
              onAction={() => setDialogOpen(true)}
            />
          ) : (
            <List>
              {successors.map((s) => (
                <ListItem key={s.family_key} divider>
                  <ListItemText
                    primary={s.name ?? s.family_key} slotProps={{ primary: { variant: 'body2' } }} />
                  <Chip
                    label={`${s.wait_years} ${t('pages.cropRotation.waitYears')}`}
                    size="small"
                    color="default"
                    variant="outlined"
                  />
                </ListItem>
              ))}
            </List>
          )}
        </Box>
      )}

      {!selectedKey && !loading && (
        <EmptyState
          illustration={kamiMasterdata}
          message={t('pages.cropRotation.selectFamilyHint')}
        />
      )}

      <Dialog fullScreen={fullScreen} open={dialogOpen} onClose={() => setDialogOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>{t('pages.cropRotation.addSuccessor')}</DialogTitle>
        <DialogContent>
          <DialogContentText sx={{ mb: 2 }}>
            {t('pages.cropRotation.addSuccessorHint')}
          </DialogContentText>
          <TextField
            select
            fullWidth
            label={t('pages.cropRotation.toFamily')}
            value={targetKey}
            onChange={(e) => setTargetKey(e.target.value)}
            helperText={t('pages.cropRotation.toFamilyHelper')}
            sx={{ mt: 1, mb: 2 }}
            data-testid="to-family-select"
          >
            {families.filter((f) => f.key !== selectedKey).map((f) => (
              <MenuItem key={f.key} value={f.key}>{f.name}</MenuItem>
            ))}
          </TextField>
          <TextField
            type="number"
            label={t('pages.cropRotation.waitYears')}
            value={waitYears}
            onChange={(e) => setWaitYears(Number(e.target.value))}
            fullWidth
            helperText={t('pages.cropRotation.waitYearsHelper')}
            slotProps={{ htmlInput: { min: 1, max: 10 } }}
            data-testid="wait-years-input"
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setDialogOpen(false)}>{t('common.cancel')}</Button>
          <Button variant="contained" onClick={handleAdd} disabled={!targetKey}>
            {t('common.create')}
          </Button>
        </DialogActions>
      </Dialog>
    </>
  );
}
