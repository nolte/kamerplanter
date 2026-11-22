/**
 * The planting timeline of a bed (REQ-053 GP-FR-103): per year the families that stood in the bed,
 * colour-coded and always named, for at least five years (the server picks `max(pause, 5)`). It is
 * the basis of the crop-rotation view. A year nobody recorded offers "What stood here?" (GP-API-042);
 * a year a grower filled in afterwards can be taken back.
 */
import { useTranslation } from 'react-i18next';
import Alert from '@mui/material/Alert';
import Box from '@mui/material/Box';
import Button from '@mui/material/Button';
import Chip from '@mui/material/Chip';
import IconButton from '@mui/material/IconButton';
import Paper from '@mui/material/Paper';
import Typography from '@mui/material/Typography';
import CloseIcon from '@mui/icons-material/Close';
import ErrorDisplay from '@/components/common/ErrorDisplay';
import LoadingSkeleton from '@/components/common/LoadingSkeleton';
import { useEffect, useMemo, useRef } from 'react';
import PlannerGlossary, { type PlannerGlossaryTerm } from '../glossary/PlannerGlossary';
import { familyColors } from './familyColor';
import type { RotationPlanting, RotationYear } from './historyTypes';
import type { TimelineState } from './useRotationTimeline';

/** The terms the timeline shows (GP-UX-011): rotation, the feeder classes on the chips and green manure. */
const TIMELINE_TERMS: readonly PlannerGlossaryTerm[] = ['fruchtfolge', 'zehrerklassen', 'gruenduengung'];

interface PlantingTimelineProps {
  state: TimelineState;
  canEdit: boolean;
  /** Open the backfill dialog, optionally for a year. */
  onBackfill: (year?: number) => void;
  /** Take a backfilled year back. */
  onCancel: (careEventKey: string, year: number) => void;
  onRetry: () => void;
  /** A year to move the keyboard focus to once its row has been refreshed (after a dialog closed). */
  focusYear?: number | null;
  onFocusHandled?: () => void;
}

function PlantingChip({
  planting,
  year,
  color,
  canEdit,
  onCancel,
}: {
  planting: RotationPlanting;
  year: number;
  color: string | undefined;
  canEdit: boolean;
  onCancel: (careEventKey: string, year: number) => void;
}) {
  const { t } = useTranslation();
  const fallow = planting.plan_role === 'fallow';
  const family = planting.family_name ?? planting.family_key;
  const label = fallow
    ? t('pages.bed.history.timeline.fallow')
    : [family, planting.plan_role === 'green_manure' ? t('pages.bed.history.timeline.greenManure') : null]
        .filter(Boolean)
        .join(' · ');
  const season = planting.season ? t(`pages.bed.history.timeline.seasons.${planting.season}`) : null;
  const demand = planting.nutrient_demand
    ? t(`enums.nutrientDemandLevel.${planting.nutrient_demand}`, { defaultValue: planting.nutrient_demand })
    : null;
  const canCancel = canEdit && planting.source === 'backfill' && planting.care_event_key !== null;
  const cancelKey = planting.care_event_key;

  return (
    <Box sx={{ display: 'inline-flex', alignItems: 'center', flexWrap: 'wrap', maxWidth: '100%' }}>
      <Chip
        variant={fallow ? 'outlined' : 'filled'}
        label={
          <>
            {label}
            {(season || demand) && (
              <Typography component="span" variant="caption" sx={{ ml: 0.75, opacity: 0.8 }}>
                {[season, demand].filter(Boolean).join(' · ')}
              </Typography>
            )}
          </>
        }
        icon={
          color ? (
            <Box
              component="span"
              aria-hidden="true"
              sx={{ width: 12, height: 12, borderRadius: '50%', bgcolor: color, flex: 'none', ml: '8px !important' }}
            />
          ) : undefined
        }
        sx={{
          height: 'auto',
          minHeight: 32,
          '& .MuiChip-label': { whiteSpace: 'normal', py: 0.5 },
          borderStyle: fallow ? 'dashed' : undefined,
          borderColor: color,
          borderWidth: color ? 2 : undefined,
        }}
        data-testid={`timeline-planting-${year}-${planting.family_key ?? 'fallow'}`}
      />
      {planting.source === 'backfill' && (
        <Typography variant="caption" color="text.secondary" sx={{ ml: 0.5 }}>
          {t('pages.bed.history.timeline.recordedLater')}
        </Typography>
      )}
      {canCancel && cancelKey && (
        <IconButton
          size="small"
          onClick={() => onCancel(cancelKey, year)}
          aria-label={t('pages.bed.history.timeline.cancelYear', { year })}
          sx={{ minWidth: 48, minHeight: 48 }}
          data-testid={`timeline-cancel-${cancelKey}`}
        >
          <CloseIcon fontSize="small" aria-hidden="true" />
        </IconButton>
      )}
    </Box>
  );
}

function YearRow({
  entry,
  colors,
  canEdit,
  onBackfill,
  onCancel,
  focusYear,
  onFocusHandled,
}: {
  focusYear?: number | null;
  onFocusHandled?: () => void;
  entry: RotationYear;
  colors: ReadonlyMap<string, string>;
  canEdit: boolean;
  onBackfill: (year?: number) => void;
  onCancel: (careEventKey: string, year: number) => void;
}) {
  const { t } = useTranslation();
  const empty = entry.plantings.length === 0;
  const current = entry.year === new Date().getFullYear();
  const rowRef = useRef<HTMLLIElement>(null);
  const seen = useRef(entry);
  useEffect(() => {
    // The trigger of the dialog may be gone (a taken-back chip): focus lands on the refreshed row,
    // not on the page top.
    if (focusYear === entry.year && seen.current !== entry) {
      rowRef.current?.focus();
      onFocusHandled?.();
    }
    seen.current = entry;
  }, [entry, focusYear, onFocusHandled]);
  return (
    <Box
      component="li"
      ref={rowRef}
      tabIndex={-1}
      data-testid={`timeline-year-${entry.year}`}
      sx={{
        display: 'flex',
        flexWrap: 'wrap',
        gap: 1,
        alignItems: 'center',
        py: 1,
        borderBottom: 1,
        borderColor: 'divider',
        listStyle: 'none',
        '&:focus-visible': { outline: 2, outlineStyle: 'solid', outlineColor: 'primary.main' },
      }}
    >
      <Typography component="span" variant="subtitle2" sx={{ width: 56, flex: 'none' }}>
        {entry.year}
      </Typography>
      {empty ? (
        <>
          <Typography variant="body2" color="text.secondary">
            {t('pages.bed.history.timeline.nothingRecorded')}
          </Typography>
          {canEdit && !current && (
            <Button
              size="small"
              onClick={() => onBackfill(entry.year)}
              sx={{ minHeight: 44 }}
              data-testid={`timeline-add-${entry.year}`}
            >
              {t('pages.bed.history.timeline.addYear', { year: entry.year })}
            </Button>
          )}
        </>
      ) : (
        <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1 }}>
          {entry.plantings.map((planting, index) => (
            <PlantingChip
              key={`${planting.source}-${planting.care_event_key ?? planting.species_key ?? planting.family_key ?? index}-${index}`}
              planting={planting}
              year={entry.year}
              color={planting.family_key ? colors.get(planting.family_key) : undefined}
              canEdit={canEdit}
              onCancel={onCancel}
            />
          ))}
        </Box>
      )}
    </Box>
  );
}

export default function PlantingTimeline({ state, canEdit, onBackfill, onCancel, onRetry, focusYear, onFocusHandled }: PlantingTimelineProps) {
  const { t } = useTranslation();
  const colors = useMemo(
    () =>
      familyColors(
        state.status === 'ready'
          ? state.timeline.timeline.flatMap((entry) => entry.plantings.flatMap((p) => (p.family_key ? [p.family_key] : [])))
          : [],
      ),
    [state],
  );
  return (
    <Paper variant="outlined" sx={{ p: 2 }} component="section" aria-labelledby="bed-timeline-title" data-testid="bed-timeline">
      <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1, alignItems: 'center', justifyContent: 'space-between' }}>
        <Typography id="bed-timeline-title" variant="h6" component="h2">
          {t('pages.bed.history.timeline.title')}
        </Typography>
        {canEdit && (
          <Button
            variant="outlined"
            onClick={() => onBackfill()}
            sx={{ minHeight: 48 }}
            data-testid="timeline-backfill"
          >
            {t('pages.bed.history.timeline.whatStood')}
          </Button>
        )}
      </Box>
      <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
        {t('pages.bed.history.timeline.hint')}
      </Typography>
      <Box sx={{ mb: 1 }}>
        <PlannerGlossary id="timeline" terms={TIMELINE_TERMS} />
      </Box>
      {state.status === 'loading' && (
        <Box role="status" aria-busy="true" aria-label={t('pages.bed.history.timeline.loading')}>
          <LoadingSkeleton variant="card" />
        </Box>
      )}
      {state.status === 'error' && <ErrorDisplay error={state.message} onRetry={onRetry} />}
      {state.status === 'ready' && (
        <>
          {!state.timeline.rotation_applicable && (
            <Alert severity="info" sx={{ mb: 1 }} data-testid="timeline-not-applicable">
              {t(`pages.bed.history.timeline.notApplicable.${state.timeline.not_applicable_reason?.split('.').pop() ?? 'unknown'}`, {
                defaultValue: t('pages.bed.history.timeline.notApplicable.unknown'),
              })}
            </Alert>
          )}
          <Box component="ol" sx={{ m: 0, p: 0 }} aria-label={t('pages.bed.history.timeline.list')}>
            {state.timeline.timeline.map((entry) => (
              <YearRow
                key={entry.year}
                entry={entry}
                colors={colors}
                canEdit={canEdit}
                onBackfill={onBackfill}
                onCancel={onCancel}
                focusYear={focusYear}
                onFocusHandled={onFocusHandled}
              />
            ))}
          </Box>
        </>
      )}
    </Paper>
  );
}
