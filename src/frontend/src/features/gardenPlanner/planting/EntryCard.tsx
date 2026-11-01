/**
 * One entry of the planting dialog (REQ-053 §11.1 steps 2-4): species and cultivar, count or "as many
 * as fit", layout, the spacings with their prefill note, the pot volume check (W-016.5) and the result
 * of the preview. Fields the grower has not filled stay empty - there is no silent default (E-10).
 */
import { useMemo, useState } from 'react';
import { useTranslation } from 'react-i18next';
import Alert from '@mui/material/Alert';
import Box from '@mui/material/Box';
import Button from '@mui/material/Button';
import Card from '@mui/material/Card';
import CardContent from '@mui/material/CardContent';
import Collapse from '@mui/material/Collapse';
import IconButton from '@mui/material/IconButton';
import InputAdornment from '@mui/material/InputAdornment';
import MenuItem from '@mui/material/MenuItem';
import TextField from '@mui/material/TextField';
import ToggleButton from '@mui/material/ToggleButton';
import ToggleButtonGroup from '@mui/material/ToggleButtonGroup';
import Typography from '@mui/material/Typography';
import ArrowBackIcon from '@mui/icons-material/ArrowBack';
import ArrowDownwardIcon from '@mui/icons-material/ArrowDownward';
import ArrowForwardIcon from '@mui/icons-material/ArrowForward';
import ArrowUpwardIcon from '@mui/icons-material/ArrowUpward';
import DeleteIcon from '@mui/icons-material/Delete';
import type { Species } from '@/api/types';
import { TRIANGULAR_ROW_FACTOR, type RowDirection } from '../model/layout';
import { MARKER_SHAPES } from './LayoutCanvas';
import SpeciesPicker from './SpeciesPicker';
import {
  containerCheck,
  LAYOUT_STRATEGIES,
  parseLowerBound,
  ROW_STRATEGIES,
  type CountMode,
  type EntryErrors,
  type EntryFormState,
  type Prefill,
} from './plantingLogic';
import { PlannerTermField } from '../glossary/PlannerGlossary';
import { useCultivars } from './useCultivars';
import type { EntryPreview } from './useEntryPreviews';

interface EntryCardProps {
  index: number;
  total: number;
  form: EntryFormState;
  species: Species | null;
  allSpecies: readonly Species[];
  favorites: ReadonlySet<string>;
  errors: EntryErrors;
  preview: EntryPreview;
  prefill: Prefill | null;
  /** Rows alternate between entries: layout, row spacing and direction come from entry 1. */
  sharedRows: boolean;
  /** Freely placed points the user has put too close together. */
  flaggedPoints: number;
  onChange: (patch: Partial<EntryFormState>) => void;
  onSpecies: (key: string | null) => void;
  onRemove: (() => void) | null;
  onRemovePoint: (pointIndex: number) => void;
  /** Keyboard route for free positions: set a point at the centre of the bed. */
  onAddCentre: () => void;
  /** Move the most recently set free point by (dx, dy) metres. */
  onNudgeLast: (dx: number, dy: number) => void;
}

/** Step of the arrow buttons that move the last free position, in centimetres. */
export const NUDGE_CM = 5;

const WARNING_KEYS: Record<string, string> = {
  'layout.spacing_below_mature_width': 'belowMatureWidth',
  'planting.spacing_below_minimum': 'belowMinimum',
  'layout.no_position_fits': 'noPositionFits',
  'layout.zone_inset_not_applied': 'zoneInsetNotApplied',
};

export const ENTRY_SHAPE_NAMES = MARKER_SHAPES;

function sourceNote(source: Prefill['spacingSource'] | undefined): 'fromSpecies' | 'fromLastUsed' | 'empty' {
  if (source === 'species') return 'fromSpecies';
  if (source === 'lastUsed') return 'fromLastUsed';
  return 'empty';
}

export default function EntryCard({
  index,
  total,
  form,
  species,
  allSpecies,
  favorites,
  errors,
  preview,
  prefill,
  sharedRows,
  flaggedPoints,
  onChange,
  onSpecies,
  onRemove,
  onRemovePoint,
  onAddCentre,
  onNudgeLast,
}: EntryCardProps) {
  const { t } = useTranslation();
  const cultivars = useCultivars(form.speciesKey);
  const [moreOpen, setMoreOpen] = useState(false);
  const rowLayout = ROW_STRATEGIES.includes(form.layout);
  const container = useMemo(() => containerCheck(form.containerVolume, species), [form.containerVolume, species]);
  const errorText = (code: string | undefined) => (code ? t(`pages.bed.planting.errors.${code}`) : undefined);
  const testPrefix = `planting-entry-${index}`;
  const shapeName = ENTRY_SHAPE_NAMES[index % ENTRY_SHAPE_NAMES.length];

  const height = species?.mature_height_cm;
  const width = species?.mature_width_cm;
  const facts: string[] = [];
  if (height) facts.push(t('pages.bed.planting.entry.height', { value: height }));
  if (width) facts.push(t('pages.bed.planting.entry.width', { value: width }));
  if (species?.support_required) facts.push(t('pages.bed.planting.entry.supportRequired'));

  const spacingHelp = errors.spacing
    ? errorText(errors.spacing)
    : form.spacing && prefill?.spacingSource && prefill.spacingSource !== 'none'
      ? t(`pages.bed.planting.entry.${sourceNote(prefill.spacingSource)}`)
      : !form.spacing && form.speciesKey
        ? t('pages.bed.planting.entry.empty')
        : undefined;

  return (
    <Card variant="outlined" component="section" aria-label={t('pages.bed.planting.entry.title', { n: index + 1 })} data-testid={testPrefix}>
      <CardContent sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
        <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: 1 }}>
          <Typography variant="subtitle1" component="h3">
            {t('pages.bed.planting.entry.title', { n: index + 1 })}
            {total > 1 ? (
              <Typography component="span" variant="caption" color="text.secondary">
                {' · '}
                {t(`pages.bed.planting.entry.shape.${shapeName}`)}
              </Typography>
            ) : null}
          </Typography>
          {onRemove ? (
            <IconButton
              onClick={onRemove}
              aria-label={t('pages.bed.planting.entry.remove', { n: index + 1 })}
              sx={{ minWidth: 44, minHeight: 44 }}
              data-testid={`${testPrefix}-remove`}
            >
              <DeleteIcon />
            </IconButton>
          ) : null}
        </Box>

        <SpeciesPicker
          species={allSpecies}
          value={form.speciesKey}
          favorites={favorites}
          label={t('pages.bed.planting.entry.species')}
          error={errorText(errors.species)}
          autoFocus={index === total - 1}
          testId={`${testPrefix}-species`}
          onChange={onSpecies}
        />
        {cultivars.length > 0 ? (
          <TextField
            select
            label={t('pages.bed.planting.entry.cultivar')}
            value={form.cultivarKey ?? ''}
            onChange={(event) => onChange({ cultivarKey: event.target.value || null })}
            sx={{ '& .MuiInputBase-root': { minHeight: 48 } }}
            slotProps={{ htmlInput: { 'data-testid': `${testPrefix}-cultivar` } }}
          >
            <MenuItem value="">{t('pages.bed.planting.entry.noCultivar')}</MenuItem>
            {cultivars.map((cultivar) => (
              <MenuItem key={cultivar.key} value={cultivar.key}>
                {cultivar.name}
              </MenuItem>
            ))}
          </TextField>
        ) : null}
        {facts.length > 0 ? (
          <Typography variant="body2" color="text.secondary" data-testid={`${testPrefix}-facts`}>
            {facts.join(' · ')}
          </Typography>
        ) : null}

        <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1 }}>
          <Typography id={`${testPrefix}-count-label`} variant="body2" color="text.secondary">
            {t('pages.bed.planting.entry.count')}
          </Typography>
          <ToggleButtonGroup
            exclusive
            fullWidth
            value={form.countMode}
            onChange={(_, next: CountMode | null) => {
              if (next) onChange({ countMode: next });
            }}
            aria-labelledby={`${testPrefix}-count-label`}
          >
            <ToggleButton value="max" sx={{ minHeight: 48 }} data-testid={`${testPrefix}-count-max`}>
              {t('pages.bed.planting.entry.asManyAsFit')}
            </ToggleButton>
            <ToggleButton value="number" sx={{ minHeight: 48 }} data-testid={`${testPrefix}-count-number`}>
              {t('pages.bed.planting.entry.exactCount')}
            </ToggleButton>
          </ToggleButtonGroup>
          {form.countMode === 'number' ? (
            <TextField
              label={t('pages.bed.planting.entry.countField')}
              value={form.count}
              onChange={(event) => onChange({ count: event.target.value })}
              error={Boolean(errors.count)}
              helperText={errorText(errors.count)}
              slotProps={{ htmlInput: { inputMode: 'numeric', 'data-testid': `${testPrefix}-count` } }}
              sx={{ '& .MuiInputBase-root': { minHeight: 48 } }}
            />
          ) : null}
        </Box>

        <TextField
          select
          label={t('pages.bed.planting.entry.layout')}
          value={form.layout}
          disabled={sharedRows}
          onChange={(event) => onChange({ layout: event.target.value as EntryFormState['layout'] })}
          helperText={
            sharedRows
              ? t('pages.bed.planting.entry.sharedRows')
              : t(`pages.bed.planting.layoutHelp.${form.layout}`)
          }
          sx={{ '& .MuiInputBase-root': { minHeight: 48 } }}
          slotProps={{ htmlInput: { 'data-testid': `${testPrefix}-layout` } }}
        >
          {LAYOUT_STRATEGIES.map((value) => (
            <MenuItem key={value} value={value}>
              {t(`enums.layoutStrategy.${value}`)}
            </MenuItem>
          ))}
        </TextField>

        {form.layout !== 'free' ? (
          <PlannerTermField term="pflanzabstand">
            <TextField
              label={t('pages.bed.planting.entry.spacing')}
              value={form.spacing}
              onChange={(event) => onChange({ spacing: event.target.value })}
              required
              error={Boolean(errors.spacing)}
              helperText={spacingHelp}
              slotProps={{
                input: { endAdornment: <InputAdornment position="end">cm</InputAdornment> },
                htmlInput: { inputMode: 'decimal', 'data-testid': `${testPrefix}-spacing` },
              }}
              sx={{ '& .MuiInputBase-root': { minHeight: 48 } }}
            />
          </PlannerTermField>
        ) : (
          <TextField
            label={t('pages.bed.planting.entry.minSpacing')}
            value={form.spacing}
            onChange={(event) => onChange({ spacing: event.target.value })}
            error={Boolean(errors.spacing)}
            helperText={errorText(errors.spacing) ?? t('pages.bed.planting.entry.minSpacingHelp')}
            slotProps={{
              input: { endAdornment: <InputAdornment position="end">cm</InputAdornment> },
              htmlInput: { inputMode: 'decimal', 'data-testid': `${testPrefix}-spacing` },
            }}
            sx={{ '& .MuiInputBase-root': { minHeight: 48 } }}
          />
        )}

        {form.layout === 'rows' && !sharedRows ? (
          <PlannerTermField term="reihenabstand">
            <TextField
              label={t('pages.bed.planting.entry.rowSpacing')}
              value={form.rowSpacing}
              onChange={(event) => onChange({ rowSpacing: event.target.value })}
              required
              error={Boolean(errors.rowSpacing)}
              helperText={
                errors.rowSpacing
                  ? errorText(errors.rowSpacing)
                  : form.rowSpacing && prefill?.rowSpacingSource && prefill.rowSpacingSource !== 'none'
                    ? t(`pages.bed.planting.entry.${sourceNote(prefill.rowSpacingSource)}`)
                    : undefined
              }
              slotProps={{
                input: { endAdornment: <InputAdornment position="end">cm</InputAdornment> },
                htmlInput: { inputMode: 'decimal', 'data-testid': `${testPrefix}-row-spacing` },
              }}
              sx={{ '& .MuiInputBase-root': { minHeight: 48 } }}
            />
          </PlannerTermField>
        ) : null}
        {form.layout === 'triangular' ? (
          <Typography variant="body2" color="text.secondary" data-testid={`${testPrefix}-derived-row`}>
            {t('pages.bed.planting.entry.derivedRowSpacing', {
              value:
                parseLowerBound(form.spacing) !== null
                  ? Math.round((parseLowerBound(form.spacing) ?? 0) * TRIANGULAR_ROW_FACTOR * 10) / 10
                  : '–',
            })}
          </Typography>
        ) : null}

        <Box>
          <Button
            size="small"
            onClick={() => setMoreOpen((open) => !open)}
            aria-expanded={moreOpen}
            sx={{ minHeight: 44 }}
            data-testid={`${testPrefix}-more`}
          >
            {t(moreOpen ? 'pages.bed.planting.entry.lessOptions' : 'pages.bed.planting.entry.moreOptions')}
          </Button>
          <Collapse in={moreOpen} unmountOnExit>
            <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2, pt: 1 }}>
              {rowLayout && !sharedRows ? (
                <TextField
                  select
                  label={t('pages.bed.planting.entry.rowDirection')}
                  value={form.rowDirection}
                  onChange={(event) => onChange({ rowDirection: event.target.value as RowDirection })}
                  sx={{ '& .MuiInputBase-root': { minHeight: 48 } }}
                >
                  {(['along_length', 'along_width'] as const).map((value) => (
                    <MenuItem key={value} value={value}>
                      {t(`enums.rowDirection.${value}`)}
                    </MenuItem>
                  ))}
                </TextField>
              ) : null}
              {form.layout !== 'free' && !sharedRows ? (
                <PlannerTermField term="randabstand">
                  <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
                    <TextField
                      label={t('pages.bed.planting.entry.edgeAlong')}
                      value={form.edgeAlong}
                      onChange={(event) => onChange({ edgeAlong: event.target.value })}
                      error={Boolean(errors.edgeAlong)}
                      helperText={errorText(errors.edgeAlong) ?? t('pages.bed.planting.entry.edgeHelp')}
                      slotProps={{
                        input: { endAdornment: <InputAdornment position="end">cm</InputAdornment> },
                        htmlInput: { inputMode: 'decimal' },
                      }}
                    />
                    <TextField
                      label={t('pages.bed.planting.entry.edgeAcross')}
                      value={form.edgeAcross}
                      onChange={(event) => onChange({ edgeAcross: event.target.value })}
                      error={Boolean(errors.edgeAcross)}
                      helperText={errorText(errors.edgeAcross) ?? t('pages.bed.planting.entry.edgeHelp')}
                      slotProps={{
                        input: { endAdornment: <InputAdornment position="end">cm</InputAdornment> },
                        htmlInput: { inputMode: 'decimal' },
                      }}
                    />
                  </Box>
                </PlannerTermField>
              ) : null}
              {container.recommendedL !== null ? (
                <TextField
                  label={t('pages.bed.planting.entry.containerVolume')}
                  value={form.containerVolume}
                  onChange={(event) => onChange({ containerVolume: event.target.value })}
                  helperText={t('pages.bed.planting.entry.containerHelp', { value: container.recommendedL })}
                  slotProps={{
                    input: { endAdornment: <InputAdornment position="end">l</InputAdornment> },
                    htmlInput: { inputMode: 'decimal', 'data-testid': `${testPrefix}-container` },
                  }}
                />
              ) : null}
            </Box>
          </Collapse>
        </Box>
        {container.volumeBelow ? (
          <Alert severity="warning" data-testid={`${testPrefix}-container-warning`}>
            {t('pages.bed.planting.entry.containerBelow', { value: container.recommendedL })}
          </Alert>
        ) : null}
        {species?.min_container_depth_cm && form.containerVolume.trim() !== '' ? (
          <Typography variant="caption" color="text.secondary">
            {t('pages.bed.planting.entry.minDepth', { value: species.min_container_depth_cm })}
          </Typography>
        ) : null}

        {form.layout === 'free' ? (
          <Box data-testid={`${testPrefix}-points`}>
            <Typography variant="body2" color="text.secondary">
              {t('pages.bed.planting.entry.freeHelp')}
            </Typography>
            <Typography variant="body2" aria-live="polite">
              {t('pages.bed.planting.entry.pointCount', { count: form.freePoints.length })}
              {flaggedPoints > 0 ? ` · ${t('pages.bed.planting.entry.tooClose', { count: flaggedPoints })}` : ''}
            </Typography>
            {errors.points ? (
              <Typography variant="caption" color="error">
                {errorText(errors.points)}
              </Typography>
            ) : null}
            <Box sx={{ display: 'flex', flexWrap: 'wrap', alignItems: 'center', gap: 1, my: 1 }}>
              <Button
                variant="outlined"
                onClick={onAddCentre}
                sx={{ minHeight: 48 }}
                data-testid={`${testPrefix}-add-centre`}
              >
                {t('pages.bed.planting.entry.addPointCentre')}
              </Button>
            </Box>
            {form.freePoints.length > 0 ? (
              <Box sx={{ mb: 1 }}>
                <Box
                  role="group"
                  aria-label={t('pages.bed.planting.entry.nudgeGroup')}
                  sx={{ display: 'flex', gap: 1, flexWrap: 'wrap' }}
                >
                  {(
                    [
                      ['up', 0, 1, <ArrowUpwardIcon key="u" />],
                      ['down', 0, -1, <ArrowDownwardIcon key="d" />],
                      ['left', -1, 0, <ArrowBackIcon key="l" />],
                      ['right', 1, 0, <ArrowForwardIcon key="r" />],
                    ] as const
                  ).map(([name, dx, dy, icon]) => (
                    <IconButton
                      key={name}
                      aria-label={`${t('pages.bed.planting.entry.nudgeGroup')}: ${t(`pages.bed.planting.position.${name}`)}`}
                      onClick={() => onNudgeLast((dx * NUDGE_CM) / 100, (dy * NUDGE_CM) / 100)}
                      sx={{ width: 48, height: 48, border: 1, borderColor: 'divider' }}
                      data-testid={`${testPrefix}-nudge-${name}`}
                    >
                      {icon}
                    </IconButton>
                  ))}
                </Box>
                <Typography variant="caption" color="text.secondary">
                  {t('pages.bed.planting.entry.nudgeHelp', { cm: NUDGE_CM })}
                </Typography>
              </Box>
            ) : null}
            <Box component="ul" sx={{ listStyle: 'none', m: 0, p: 0, display: 'flex', flexWrap: 'wrap', gap: 0.5 }}>
              {form.freePoints.map((point, pointIndex) => (
                <li key={`${point[0]}-${point[1]}-${pointIndex}`}>
                  <Button
                    size="small"
                    variant="outlined"
                    onClick={() => onRemovePoint(pointIndex)}
                    aria-label={t('pages.bed.planting.entry.removePoint', {
                      n: pointIndex + 1,
                      x: Math.round(point[0] * 100),
                      y: Math.round(point[1] * 100),
                    })}
                    sx={{ minHeight: 44, minWidth: 44 }}
                  >
                    {pointIndex + 1}
                  </Button>
                </li>
              ))}
            </Box>
          </Box>
        ) : null}

        <PreviewSummary preview={preview} testId={`${testPrefix}-result`} />
      </CardContent>
    </Card>
  );
}

function PreviewSummary({ preview, testId }: { preview: EntryPreview; testId: string }) {
  const { t } = useTranslation();
  if (preview.error) {
    const key = preview.error.code ? preview.error.code.replace(/\./g, '_') : null;
    return (
      <Alert severity="error" data-testid={testId}>
        {key ? t(`pages.bed.planting.layoutErrors.${key}`, { defaultValue: preview.error.message }) : preview.error.message}
      </Alert>
    );
  }
  if (preview.capacityMax === 0 && preview.count === 0 && preview.positions.length === 0 && preview.zones.length === 0) {
    return null;
  }
  return (
    <Box data-testid={testId} aria-live="polite">
      <Typography variant="body1">
        {t('pages.bed.planting.entry.result', { count: preview.count, max: preview.capacityMax })}
        {preview.pending ? (
          <Typography component="span" variant="caption" color="text.secondary">
            {' · '}
            {t('pages.bed.planting.entry.confirming')}
          </Typography>
        ) : null}
      </Typography>
      {preview.warnings.map((warning) => {
        const key = WARNING_KEYS[warning.code];
        return (
          <Alert key={warning.code} severity="warning" sx={{ mt: 1 }}>
            {key
              ? t(`pages.bed.planting.warnings.${key}`, warning.detail)
              : warning.code}
          </Alert>
        );
      })}
    </Box>
  );
}
