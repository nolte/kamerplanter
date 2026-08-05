import { useCallback, useMemo, useState } from 'react';
import { useTranslation } from 'react-i18next';
import Badge from '@mui/material/Badge';
import Box from '@mui/material/Box';
import Button from '@mui/material/Button';
import Checkbox from '@mui/material/Checkbox';
import Chip from '@mui/material/Chip';
import Collapse from '@mui/material/Collapse';
import FormControl from '@mui/material/FormControl';
import InputAdornment from '@mui/material/InputAdornment';
import InputLabel from '@mui/material/InputLabel';
import ListItemText from '@mui/material/ListItemText';
import MenuItem from '@mui/material/MenuItem';
import OutlinedInput from '@mui/material/OutlinedInput';
import Select, { type SelectChangeEvent } from '@mui/material/Select';
import TextField from '@mui/material/TextField';
import Typography from '@mui/material/Typography';
import useMediaQuery from '@mui/material/useMediaQuery';
import { useTheme } from '@mui/material/styles';
import FilterListIcon from '@mui/icons-material/FilterList';
import FilterListOffIcon from '@mui/icons-material/FilterListOff';
import SearchIcon from '@mui/icons-material/Search';
import { DIARY_ANALYSIS_STATES, DIARY_ENTRY_TYPES } from '@/api/endpoints/diary';
import type { DiaryAnalysisState, DiaryEntryType } from '@/api/types';
import {
  activeDiaryFilterCount,
  activeQuickFilter,
  EMPTY_DIARY_FILTERS,
  type DiaryOverviewFilterState,
} from './diaryOverviewFilterState';

/** One option of the plant / species dropdowns. */
export interface DiaryFilterOption {
  value: string;
  label: string;
}

interface DiaryOverviewFiltersProps {
  value: DiaryOverviewFilterState;
  onChange: (next: DiaryOverviewFilterState) => void;
  plantOptions: DiaryFilterOption[];
  speciesOptions: DiaryFilterOption[];
}

const MENU_PROPS = { slotProps: { paper: { style: { maxHeight: 320 } } } };

/**
 * REQ-050 §2.5.2 — the filter row of the tenant-wide diary overview.
 *
 * **The analysis-state filter is never hidden.** "What is finished by now?" is
 * the most frequent access to this page, so "only with a result" and "only
 * waiting" sit as chips in the first row on every viewport — not inside a
 * collapsed panel a phone user has to discover first. The remaining filters
 * (plant, species, type, tag, period, sort order) are secondary and do collapse
 * below `md`, because six stacked full-width controls would otherwise push the
 * list itself off a 360 px screen.
 *
 * Every filter is a **server** parameter. Nothing here narrows the loaded page
 * locally, so the row count under a filter is the real number of matches across
 * all pages and not "whatever survived of the current 50".
 */
export default function DiaryOverviewFilters({
  value,
  onChange,
  plantOptions,
  speciesOptions,
}: DiaryOverviewFiltersProps) {
  const { t } = useTranslation();
  const theme = useTheme();
  const isCompact = useMediaQuery(theme.breakpoints.down('md'));
  const [panelOpen, setPanelOpen] = useState(false);

  const activeCount = activeDiaryFilterCount(value);
  const quick = activeQuickFilter(value.analysisStates);

  const patch = useCallback(
    (fields: Partial<DiaryOverviewFilterState>) => onChange({ ...value, ...fields }),
    [onChange, value],
  );

  const stateLabels = useMemo(
    () =>
      Object.fromEntries(
        DIARY_ANALYSIS_STATES.map((s) => [s, t(`enums.diaryAnalysisState.${s}`)]),
      ) as Record<DiaryAnalysisState, string>,
    [t],
  );

  const handleStatesChange = (event: SelectChangeEvent<DiaryAnalysisState[]>) => {
    const next = event.target.value;
    patch({
      analysisStates: (typeof next === 'string'
        ? (next.split(',') as DiaryAnalysisState[])
        : next) as DiaryAnalysisState[],
    });
  };

  /** The shorthand chips — one click, no detour (§2.5.2). */
  const quickChips: Array<{ id: 'all' | 'completed' | 'requested'; states: DiaryAnalysisState[] }> = [
    { id: 'all', states: [] },
    { id: 'completed', states: ['completed'] },
    { id: 'requested', states: ['requested'] },
  ];

  const secondaryFilters = (
    <Box
      sx={{
        display: 'flex',
        flexWrap: 'wrap',
        gap: 1,
        mt: 1,
      }}
    >
      <FormControl size="small" sx={{ minWidth: { xs: '100%', sm: 200 } }}>
        <InputLabel id="diary-filter-plant-label">
          {t('pages.diaryOverview.filters.plant')}
        </InputLabel>
        <Select
          labelId="diary-filter-plant-label"
          label={t('pages.diaryOverview.filters.plant')}
          value={value.plantKey}
          onChange={(e) => patch({ plantKey: e.target.value })}
          MenuProps={MENU_PROPS}
          data-testid="diary-filter-plant"
        >
          <MenuItem value="">{t('pages.diaryOverview.filters.anyPlant')}</MenuItem>
          {plantOptions.map((option) => (
            <MenuItem key={option.value} value={option.value}>
              {option.label}
            </MenuItem>
          ))}
        </Select>
      </FormControl>

      <FormControl size="small" sx={{ minWidth: { xs: '100%', sm: 200 } }}>
        <InputLabel id="diary-filter-species-label">
          {t('pages.diaryOverview.filters.species')}
        </InputLabel>
        <Select
          labelId="diary-filter-species-label"
          label={t('pages.diaryOverview.filters.species')}
          value={value.speciesKey}
          onChange={(e) => patch({ speciesKey: e.target.value })}
          MenuProps={MENU_PROPS}
          data-testid="diary-filter-species"
        >
          <MenuItem value="">{t('pages.diaryOverview.filters.anySpecies')}</MenuItem>
          {speciesOptions.map((option) => (
            <MenuItem key={option.value} value={option.value}>
              {option.label}
            </MenuItem>
          ))}
        </Select>
      </FormControl>

      <FormControl size="small" sx={{ minWidth: { xs: '100%', sm: 180 } }}>
        <InputLabel id="diary-filter-entry-type-label">
          {t('pages.diaryOverview.filters.entryType')}
        </InputLabel>
        <Select
          labelId="diary-filter-entry-type-label"
          label={t('pages.diaryOverview.filters.entryType')}
          value={value.entryType}
          onChange={(e) => patch({ entryType: e.target.value as DiaryEntryType | '' })}
          MenuProps={MENU_PROPS}
          data-testid="diary-filter-entry-type"
        >
          <MenuItem value="">{t('pages.diaryOverview.filters.anyEntryType')}</MenuItem>
          {DIARY_ENTRY_TYPES.map((type) => (
            <MenuItem
              key={type}
              value={type}
              data-testid={`diary-filter-entry-type-option-${type}`}
            >
              {t(`enums.diaryEntryType.${type}`)}
            </MenuItem>
          ))}
        </Select>
      </FormControl>

      <TextField
        size="small"
        label={t('pages.diaryOverview.filters.tag')}
        helperText={t('pages.diaryOverview.filters.tagHint')}
        value={value.tag}
        onChange={(e) => patch({ tag: e.target.value })}
        sx={{ minWidth: { xs: '100%', sm: 180 } }}
        data-testid="diary-filter-tag"
      />

      <TextField
        size="small"
        type="date"
        label={t('pages.diaryOverview.filters.from')}
        value={value.from}
        onChange={(e) => patch({ from: e.target.value })}
        slotProps={{ inputLabel: { shrink: true } }}
        sx={{ minWidth: { xs: '100%', sm: 170 } }}
        data-testid="diary-filter-from"
      />
      <TextField
        size="small"
        type="date"
        label={t('pages.diaryOverview.filters.to')}
        value={value.to}
        onChange={(e) => patch({ to: e.target.value })}
        slotProps={{ inputLabel: { shrink: true } }}
        sx={{ minWidth: { xs: '100%', sm: 170 } }}
        data-testid="diary-filter-to"
      />

      <FormControl size="small" sx={{ minWidth: { xs: '100%', sm: 200 } }}>
        <InputLabel id="diary-filter-sort-label">
          {t('pages.diaryOverview.filters.sort')}
        </InputLabel>
        <Select
          labelId="diary-filter-sort-label"
          label={t('pages.diaryOverview.filters.sort')}
          value={value.sort}
          onChange={(e) => patch({ sort: e.target.value as 'created_at' | 'analyzed_at' })}
          data-testid="diary-filter-sort"
        >
          <MenuItem value="created_at">{t('pages.diaryOverview.filters.sortCreatedAt')}</MenuItem>
          <MenuItem value="analyzed_at">{t('pages.diaryOverview.filters.sortAnalyzedAt')}</MenuItem>
        </Select>
      </FormControl>
    </Box>
  );

  return (
    <Box sx={{ mb: 2 }} data-testid="diary-overview-filters">
      {/* ── Row 1: the analysis state — the reason this page exists. ── */}
      <Box
        role="group"
        aria-label={t('pages.diaryOverview.filters.analysisStateGroup')}
        sx={{ display: 'flex', flexWrap: 'wrap', alignItems: 'center', gap: 1 }}
        data-testid="diary-state-quick-filters"
      >
        <Typography variant="body2" color="text.secondary" sx={{ mr: 0.5 }}>
          {t('pages.diaryOverview.filters.analysisState')}
        </Typography>

        {quickChips.map(({ id, states }) => {
          const selected = quick === id;
          return (
            <Chip
              key={id}
              label={t(`pages.diaryOverview.filters.quick.${id}`)}
              onClick={() => patch({ analysisStates: states })}
              color={selected ? 'primary' : 'default'}
              variant={selected ? 'filled' : 'outlined'}
              aria-pressed={selected}
              // 44 px minimum touch target — these chips are the primary control
              // of the page on a phone, not decoration.
              sx={{ minHeight: 36, px: 0.5 }}
              data-testid={`diary-quick-filter-${id}`}
            />
          );
        })}

        {/* Full control for every combination the two shorthands do not cover
            (e.g. "failed and in progress"). */}
        <FormControl size="small" sx={{ minWidth: { xs: '100%', sm: 240 } }}>
          <InputLabel id="diary-filter-analysis-state-label">
            {t('pages.diaryOverview.filters.analysisStateSelect')}
          </InputLabel>
          <Select
            labelId="diary-filter-analysis-state-label"
            multiple
            value={value.analysisStates}
            onChange={handleStatesChange}
            input={<OutlinedInput label={t('pages.diaryOverview.filters.analysisStateSelect')} />}
            renderValue={(picked) =>
              picked.length === 0
                ? t('pages.diaryOverview.filters.quick.all')
                : picked.map((s) => stateLabels[s]).join(', ')
            }
            MenuProps={MENU_PROPS}
            data-testid="diary-filter-analysis-state"
          >
            {DIARY_ANALYSIS_STATES.map((state) => (
              <MenuItem
                key={state}
                value={state}
                data-testid={`diary-filter-analysis-state-option-${state}`}
              >
                <Checkbox checked={value.analysisStates.includes(state)} size="small" />
                <ListItemText primary={stateLabels[state]} />
              </MenuItem>
            ))}
          </Select>
        </FormControl>
      </Box>

      {/* ── Row 2: free-text search + the collapse toggle on small screens. ── */}
      <Box sx={{ display: 'flex', flexWrap: 'wrap', alignItems: 'center', gap: 1, mt: 1.5 }}>
        <TextField
          size="small"
          label={t('pages.diaryOverview.filters.search')}
          placeholder={t('pages.diaryOverview.filters.searchPlaceholder')}
          helperText={t('pages.diaryOverview.filters.searchHint')}
          value={value.q}
          onChange={(e) => patch({ q: e.target.value })}
          slotProps={{
            input: {
              startAdornment: (
                <InputAdornment position="start">
                  <SearchIcon fontSize="small" />
                </InputAdornment>
              ),
            },
          }}
          sx={{ minWidth: { xs: '100%', sm: 260 }, flex: { sm: '1 1 260px' }, maxWidth: 420 }}
          data-testid="diary-search-input"
        />

        {isCompact && (
          <Button
            variant="outlined"
            startIcon={
              <Badge badgeContent={activeCount > 0 ? activeCount : undefined} color="primary">
                {panelOpen ? <FilterListOffIcon /> : <FilterListIcon />}
              </Badge>
            }
            onClick={() => setPanelOpen((open) => !open)}
            aria-expanded={panelOpen}
            aria-controls="diary-secondary-filters"
            sx={{ minHeight: 44 }}
            data-testid="diary-toggle-filter-panel"
          >
            {panelOpen
              ? t('pages.diaryOverview.filters.hideMore')
              : t('pages.diaryOverview.filters.showMore')}
          </Button>
        )}

        {activeCount > 0 && (
          <Button
            size="small"
            onClick={() => onChange({ ...EMPTY_DIARY_FILTERS, sort: value.sort })}
            sx={{ minHeight: 44 }}
            data-testid="diary-reset-filters"
          >
            {t('pages.diaryOverview.filters.reset')}
          </Button>
        )}
      </Box>

      {/* ── Row 3: the secondary filters. Always open from `md` up. ── */}
      {isCompact ? (
        <Collapse in={panelOpen} unmountOnExit id="diary-secondary-filters">
          {secondaryFilters}
        </Collapse>
      ) : (
        <Box id="diary-secondary-filters">{secondaryFilters}</Box>
      )}
    </Box>
  );
}
