import { useMemo, useState } from 'react';
import { useTranslation } from 'react-i18next';
import Box from '@mui/material/Box';
import Badge from '@mui/material/Badge';
import Button from '@mui/material/Button';
import Checkbox from '@mui/material/Checkbox';
import Chip from '@mui/material/Chip';
import Collapse from '@mui/material/Collapse';
import FormControl from '@mui/material/FormControl';
import IconButton from '@mui/material/IconButton';
import InputLabel from '@mui/material/InputLabel';
import ListItemText from '@mui/material/ListItemText';
import MenuItem from '@mui/material/MenuItem';
import OutlinedInput from '@mui/material/OutlinedInput';
import Select, { type SelectChangeEvent } from '@mui/material/Select';
import Tooltip from '@mui/material/Tooltip';
import FilterListIcon from '@mui/icons-material/FilterList';
import FilterListOffIcon from '@mui/icons-material/FilterListOff';
import useMediaQuery from '@mui/material/useMediaQuery';
import { useTheme } from '@mui/material/styles';
import type { ColumnFiltersResult } from '@/hooks/useColumnFilters';

export interface ColumnFilterOption {
  /** Stored value (matches the row field / URL param value). */
  value: string;
  /** Human-readable, localized option label. */
  label: string;
}

export interface ColumnFilterDef {
  /** Filter id == query-param name (must be one of the ids passed to useColumnFilters). */
  id: string;
  /** Localized control label shown inside the Select. */
  label: string;
  options: ColumnFilterOption[];
}

interface ColumnFilterBarProps {
  filters: ColumnFilterDef[];
  state: ColumnFiltersResult;
}

const MENU_PROPS = {
  slotProps: { paper: { style: { maxHeight: 320 } } },
};

/**
 * Toolbar row of multi-select column filters with checkbox menus.
 *
 * **Desktop (md+):** filters are shown inline next to each other.
 * **Mobile/tablet (< md):** filters are hidden behind a toggle button with an
 * active-count badge and collapse open on demand — avoids three cramped
 * dropdowns squeezing a 360 px viewport.
 *
 * Each control is fully keyboard-operable (MUI `Select`) and labelled for
 * screen readers. A "clear all" button appears only when at least one value
 * is selected (UI-NFR-010 R-010).
 */
export function ColumnFilterBar({ filters, state }: ColumnFilterBarProps) {
  const { t } = useTranslation();
  const theme = useTheme();
  const isCompact = useMediaQuery(theme.breakpoints.down('md'));

  const { values, setFilter, clearAll, activeCount } = state;

  // On compact viewports the filter panel is collapsed by default and the
  // user toggles it via an icon button.  On desktop it is always open.
  const [panelOpen, setPanelOpen] = useState(false);

  const labelById = useMemo(() => {
    const map: Record<string, Record<string, string>> = {};
    for (const f of filters) {
      map[f.id] = Object.fromEntries(f.options.map((o) => [o.value, o.label]));
    }
    return map;
  }, [filters]);

  const handleChange = (id: string) => (event: SelectChangeEvent<string[]>) => {
    const value = event.target.value;
    setFilter(id, typeof value === 'string' ? value.split(',') : value);
  };

  const filterControls = (
    <Box
      sx={{
        display: 'flex',
        alignItems: 'center',
        flexWrap: 'wrap',
        gap: 1,
        // On mobile the panel sits below the toggle row; give it some breathing room.
        mt: isCompact ? 1 : 0,
      }}
    >
      {filters.map((filter) => {
        const selected = values[filter.id] ?? [];
        const labelId = `column-filter-label-${filter.id}`;
        return (
          <FormControl
            key={filter.id}
            size="small"
            sx={{
              // On mobile: fill available width (up to 100%) so labels are never
              // cut off. On desktop keep a sensible min/max to prevent very wide
              // controls with few options.
              minWidth: { xs: '100%', sm: 200, md: 180 },
              maxWidth: { xs: '100%', sm: 320, md: 280 },
            }}
          >
            <InputLabel id={labelId}>{filter.label}</InputLabel>
            <Select
              labelId={labelId}
              multiple
              value={selected}
              onChange={handleChange(filter.id)}
              input={<OutlinedInput label={filter.label} />}
              renderValue={(picked) =>
                picked.length === 0
                  ? ''
                  : picked.map((v) => labelById[filter.id]?.[v] ?? v).join(', ')
              }
              MenuProps={MENU_PROPS}
              data-testid={`column-filter-${filter.id}`}
              inputProps={{ 'aria-label': filter.label }}
            >
              {filter.options.map((option) => (
                <MenuItem
                  key={option.value}
                  value={option.value}
                  data-testid={`column-filter-${filter.id}-option-${option.value}`}
                >
                  <Checkbox checked={selected.includes(option.value)} size="small" />
                  <ListItemText primary={option.label} />
                </MenuItem>
              ))}
            </Select>
          </FormControl>
        );
      })}

      {activeCount > 0 && (
        // `role="status"` + `aria-live="polite"` so screen-reader users hear the
        // updated active-filter count after toggling an option inside the Select
        // menu, without requiring them to close the menu and re-discover the chip.
        <Box
          role="status"
          aria-live="polite"
          sx={{ display: 'flex', alignItems: 'center', gap: 1 }}
        >
          <Chip
            label={t('table.activeFilters', { count: activeCount })}
            size="small"
            color="primary"
            variant="outlined"
            data-testid="active-filters-chip"
          />
          <Button
            size="small"
            onClick={clearAll}
            data-testid="clear-column-filters-button"
          >
            {t('table.clearFilters')}
          </Button>
        </Box>
      )}
    </Box>
  );

  // --- Desktop layout: icon + filter controls in one row ---
  if (!isCompact) {
    return (
      <Box
        sx={{ display: 'flex', alignItems: 'center', flexWrap: 'wrap', gap: 1, mb: 2 }}
        role="group"
        aria-label={t('table.filterGroupLabel')}
        data-testid="column-filter-bar"
      >
        <FilterListIcon fontSize="small" color="action" aria-hidden="true" />
        {filterControls}
      </Box>
    );
  }

  // --- Mobile/tablet layout: toggle button + collapsible panel ---
  return (
    <Box sx={{ mb: 2 }} data-testid="column-filter-bar">
      {/* Toggle row */}
      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
        <Tooltip
          title={panelOpen ? t('table.hideFilters') : t('table.showFilters')}
          arrow
        >
          <IconButton
            size="small"
            onClick={() => setPanelOpen((prev) => !prev)}
            aria-expanded={panelOpen}
            aria-controls="column-filter-panel"
            aria-label={
              panelOpen ? t('table.hideFilters') : t('table.showFilters')
            }
            data-testid="toggle-filter-panel-button"
            color={activeCount > 0 ? 'primary' : 'default'}
            // UI-NFR-001 R-011: 48x48 minimum touch target on the mobile/tablet
            // toggle — the default `size="small"` hit area (~34px) is below the
            // mandatory minimum on this touch-primary breakpoint.
            sx={{ minWidth: 48, minHeight: 48 }}
          >
            <Badge badgeContent={activeCount > 0 ? activeCount : undefined} color="primary">
              {panelOpen ? (
                <FilterListOffIcon fontSize="small" />
              ) : (
                <FilterListIcon fontSize="small" />
              )}
            </Badge>
          </IconButton>
        </Tooltip>

        {/* Summary chips when panel is closed */}
        {!panelOpen && activeCount > 0 && (
          <Box role="status" aria-live="polite" sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <Chip
              label={t('table.activeFilters', { count: activeCount })}
              size="small"
              color="primary"
              variant="outlined"
              data-testid="active-filters-chip"
            />
            <Button
              size="small"
              onClick={clearAll}
              data-testid="clear-column-filters-button"
            >
              {t('table.clearFilters')}
            </Button>
          </Box>
        )}
      </Box>

      {/* Collapsible filter panel */}
      <Collapse in={panelOpen} id="column-filter-panel">
        {filterControls}
      </Collapse>
    </Box>
  );
}
