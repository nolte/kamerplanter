import { useMemo, useState } from 'react';
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

  const [search, setSearch] = useState('');

  const normalizedSearch = search.trim().toLowerCase();

  const persist = (next: Record<string, ModuleVisibilityState>) => {
    dispatch(saveModuleVisibility(next));
    enqueueSnackbar(t('common.saved'), { variant: 'success' });
  };

  const handleToggle = (key: ModuleKey, checked: boolean) => {
    persist({ ...overrides, [key]: checked ? 'enabled' : 'disabled' });
  };

  const handleReset = (key: ModuleKey) => {
    const next = { ...overrides };
    delete next[key];
    persist(next);
  };

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
        <AlertTitle sx={{ fontWeight: 600 }}>{t('modules.settings.introTitle')}</AlertTitle>
        <Typography variant="body2">{t('modules.settings.subtitle')}</Typography>
      </Alert>

      {/* Search field */}
      <TextField
        fullWidth
        size="small"
        value={search}
        onChange={(e) => setSearch(e.target.value)}
        placeholder={t('modules.settings.searchPlaceholder')}
        aria-label={t('modules.settings.searchAriaLabel')}
        slotProps={{
          input: {
            startAdornment: (
              <InputAdornment position="start">
                <SearchIcon fontSize="small" color="action" aria-hidden="true" />
              </InputAdornment>
            ),
          },
          htmlInput: { 'aria-controls': 'modules-list-region' },
        }}
        data-testid="modules-search-field"
      />

      {/* Live region for screen reader announcements on search result count */}
      <Box
        role="status"
        aria-live="polite"
        aria-atomic="true"
        sx={{ position: 'absolute', width: 1, height: 1, overflow: 'hidden', clip: 'rect(0,0,0,0)' }}
      >
        {isSearchActive &&
          t('modules.settings.searchResultsAria', { count: totalMatchCount, query: search })}
      </Box>

      {/* Module accordion list */}
      <Box id="modules-list-region">
        {groupedModules.map(({ category, modules }) => (
          <Accordion
            key={category}
            defaultExpanded
            disableGutters
            data-testid={`modules-category-${category}`}
            sx={{ mb: 1 }}
          >
            <AccordionSummary
              expandIcon={<ExpandMoreIcon />}
              aria-label={t(`modules.categories.${category}`)}
            >
              <Typography variant="subtitle1" sx={{ fontWeight: 600 }}>
                {t(`modules.categories.${category}`)}
              </Typography>
            </AccordionSummary>
            <AccordionDetails sx={{ display: 'flex', flexDirection: 'column', gap: 1.5, pt: 0 }}>
              {modules.map((def) => {
                const override = overrides[def.key] as ModuleVisibilityState | undefined;
                const visible = isModuleVisible(def.key);
                const hasOverride = override !== undefined;

                let stateLabel: string;
                if (override === 'enabled') stateLabel = t('modules.settings.manualOn');
                else if (override === 'disabled') stateLabel = t('modules.settings.manualOff');
                else if (visible) stateLabel = t('modules.settings.followsLevelVisible');
                else stateLabel = t('modules.settings.followsLevelHidden');

                // Accessible label that conveys both module name and current state.
                const switchAriaLabel = t('modules.settings.switchAriaLabel', {
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
                        <Typography variant="body2" color="text.secondary" sx={{ mb: hasOverride ? 0.75 : 0 }}>
                          {t(def.descriptionKey)}
                        </Typography>
                        {hasOverride && (
                          <Button
                            size="small"
                            variant="text"
                            onClick={() => handleReset(def.key)}
                            // Minimum 44px touch height via py padding
                            sx={{ mt: 0.25, py: 0.75, px: 1, minWidth: 'auto', fontSize: '0.75rem' }}
                            data-testid={`module-reset-${def.key}`}
                            aria-label={t('modules.settings.resetAriaLabel', {
                              module: t(def.labelKey),
                            })}
                          >
                            {t('modules.settings.reset')}
                          </Button>
                        )}
                      </Box>

                      {/* Switch — 48px touch target via wrapper */}
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
        ))}

        {/* Empty state when search yields no results */}
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
              {t('modules.settings.noResultsTitle')}
            </Typography>
            <Typography variant="body2">
              {t('modules.settings.noResultsHint', { query: search })}
            </Typography>
            <Button
              size="small"
              variant="outlined"
              onClick={() => setSearch('')}
              data-testid="modules-clear-search"
            >
              {t('modules.settings.clearSearch')}
            </Button>
          </Box>
        )}
      </Box>

      <Divider sx={{ mt: 0.5 }} />

      {/* Core modules — fixed, never hideable. */}
      <Box>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1.5 }}>
          <LockIcon fontSize="small" sx={{ color: 'text.secondary' }} aria-hidden="true" />
          <Typography variant="subtitle1" sx={{ fontWeight: 600 }}>
            {t('modules.settings.coreSectionTitle')}
          </Typography>
          <Tooltip
            title={t('modules.settings.coreSectionTooltip')}
            enterTouchDelay={0}
            leaveTouchDelay={3000}
          >
            <InfoIcon
              fontSize="small"
              sx={{ color: 'text.secondary', fontSize: 18, cursor: 'help' }}
              aria-label={t('modules.settings.coreSectionTooltip')}
              tabIndex={0}
            />
          </Tooltip>
        </Box>
        <Box
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
                  alignItems: 'center',
                  gap: 2,
                  py: 1.25,
                  '&:last-child': { pb: 1.25 },
                }}
              >
                <Box sx={{ flex: 1, minWidth: 0 }}>
                  <Typography variant="subtitle2" color="text.secondary">
                    {t(def.labelKey)}
                  </Typography>
                </Box>
                <Tooltip title={t('modules.settings.coreTooltip')} enterTouchDelay={0}>
                  <span>
                    <Switch
                      checked
                      disabled
                      size="small"
                      slotProps={{
                        input: {
                          'aria-label': t('modules.settings.coreAriaLabel', {
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
