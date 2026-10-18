/**
 * The head of the bed view (REQ-053 GP-FR-047, GP-FR-077): area, type, status, soil, sun, active
 * plants, open tasks, last care, next due date, assignment and the previous year. It reads the
 * summary only and owns no state.
 */
import { useMemo, type ReactNode } from 'react';
import { useTranslation } from 'react-i18next';
import Box from '@mui/material/Box';
import Button from '@mui/material/Button';
import Card from '@mui/material/Card';
import CardContent from '@mui/material/CardContent';
import Chip from '@mui/material/Chip';
import MenuItem from '@mui/material/MenuItem';
import TextField from '@mui/material/TextField';
import Typography from '@mui/material/Typography';
import SwapHorizIcon from '@mui/icons-material/SwapHoriz';
import type { BedAssignee, BedSummary } from './types';
import { BED_STATUS_COLOR, formatBedDate, isOverdue } from './bedFormat';

interface BedHeaderProps {
  summary: BedSummary;
  /** Display name of the location type; the raw key is shown while the types are loading. */
  typeName: string;
  assignees: readonly BedAssignee[];
  /** The season shown (`?year=`) and the years on offer. */
  year: number;
  years: readonly number[];
  onYearChange: (year: number) => void;
  /** `null` hides the control (a viewer cannot change the status). */
  onChangeStatus: (() => void) | null;
}

function Fact({ label, children, testId }: { label: string; children: ReactNode; testId: string }) {
  return (
    <Box sx={{ minWidth: 140 }} data-testid={testId}>
      <Typography variant="caption" color="text.secondary" component="div">
        {label}
      </Typography>
      <Typography variant="body1" component="div">
        {children}
      </Typography>
    </Box>
  );
}

export default function BedHeader({
  summary,
  typeName,
  assignees,
  year,
  years,
  onYearChange,
  onChangeStatus,
}: BedHeaderProps) {
  const { t, i18n } = useTranslation();
  const language = i18n.language;
  const area = useMemo(
    () => new Intl.NumberFormat(language, { maximumFractionDigits: 2 }).format(summary.area_m2),
    [language, summary.area_m2],
  );
  const soil = summary.soil_profile;
  const lastCare = formatBedDate(summary.last_care_at, language);
  const nextDue = formatBedDate(summary.next_due_at, language);
  const overdue = isOverdue(summary.next_due_at);
  const notSet = t('pages.bed.header.unknown');

  return (
    <Card variant="outlined" data-testid="bed-header" component="section" aria-label={t('pages.bed.header.title')}>
      <CardContent>
        <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 3, alignItems: 'flex-start' }}>
          <Fact label={t('pages.bed.header.area')} testId="bed-header-area">
            {area} m²
          </Fact>
          <Fact label={t('pages.bed.header.type')} testId="bed-header-type">
            {typeName || notSet}
          </Fact>
          <Fact label={t('pages.bed.header.status')} testId="bed-header-status">
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, flexWrap: 'wrap' }}>
              <Chip
                size="small"
                color={BED_STATUS_COLOR[summary.bed_status]}
                label={t(`enums.bedStatus.${summary.bed_status}`)}
              />
              {onChangeStatus && (
                <Button
                  size="small"
                  startIcon={<SwapHorizIcon />}
                  onClick={onChangeStatus}
                  data-testid="bed-status-change-button"
                  sx={{ minHeight: 44 }}
                >
                  {t('pages.bed.header.changeStatus')}
                </Button>
              )}
            </Box>
          </Fact>
          <Fact label={t('pages.bed.header.soil')} testId="bed-header-soil">
            {soil && soil.soil_texture !== 'unknown' ? t(`enums.soilTexture.${soil.soil_texture}`) : notSet}
          </Fact>
          <Fact label={t('pages.bed.header.sun')} testId="bed-header-sun">
            {summary.sun_exposure !== 'unknown' ? t(`enums.sunExposure.${summary.sun_exposure}`) : notSet}
          </Fact>
          <Fact label={t('pages.bed.header.plants')} testId="bed-header-plants">
            {t('pages.bed.header.plantCount', { count: summary.active_plant_count })}
            {summary.species_keys.length > 0 && (
              <Typography variant="caption" color="text.secondary" component="div">
                {t('pages.bed.header.speciesCount', { count: summary.species_keys.length })}
              </Typography>
            )}
          </Fact>
          <Fact label={t('pages.bed.header.openTasks')} testId="bed-header-tasks">
            {t('pages.bed.header.taskCount', { count: summary.open_task_count })}
            {summary.overdue_task_count > 0 && (
              <Typography variant="caption" color="error" component="div">
                {t('pages.bed.header.overdueCount', { count: summary.overdue_task_count })}
              </Typography>
            )}
          </Fact>
          <Fact label={t('pages.bed.header.lastCare')} testId="bed-header-last-care">
            {lastCare ?? t('pages.bed.header.never')}
          </Fact>
          <Fact label={t('pages.bed.header.nextDue')} testId="bed-header-next-due">
            {nextDue ? (
              <Typography component="span" color={overdue ? 'error' : 'inherit'}>
                {nextDue}
              </Typography>
            ) : (
              t('pages.bed.header.none')
            )}
          </Fact>
          <Fact label={t('pages.bed.header.assigned')} testId="bed-header-assigned">
            {assignees.length > 0 ? (
              <Box sx={{ display: 'flex', gap: 0.5, flexWrap: 'wrap' }}>
                {assignees.map((person) => (
                  <Chip key={person.membershipKey} size="small" variant="outlined" label={person.displayName} />
                ))}
              </Box>
            ) : (
              t('pages.bed.header.nobody')
            )}
          </Fact>
        </Box>

        <Box
          sx={{ mt: 2, display: 'flex', flexWrap: 'wrap', gap: 2, alignItems: 'center' }}
          data-testid="bed-header-season"
        >
          <TextField
            select
            size="small"
            label={t('pages.bed.header.year')}
            value={year}
            onChange={(event) => onYearChange(Number(event.target.value))}
            sx={{ minWidth: 120 }}
            slotProps={{ htmlInput: { 'data-testid': 'bed-year-select' } }}
          >
            {years.map((value) => (
              <MenuItem key={value} value={value}>
                {value}
              </MenuItem>
            ))}
          </TextField>
          <Typography variant="body2" color="text.secondary" data-testid="bed-header-previous-year">
            {t('pages.bed.header.previousYear', { year: year - 1 })}
          </Typography>
        </Box>
      </CardContent>
    </Card>
  );
}
