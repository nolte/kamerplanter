import { useCallback, useMemo, useId, useState } from 'react';
import { useTranslation } from 'react-i18next';
import Box from '@mui/material/Box';
import Typography from '@mui/material/Typography';
import TextField from '@mui/material/TextField';
import InputAdornment from '@mui/material/InputAdornment';
import Accordion from '@mui/material/Accordion';
import AccordionSummary from '@mui/material/AccordionSummary';
import AccordionDetails from '@mui/material/AccordionDetails';
import Card from '@mui/material/Card';
import CardContent from '@mui/material/CardContent';
import Switch from '@mui/material/Switch';
import Chip from '@mui/material/Chip';
import Button from '@mui/material/Button';
import Tooltip from '@mui/material/Tooltip';
import Alert from '@mui/material/Alert';
import AlertTitle from '@mui/material/AlertTitle';
import Divider from '@mui/material/Divider';
import InfoIcon from '@mui/icons-material/Info';
import ExpandMoreIcon from '@mui/icons-material/ExpandMore';
import SearchIcon from '@mui/icons-material/Search';
import LockIcon from '@mui/icons-material/Lock';
import SearchOffIcon from '@mui/icons-material/SearchOff';
import { useSnackbar } from 'notistack';

import { useAppDispatch } from '@/store/hooks';
import { saveModuleVisibility } from '@/store/slices/userPreferencesSlice';
import { useModuleVisibility } from '@/hooks/useModuleVisibility';
import {
  moduleCatalog,
  MODULE_CATEGORIES,
  type ModuleDefinition,
  type ModuleKey,
} from '@/config/moduleCatalog';
import type { ModuleVisibilityState } from '@/api/types';

const CORE_MODULES: ModuleDefinition[] = Object.values(moduleCatalog).filter(
  (m) => m.core,
);

/** Maps tri-state override to a chip colour so the status is visually distinct. */
function resolveChipColor(
  override: ModuleVisibilityState | undefined,
  visible: boolean,
): 'success' | 'warning' | 'default' {
  if (override === 'enabled') return 'success';
  if (override === 'disabled') return 'warning';
  return visible ? 'default' : 'default';
}

export default function ModulesSettingsTab() {
  const { t } = useTranslation();
  const dispatch = useAppDispatch();
  const { enqueueSnackbar } = useSnackbar();
  const { isModuleVisible, overrides } = useModuleVisibility();
  const coreSectionId = useId();

  const [search, setSearch] = useState('');

  const normalizedSearch = search.trim().toLowerCase();

  // Stable callback reference — avoids recreating the function on every render.
  const persist = useCallback(
    (next: Record<string, ModuleVisibilityState>) => {
      dispatch(saveModuleVisibility(next));
      enqueueSnackbar(t('common.saved'), { variant: 'success' });
    },
    [dispatch, enqueueSnackbar, t],
  );

  const handleToggle = useCallback(
    (key: ModuleKey, checked: boolean) => {
      persist({ ...overrides, [key]: checked ? 'enabled' : 'disabled' });
    },
    [persist, overrides],
  );

  const handleReset = useCallback(
    (key: ModuleKey) => {
      const next = { ...overrides };
      delete next[key];
      persist(next);
    },
    [persist, overrides],
  );

  // Modules grouped by category, filtered by the search term.
  const groupedModules = useMemo(() => {
    const matches = (def: ModuleDefinition) => {
      if (!normalizedSearch) return true;
      const label = t(def.labelKey).toLowerCase();
      const description = t(def.descriptionKey).toLowerCase();
      return label.includes(normalizedSearch) || description.includes(normalizedSearch);
    };

    return MODULE_CATEGORIES.map((category) => ({
      category,
      modules: Object.values(moduleCatalog).filter(
        (m) => !m.core && m.category === category && matches(m),
      ),
    })).filter((group) => group.modules.length > 0);
  }, [normalizedSearch, t]);

  const totalMatchCount = useMemo(
    () => groupedModules.reduce((sum, g) => sum + g.modules.length, 0),
    [groupedModules],
  );

  const isSearchActive = normalizedSearch.length > 0;
  const hasNoResults = isSearchActive && totalMatchCount === 0;

  return (
    <Box data-testid="modules-settings-tab" sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
      {/* Introductory explanation — prominent, before any controls */}
      <Alert
        severity="info"
        icon={<InfoIcon fontSize="small" />}
        data-testid="modules-intro-alert"
      >
        <AlertTitle sx={{ fontWeight: 600 }}>{t('modules.manage.introTitle')}</AlertTitle>
        <Typography variant="body2">{t('modules.manage.subtitle')}</Typography>
      </Alert>

      {/* Search field — min-height 44px for touch-target compliance (UI-NFR-001 R-011) */}
      <TextField
        fullWidth
        value={search}
        onChange={(e) => setSearch(e.target.value)}
        placeholder={t('modules.manage.searchPlaceholder')}
        aria-label={t('modules.manage.searchAriaLabel')}
        slotProps={{
          input: {
            startAdornment: (
              <InputAdornment position="start">
                <SearchIcon fontSize="small" color="action" aria-hidden="true" />
              </InputAdornment>
            ),
            // Enforce 44px min-height for touch targets on mobile
            sx: { minHeight: 44 },
          },
          htmlInput: { 'aria-controls': 'modules-list-region' },
        }}
        data-testid="modules-search-field"
      />

      {/* Live region for screen-reader announcements on search result count (UI-NFR-002 R-011) */}
      <Box
        role="status"
        aria-live="polite"
        aria-atomic="true"
        sx={{ position: 'absolute', width: 1, height: 1, overflow: 'hidden', clip: 'rect(0,0,0,0)' }}
      >
        {isSearchActive &&
          t('modules.manage.searchResultsAria', { count: totalMatchCount, query: search })}
      </Box>

      {/* Module accordion list */}
      <Box id="modules-list-region">
        {groupedModules.map(({ category, modules }) => {
          const categoryHeadingId = `category-heading-${category}`;
          return (
            <Accordion
              key={category}
              defaultExpanded
              disableGutters
              data-testid={`modules-category-${category}`}
              sx={{ mb: 1 }}
            >
              {/*
               * AccordionSummary renders a <button>. Do NOT set aria-label here —
               * MUI already computes the button's accessible name from its children
               * and appends the aria-expanded state. Overriding aria-label would
               * replace the child text entirely (WCAG 4.1.2).
               */}
              <AccordionSummary expandIcon={<ExpandMoreIcon />} id={categoryHeadingId}>
                <Box
                  sx={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: 1,
                    flexWrap: 'wrap',
                    width: '100%',
                  }}
                >
                  <Typography variant="subtitle1" sx={{ fontWeight: 600 }}>
                    {t(`modules.categories.${category}`)}
                  </Typography>
                  {/* Module count badge — helps orientate users without opening accordion */}
                  <Chip
                    label={t('modules.manage.categoryCount', { count: modules.length })}
                    size="small"
                    variant="outlined"
                    sx={{ fontSize: '0.7rem', height: 20, pointerEvents: 'none' }}
                    aria-hidden="true"
                  />
                </Box>
              </AccordionSummary>
              {/*
               * role="group" + aria-labelledby links each module list to its
               * category heading so screen-readers announce the context
               * when navigating the list (UI-NFR-002 R-010).
               */}
              <AccordionDetails
                role="group"
                aria-labelledby={categoryHeadingId}
                sx={{ display: 'flex', flexDirection: 'column', gap: 1.5, pt: 0 }}
              >
                {modules.map((def) => {
                  const override = overrides[def.key] as ModuleVisibilityState | undefined;
                  const visible = isModuleVisible(def.key);
                  const hasOverride = override !== undefined;

                  let stateLabel: string;
                  if (override === 'enabled') stateLabel = t('modules.manage.manualOn');
                  else if (override === 'disabled') stateLabel = t('modules.manage.manualOff');
                  else if (visible) stateLabel = t('modules.manage.followsLevelVisible');
                  else stateLabel = t('modules.manage.followsLevelHidden');

                  // Accessible label that conveys both module name and current state.
                  const switchAriaLabel = t('modules.manage.switchAriaLabel', {
                    module: t(def.labelKey),
                    state: stateLabel,
                  });

                  return (
                    <Card
                      key={def.key}
                      variant="outlined"
                      data-testid={`module-row-${def.key}`}
                      sx={{
                        borderColor: hasOverride ? 'primary.light' : 'divider',
                        transition: 'border-color 0.2s',
                      }}
                    >
                      <CardContent
                        sx={{
                          display: 'flex',
                          alignItems: 'flex-start',
                          gap: 2,
                          py: { xs: 1.5, sm: 2 },
                          '&:last-child': { pb: { xs: 1.5, sm: 2 } },
                        }}
                      >
                        {/* Text block */}
                        <Box sx={{ flex: 1, minWidth: 0 }}>
                          <Box
                            sx={{
                              display: 'flex',
                              alignItems: 'center',
                              gap: 1,
                              flexWrap: 'wrap',
                              mb: 0.5,
                            }}
                          >
                            <Typography variant="subtitle2" component="span">
                              {t(def.labelKey)}
                            </Typography>
                            <Chip
                              size="small"
                              variant={hasOverride ? 'filled' : 'outlined'}
                              color={resolveChipColor(override, visible)}
                              label={stateLabel}
                              sx={{ fontSize: '0.7rem', height: 20 }}
                            />
                          </Box>
                          <Typography
                            variant="body2"
                            color="text.secondary"
                            sx={{ mb: hasOverride ? 0.75 : 0 }}
                          >
                            {t(def.descriptionKey)}
                          </Typography>
                          {hasOverride && (
                            <Button
                              size="small"
                              variant="text"
                              onClick={() => handleReset(def.key)}
                              /*
                               * Minimum 44px touch target: py 1.25 = 10px top+bottom
                               * padding + ~20px text ≈ 40px + border → meets 44px
                               * via the surrounding flex container's minHeight.
                               */
                              sx={{ mt: 0.25, py: 1.25, px: 1, minWidth: 'auto', fontSize: '0.75rem' }}
                              data-testid={`module-reset-${def.key}`}
                              aria-label={t('modules.manage.resetAriaLabel', {
                                module: t(def.labelKey),
                              })}
                            >
                              {t('modules.manage.reset')}
                            </Button>
                          )}
                        </Box>

                        {/* Switch — 48px touch target via wrapper (UI-NFR-001 R-011) */}
                        <Box
                          sx={{
                            display: 'flex',
                            alignItems: 'center',
                            minHeight: 48,
                            flexShrink: 0,
                          }}
                        >
                          <Switch
                            checked={visible}
                            onChange={(e) => handleToggle(def.key, e.target.checked)}
                            slotProps={{ input: { 'aria-label': switchAriaLabel } }}
                            data-testid={`module-switch-${def.key}`}
                          />
                        </Box>
                      </CardContent>
                    </Card>
                  );
                })}
              </AccordionDetails>
            </Accordion>
          );
        })}

        {/* Empty state when search yields no results (UI-NFR-004 R-012/R-013/R-014) */}
        {hasNoResults && (
          <Box
            data-testid="modules-no-results"
            sx={{
              display: 'flex',
              flexDirection: 'column',
              alignItems: 'center',
              gap: 1.5,
              py: 6,
              px: 2,
              textAlign: 'center',
              color: 'text.secondary',
            }}
          >
            <SearchOffIcon sx={{ fontSize: 48, opacity: 0.4 }} aria-hidden="true" />
            <Typography variant="body1" sx={{ fontWeight: 500 }}>
              {t('modules.manage.noResultsTitle')}
            </Typography>
            <Typography variant="body2">
              {t('modules.manage.noResultsHint', { query: search })}
            </Typography>
            <Button
              size="small"
              variant="outlined"
              onClick={() => setSearch('')}
              data-testid="modules-clear-search"
              // Minimum 44px touch target: MUI outlined Button default is ~36px;
              // explicit sy ensures mobile compliance (UI-NFR-001 R-011).
              sx={{ minHeight: 44, px: 3 }}
            >
              {t('modules.manage.clearSearch')}
            </Button>
          </Box>
        )}
      </Box>

      <Divider sx={{ mt: 0.5 }} />

      {/* Core modules — fixed, never hideable. */}
      <Box>
        <Box
          sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1.5 }}
          id={coreSectionId}
        >
          <LockIcon fontSize="small" sx={{ color: 'text.secondary' }} aria-hidden="true" />
          <Typography variant="subtitle1" sx={{ fontWeight: 600 }}>
            {t('modules.manage.coreSectionTitle')}
          </Typography>
          {/*
           * Tooltip trigger is a focusable span so keyboard users can
           * access the explanation (WCAG 2.1 SC 1.4.13 / UI-NFR-002 R-003).
           * enterTouchDelay=0 ensures immediate activation on touch.
           */}
          <Tooltip
            title={t('modules.manage.coreSectionTooltip')}
            enterTouchDelay={0}
            leaveTouchDelay={3000}
          >
            <Box
              component="span"
              role="button"
              tabIndex={0}
              aria-label={t('modules.manage.coreSectionTooltipAriaLabel')}
              sx={{
                display: 'inline-flex',
                alignItems: 'center',
                cursor: 'help',
                borderRadius: '50%',
                '&:focus-visible': {
                  outline: '2px solid',
                  outlineColor: 'primary.main',
                  outlineOffset: 2,
                },
              }}
            >
              <InfoIcon
                fontSize="small"
                sx={{ color: 'text.secondary', fontSize: 18 }}
                aria-hidden="true"
              />
            </Box>
          </Tooltip>
        </Box>
        <Box
          role="group"
          aria-labelledby={coreSectionId}
          sx={{ display: 'flex', flexDirection: 'column', gap: 1 }}
          data-testid="modules-core-section"
        >
          {CORE_MODULES.map((def) => (
            <Card
              key={def.key}
              variant="outlined"
              sx={{ opacity: 0.65, bgcolor: 'action.hover' }}
              data-testid={`module-core-${def.key}`}
            >
              <CardContent
                sx={{
                  display: 'flex',
                  alignItems: 'flex-start',
                  gap: 2,
                  py: { xs: 1.25, sm: 1.5 },
                  '&:last-child': { pb: { xs: 1.25, sm: 1.5 } },
                }}
              >
                <Box sx={{ flex: 1, minWidth: 0 }}>
                  <Typography variant="subtitle2" color="text.secondary">
                    {t(def.labelKey)}
                  </Typography>
                  {/* Description keeps information density consistent with non-core modules */}
                  <Typography variant="body2" color="text.secondary" sx={{ mt: 0.25 }}>
                    {t(def.descriptionKey)}
                  </Typography>
                </Box>
                <Tooltip
                  title={t('modules.manage.coreTooltip')}
                  enterTouchDelay={0}
                  leaveTouchDelay={3000}
                >
                  <span>
                    <Switch
                      checked
                      disabled
                      size="small"
                      slotProps={{
                        input: {
                          'aria-label': t('modules.manage.coreAriaLabel', {
                            module: t(def.labelKey),
                          }),
                        },
                      }}
                    />
                  </span>
                </Tooltip>
              </CardContent>
            </Card>
          ))}
        </Box>
      </Box>
    </Box>
  );
}
