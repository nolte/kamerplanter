/**
 * The filters of the bed history and of the tenant-wide history (REQ-053 GP-FR-102, GP-FR-107):
 * category, period, plant, person and bed, plus the "Show corrections" switch. The same bar serves
 * both lists; the tenant-wide page adds the bed filter, the bed tab the plant filter.
 */
import { useId, useState } from 'react';
import { useTranslation } from 'react-i18next';
import Button from '@mui/material/Button';
import Collapse from '@mui/material/Collapse';
import FormControlLabel from '@mui/material/FormControlLabel';
import MenuItem from '@mui/material/MenuItem';
import Switch from '@mui/material/Switch';
import TextField from '@mui/material/TextField';
import useMediaQuery from '@mui/material/useMediaQuery';
import { useTheme } from '@mui/material/styles';
import ExpandLessIcon from '@mui/icons-material/ExpandLess';
import ExpandMoreIcon from '@mui/icons-material/ExpandMore';
import Box from '@mui/material/Box';
import Form from '@/components/form/Form';
import { categoryLabel } from './historyFormat';
import {
  activeFilterCount,
  HISTORY_CATEGORIES,
  isRangeInverted,
  type HistoryFilters,
  type Period,
} from './historyFilters';
import type { FilterOption } from './historyTypes';

const PERIODS: readonly Period[] = ['30d', '90d', '365d', 'all', 'custom'];
const CONTROL_SX = { minWidth: { sm: 180 }, flex: { xs: '1 1 100%', sm: '0 1 200px' } };

interface HistoryFilterBarProps {
  filters: HistoryFilters;
  defaults: HistoryFilters;
  onChange: (patch: Partial<HistoryFilters>) => void;
  onReset: () => void;
  /** Plants the bed has had; the filter is hidden when the list is empty. */
  plants?: readonly FilterOption[];
  /** Beds to filter by (tenant-wide page). */
  beds?: readonly FilterOption[];
  /** Members the person filter names; the first entry is the caller (`Me`). */
  people: readonly FilterOption[];
  testIdPrefix: string;
}

export default function HistoryFilterBar({
  filters,
  defaults,
  onChange,
  onReset,
  plants = [],
  beds = [],
  people,
  testIdPrefix,
}: HistoryFilterBarProps) {
  const { t } = useTranslation();
  const active = activeFilterCount(filters, defaults);
  const inverted = isRangeInverted(filters);
  const id = (name: string) => `${testIdPrefix}-${name}`;
  const theme = useTheme();
  // On a phone six controls would push the list off the screen: they fold away behind one button.
  const compact = useMediaQuery(theme.breakpoints.down('sm'));
  const [open, setOpen] = useState(false);
  const regionId = useId();
  const expanded = !compact || open;

  return (
    <Form
      role="search"
      aria-label={t('pages.bed.history.filters.label')}
      onSubmit={(event) => event.preventDefault()}
      data-testid={id('filters')}
      sx={{ display: 'flex', flexDirection: 'column', gap: 1 }}
    >
      {compact && (
        <Button
          variant="outlined"
          onClick={() => setOpen((value) => !value)}
          aria-expanded={open}
          aria-controls={regionId}
          endIcon={open ? <ExpandLessIcon /> : <ExpandMoreIcon />}
          sx={{ minHeight: 48, justifyContent: 'space-between' }}
          data-testid={id('filters-toggle')}
        >
          {active > 0
            ? t('pages.bed.history.filters.toggleActive', { count: active })
            : t('pages.bed.history.filters.toggle')}
        </Button>
      )}
      <Collapse in={expanded} unmountOnExit={false} id={regionId}>
        <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 2, alignItems: 'center', pt: compact ? 1 : 0 }}>
      <TextField
        select
        size="small"
        label={t('pages.bed.history.filters.category')}
        value={filters.category}
        onChange={(event) => onChange({ category: event.target.value })}
        sx={CONTROL_SX}
        slotProps={{ htmlInput: { 'data-testid': id('category') } }}
      >
        <MenuItem value="">{t('pages.bed.history.filters.allCategories')}</MenuItem>
        {HISTORY_CATEGORIES.map((category) => (
          <MenuItem key={category} value={category}>
            {categoryLabel(t, category)}
          </MenuItem>
        ))}
      </TextField>

      <TextField
        select
        size="small"
        label={t('pages.bed.history.filters.period')}
        value={filters.period}
        onChange={(event) => onChange({ period: event.target.value as Period })}
        sx={CONTROL_SX}
        slotProps={{ htmlInput: { 'data-testid': id('period') } }}
      >
        {PERIODS.map((period) => (
          <MenuItem key={period} value={period}>
            {t(`pages.bed.history.filters.periods.${period}`)}
          </MenuItem>
        ))}
      </TextField>

      {filters.period === 'custom' && (
        <>
          <TextField
            size="small"
            type="date"
            label={t('pages.bed.history.filters.from')}
            value={filters.from}
            onChange={(event) => onChange({ from: event.target.value })}
            error={inverted}
            sx={CONTROL_SX}
            slotProps={{ inputLabel: { shrink: true }, htmlInput: { 'data-testid': id('from') } }}
          />
          <TextField
            size="small"
            type="date"
            label={t('pages.bed.history.filters.to')}
            value={filters.to}
            onChange={(event) => onChange({ to: event.target.value })}
            error={inverted}
            helperText={inverted ? t('pages.bed.history.filters.rangeInverted') : undefined}
            sx={CONTROL_SX}
            slotProps={{ inputLabel: { shrink: true }, htmlInput: { 'data-testid': id('to') } }}
          />
        </>
      )}

      {beds.length > 0 && (
        <TextField
          select
          size="small"
          label={t('pages.bed.history.filters.bed')}
          value={filters.locationKey}
          onChange={(event) => onChange({ locationKey: event.target.value, plantKey: '' })}
          sx={CONTROL_SX}
          slotProps={{ htmlInput: { 'data-testid': id('bed') } }}
        >
          <MenuItem value="">{t('pages.bed.history.filters.allBeds')}</MenuItem>
          {beds.map((bed) => (
            <MenuItem key={bed.key} value={bed.key}>
              {bed.label}
            </MenuItem>
          ))}
        </TextField>
      )}

      {plants.length > 0 && (
        <TextField
          select
          size="small"
          label={t('pages.bed.history.filters.plant')}
          value={filters.plantKey}
          onChange={(event) => onChange({ plantKey: event.target.value })}
          sx={CONTROL_SX}
          slotProps={{ htmlInput: { 'data-testid': id('plant') } }}
        >
          <MenuItem value="">{t('pages.bed.history.filters.allPlants')}</MenuItem>
          {plants.map((plant) => (
            <MenuItem key={plant.key} value={plant.key}>
              {plant.label}
            </MenuItem>
          ))}
        </TextField>
      )}

      <TextField
        select
        size="small"
        label={t('pages.bed.history.filters.person')}
        value={filters.performedBy}
        onChange={(event) => onChange({ performedBy: event.target.value })}
        helperText={people.length <= 1 ? t('pages.bed.history.filters.personOwnOnly') : undefined}
        sx={CONTROL_SX}
        slotProps={{ htmlInput: { 'data-testid': id('person') } }}
      >
        <MenuItem value="">{t('pages.bed.history.filters.everyone')}</MenuItem>
        {people.map((person, index) => (
          <MenuItem key={person.key} value={person.key}>
            {index === 0 ? t('pages.bed.history.filters.me') : person.label}
          </MenuItem>
        ))}
      </TextField>

      <FormControlLabel
        control={
          <Switch
            checked={filters.includeCorrections}
            onChange={(event) => onChange({ includeCorrections: event.target.checked })}
            slotProps={{ input: { 'data-testid': id('corrections') } as React.InputHTMLAttributes<HTMLInputElement> }}
          />
        }
        label={t('pages.bed.history.filters.corrections')}
        sx={{ minHeight: 48, mr: 0 }}
      />

      {active > 0 && (
        <Button onClick={onReset} sx={{ minHeight: 44 }} data-testid={id('reset')}>
          {t('pages.bed.history.filters.reset')}
        </Button>
      )}
        </Box>
      </Collapse>
    </Form>
  );
}
