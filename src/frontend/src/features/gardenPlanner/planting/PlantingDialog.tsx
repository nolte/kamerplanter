/**
 * The planting dialog (REQ-053 §11.1, GP-FR-060…073, GP-FR-132): species and count, layout and spacings
 * with their prefill, the hints on crop rotation and neighbours *before* the layout, a live preview on
 * the bed (TS port first, the server's answer replaces it), alternating rows for mixed cultures and
 * freely placed positions. A hint never blocks; from a warning on, planting anyway needs a reason.
 */
import { useCallback, useEffect, useMemo, useState } from 'react';
import { useTranslation } from 'react-i18next';
import Alert from '@mui/material/Alert';
import Box from '@mui/material/Box';
import Button from '@mui/material/Button';
import Dialog from '@mui/material/Dialog';
import DialogActions from '@mui/material/DialogActions';
import DialogContent from '@mui/material/DialogContent';
import DialogTitle from '@mui/material/DialogTitle';
import FormControlLabel from '@mui/material/FormControlLabel';
import Switch from '@mui/material/Switch';
import TextField from '@mui/material/TextField';
import Typography from '@mui/material/Typography';
import useMediaQuery from '@mui/material/useMediaQuery';
import { useTheme } from '@mui/material/styles';
import AddIcon from '@mui/icons-material/Add';
import { listAllSpecies } from '@/api/endpoints/species';
import type { Species } from '@/api/types';
import LoadingSkeleton from '@/components/common/LoadingSkeleton';
import { useApiError } from '@/hooks/useApiError';
import { useServerFavorites } from '@/hooks/useServerFavorites';
import { toLocalShape } from '../model/geometry';
import { computeLayout } from '../model/layout';
import type { Geometry, Point, SunExposure } from '../model/types';
import EntryCard from './EntryCard';
import HintsPanel from './HintsPanel';
import { siteFitOf } from './siteFitOf';
import LayoutCanvas, { MARKER_SHAPES, type CanvasLayer } from './LayoutCanvas';
import { listBedSlots } from './plantingApi';
import {
  alternatingRows,
  canAlternate,
  emptyEntry,
  hasErrors,
  insideBed,
  MAX_ENTRIES,
  needsOverrideReason,
  parseLowerBound,
  prefillFor,
  requestedCount,
  ROW_STRATEGIES,
  toEntryLayout,
  tooClosePoints,
  validateEntry,
  worstSeverity,
  type EntryFormState,
  type Prefill,
} from './plantingLogic';
import { quickBody, readLastUsed, submitQuick, submitRuns, writeLastUsed } from './plantingSubmit';
import type { RotationSeverity } from './plantingTypes';
import { speciesLabel } from './SpeciesPicker';
import { useBedHints, useMixedCompatibility } from './useBedHints';
import { useEntryPreviews, type EntryPreview, type PreviewRequest } from './useEntryPreviews';

export interface PlantedResult {
  runKeys: string[];
  plantCount: number;
  /** The field-mode shortcut was used: the plants exist already. */
  quick: boolean;
}

interface PlantingDialogProps {
  bedKey: string;
  bedName: string;
  geometry: Geometry;
  /** The sun class of the bed (GP-FR-157); with the species' light requirement it gives the `site_fit` hint. */
  sunExposure?: SunExposure;
  onClose: () => void;
  onPlanted: (result: PlantedResult) => void;
  /** Start with "Already planted" on: the field-mode chip "Planted" opens the quick-planting shortcut (GP-UX-027). */
  initialAlreadyPlanted?: boolean;
  /**
   * Minimum edge in px of the dialog's own controls (add entry, switches, date, actions); field mode passes
   * the kiosk target (64 px, GP-UX-020). The entry cards keep their own sizes.
   */
  touchTarget?: number;
}

function todayText(): string {
  const now = new Date();
  const pad = (value: number) => String(value).padStart(2, '0');
  return `${now.getFullYear()}-${pad(now.getMonth() + 1)}-${pad(now.getDate())}`;
}

/** Entries 2..n take layout, row spacing, direction and margins of entry 1 when the rows alternate. */
function shareRows(forms: readonly EntryFormState[]): EntryFormState[] {
  const [first, ...rest] = forms;
  return [
    first,
    ...rest.map((form) => ({
      ...form,
      layout: first.layout,
      rowSpacing: first.rowSpacing,
      rowDirection: first.rowDirection,
      edgeAlong: first.edgeAlong,
      edgeAcross: first.edgeAcross,
    })),
  ];
}

const IDLE_PREVIEW: EntryPreview = {
  positions: [],
  zones: [],
  count: 0,
  capacityMax: 0,
  warnings: [],
  source: 'local',
  pending: false,
  error: null,
};

export default function PlantingDialog({
  bedKey,
  bedName,
  geometry,
  sunExposure = 'unknown',
  onClose,
  onPlanted,
  initialAlreadyPlanted = false,
  touchTarget = 48,
}: PlantingDialogProps) {
  const { t } = useTranslation();
  const theme = useTheme();
  const fullScreen = useMediaQuery(theme.breakpoints.down('md'));
  const { handleError } = useApiError();
  const { favorites } = useServerFavorites('species');

  const [catalogue, setCatalogue] = useState<{ status: 'loading' } | { status: 'ready'; items: Species[] } | { status: 'error' }>({
    status: 'loading',
  });
  const [existing, setExisting] = useState<Point[]>([]);
  const [forms, setForms] = useState<EntryFormState[]>([emptyEntry('e1')]);
  const [prefills, setPrefills] = useState<Record<string, Prefill | null>>({});
  const [nextId, setNextId] = useState(2);
  const [activeId, setActiveId] = useState('e1');
  const [alternate, setAlternate] = useState(true);
  const [alreadyPlanted, setAlreadyPlanted] = useState(initialAlreadyPlanted);
  const [plantedFrom, setPlantedFrom] = useState(todayText);
  const [overrideChecked, setOverrideChecked] = useState(false);
  const [overrideReason, setOverrideReason] = useState('');
  const [showErrors, setShowErrors] = useState(false);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    let cancelled = false;
    listAllSpecies()
      .then((response) => {
        if (!cancelled) setCatalogue({ status: 'ready', items: response.items });
      })
      .catch(() => {
        if (!cancelled) setCatalogue({ status: 'error' });
      });
    listBedSlots(bedKey)
      .then((slots) => {
        if (cancelled) return;
        setExisting(
          slots.flatMap((slot) =>
            !slot.archived_at && slot.geometry?.kind === 'point' ? [slot.geometry.origin] : [],
          ),
        );
      })
      .catch(() => undefined); // the grey dots are context only
    return () => {
      cancelled = true;
    };
  }, [bedKey]);

  const species = useMemo(() => (catalogue.status === 'ready' ? catalogue.items : []), [catalogue]);
  const speciesByKey = useMemo(() => new Map(species.map((s) => [s.key, s])), [species]);
  const speciesNames = useMemo(() => new Map(species.map((s) => [s.key, speciesLabel(s)])), [species]);

  const sharing = alternate && canAlternate(forms);
  const effective = useMemo(() => (sharing ? shareRows(forms) : forms), [sharing, forms]);

  // Alternating rows (GP-FR-070): the rows are those of entry 1's full layout; entry k takes every nth.
  const rowAssignments = useMemo(() => {
    const result: Record<string, number[] | null> = {};
    if (!sharing) {
      for (const form of effective) result[form.id] = null;
      return result;
    }
    const first = effective[0];
    const width = parseLowerBound(speciesByKey.get(first.speciesKey ?? '')?.mature_width_cm);
    const layout = toEntryLayout(first, width, null);
    let rows = 0;
    if (layout) {
      try {
        const full = computeLayout(geometry, layout, null);
        rows = full.slots.reduce((max, slot) => Math.max(max, (slot.row_index ?? -1) + 1), 0);
      } catch {
        rows = 0;
      }
    }
    effective.forEach((form, index) => {
      result[form.id] = alternatingRows(rows, effective.length, index);
    });
    return result;
  }, [sharing, effective, geometry, speciesByKey]);

  const requests = useMemo<PreviewRequest[]>(
    () =>
      effective.map((form) => ({
        id: form.id,
        layout: toEntryLayout(
          form,
          parseLowerBound(speciesByKey.get(form.speciesKey ?? '')?.mature_width_cm),
          rowAssignments[form.id] ?? null,
        ),
        maxCount: requestedCount(form),
      })),
    [effective, speciesByKey, rowAssignments],
  );
  const computed = useEntryPreviews(bedKey, geometry, requests);

  const previews = useMemo(() => {
    const merged: Record<string, EntryPreview> = {};
    for (const form of effective) {
      if (form.layout === 'free') {
        merged[form.id] = {
          ...IDLE_PREVIEW,
          positions: form.freePoints.map((point) => ({ point, row: null })),
          count: form.freePoints.length,
          capacityMax: form.freePoints.length,
        };
      } else {
        merged[form.id] = computed[form.id] ?? IDLE_PREVIEW;
      }
    }
    return merged;
  }, [effective, computed]);

  const speciesKeys = useMemo(() => effective.map((form) => form.speciesKey), [effective]);
  const hintStates = useBedHints(bedKey, speciesKeys);
  const mix = useMixedCompatibility(speciesKeys);
  const severity = useMemo<RotationSeverity>(() => {
    const all: RotationSeverity[] = [];
    for (const state of Object.values(hintStates)) if (state.status === 'ready') all.push(state.data.severity);
    if (mix.some((pair) => pair.kind === 'incompatible')) all.push('WARNING');
    return worstSeverity(all);
  }, [hintStates, mix]);
  const hintSpecies = useMemo(
    () =>
      [...new Set(speciesKeys.filter((key): key is string => Boolean(key)))].map((key) => ({
        key,
        name: speciesNames.get(key) ?? key,
        state: hintStates[key],
        siteFit: siteFitOf(speciesByKey.get(key), sunExposure),
      })),
    [speciesKeys, speciesNames, hintStates, speciesByKey, sunExposure],
  );

  const layers = useMemo<CanvasLayer[]>(
    () =>
      effective.map((form, index) => {
        const preview = previews[form.id];
        const spacing = parseLowerBound(form.spacing);
        const colors = [
          theme.palette.success.dark,
          theme.palette.info.dark,
          theme.palette.warning.dark,
          theme.palette.secondary.dark,
        ];
        return {
          id: form.id,
          shape: MARKER_SHAPES[index % MARKER_SHAPES.length],
          color: colors[index % colors.length],
          positions: preview.positions.map((p) => p.point),
          zones: preview.zones,
          flagged: form.layout === 'free' && spacing ? tooClosePoints(form.freePoints, spacing) : [],
        };
      }),
    [effective, previews, theme],
  );
  const freeForm = effective.find((form) => form.id === activeId && form.layout === 'free') ??
    effective.find((form) => form.layout === 'free');

  const change = useCallback((id: string, patch: Partial<EntryFormState>) => {
    setForms((current) => current.map((form) => (form.id === id ? { ...form, ...patch } : form)));
  }, []);

  const chooseSpecies = useCallback(
    (id: string, key: string | null) => {
      const chosen = key ? (speciesByKey.get(key) ?? null) : null;
      const prefill = key ? prefillFor(chosen, readLastUsed(key)) : null;
      setPrefills((current) => ({ ...current, [id]: prefill }));
      setForms((current) =>
        current.map((form) =>
          form.id === id
            ? {
                ...form,
                speciesKey: key,
                cultivarKey: null,
                spacing: prefill?.spacing ?? '',
                rowSpacing: prefill?.rowSpacing ?? '',
                layout: prefill?.layout && form.layout === 'grid' ? prefill.layout : form.layout,
              }
            : form,
        ),
      );
    },
    [speciesByKey],
  );

  const addEntry = () => {
    const id = `e${nextId}`;
    setNextId((value) => value + 1);
    setForms((current) => [...current, emptyEntry(id)]);
    setActiveId(id);
  };
  const removeEntry = (id: string) => setForms((current) => current.filter((form) => form.id !== id));

  const quickAllowed =
    forms.length === 1 && ROW_STRATEGIES.includes(forms[0].layout) && forms[0].speciesKey !== null;
  // The shortcut has no edge-margin fields: with margins set the plants would not stand where the preview shows.
  const marginsSet = forms[0].edgeAlong.trim() !== '' || forms[0].edgeAcross.trim() !== '';
  const quick = alreadyPlanted && quickAllowed && !marginsSet;

  const errorsByEntry = useMemo(
    () => Object.fromEntries(effective.map((form) => [form.id, validateEntry(form)])),
    [effective],
  );
  const mustGiveReason = needsOverrideReason(severity);
  // The strength is only known once every chosen species has been checked; a failed check is "unknown", shown
  // as such, and does not hold the grower back (D-09) - but a check still running does.
  const hintsPending = hintSpecies.some((hint) => !hint.state || hint.state.status === 'loading');

  const waitingForHints = catalogue.status === 'ready' && hintsPending;

  const submit = async () => {
    const invalid = effective.some((form) => hasErrors(errorsByEntry[form.id]));
    const refused = effective.some((form) => previews[form.id].error !== null);
    const noPositions = effective.some((form) => previews[form.id].count === 0);
    if (invalid || refused || noPositions || (mustGiveReason && (!overrideChecked || overrideReason.trim() === ''))) {
      setShowErrors(true);
      return;
    }
    const reason = mustGiveReason ? overrideReason.trim() : null;
    setSaving(true);
    try {
      let result: PlantedResult;
      if (quick) {
        const form = effective[0];
        const chosen = speciesByKey.get(form.speciesKey ?? '');
        if (!chosen) return;
        const response = await submitQuick(bedKey, quickBody(form, chosen, previews[form.id], plantedFrom, reason));
        result = { runKeys: [response.run_key], plantCount: response.plant_keys.length, quick: true };
      } else {
        const outcome = await submitRuns({
          bedKey,
          bedName,
          forms: effective,
          species,
          previews,
          rowAssignments,
          plantedFrom,
          overrideReason: reason,
        });
        result = { ...outcome, quick: false };
      }
      writeLastUsed(effective);
      onPlanted(result);
    } catch (error) {
      handleError(error);
    } finally {
      setSaving(false);
    }
  };

  // A position outside the bed frame would be refused by the server (V-04); the canvas simply does not take it.
  const onAddPoint = (point: Point) => {
    if (freeForm && insideBed(geometry, point)) {
      change(freeForm.id, { freePoints: [...freeForm.freePoints, point] });
    }
  };
  const onMovePoint = (layerId: string, index: number, point: Point) => {
    const form = forms.find((candidate) => candidate.id === layerId);
    if (form && insideBed(geometry, point)) {
      change(layerId, { freePoints: form.freePoints.map((p, i) => (i === index ? point : p)) });
    }
  };

  // Keyboard and switch access to free positions: a point at the centre, then moved with the arrow buttons.
  const bedCentre = useMemo<Point>(() => {
    const shape = toLocalShape(geometry);
    if (shape.kind === 'circle') return shape.center;
    const xs = shape.vertices.map((v) => v[0]);
    const ys = shape.vertices.map((v) => v[1]);
    return [(Math.min(...xs) + Math.max(...xs)) / 2, (Math.min(...ys) + Math.max(...ys)) / 2];
  }, [geometry]);
  const roundCm = (value: number) => Math.round(value * 100) / 100;
  const addCentre = (id: string) => {
    const form = forms.find((candidate) => candidate.id === id);
    const point: Point = [roundCm(bedCentre[0]), roundCm(bedCentre[1])];
    if (form && insideBed(geometry, point)) change(id, { freePoints: [...form.freePoints, point] });
  };
  const nudgeLast = (id: string, dx: number, dy: number) => {
    const form = forms.find((candidate) => candidate.id === id);
    if (!form || form.freePoints.length === 0) return;
    const last = form.freePoints[form.freePoints.length - 1];
    const next: Point = [roundCm(last[0] + dx), roundCm(last[1] + dy)];
    if (insideBed(geometry, next)) change(id, { freePoints: [...form.freePoints.slice(0, -1), next] });
  };

  const hintsVisible = hintSpecies.length > 0;

  return (
    <Dialog
      open
      onClose={saving ? undefined : onClose}
      fullScreen={fullScreen}
      maxWidth="lg"
      fullWidth
      aria-labelledby="planting-dialog-title"
      data-testid="planting-dialog"
    >
      <DialogTitle id="planting-dialog-title">{t('pages.bed.planting.dialog.title', { bed: bedName })}</DialogTitle>
      <DialogContent>
        {catalogue.status === 'loading' ? <LoadingSkeleton variant="card" /> : null}
        {catalogue.status === 'error' ? (
          <Alert severity="error">{t('pages.bed.planting.dialog.speciesFailed')}</Alert>
        ) : null}
        {catalogue.status === 'ready' ? (
          <Box
            sx={{
              display: 'grid',
              gridTemplateColumns: { xs: 'minmax(0, 1fr)', md: 'minmax(0, 1fr) minmax(0, 1fr)' },
              gap: 3,
              alignItems: 'start',
              pt: 1,
            }}
          >
            <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
              {hintsVisible ? (
                <HintsPanel
                  species={hintSpecies}
                  bedSun={sunExposure}
                  speciesNames={speciesNames}
                  mix={mix}
                  severity={severity}
                  overrideChecked={overrideChecked}
                  overrideReason={overrideReason}
                  showReasonError={showErrors}
                  onOverrideChecked={setOverrideChecked}
                  onOverrideReason={setOverrideReason}
                />
              ) : (
                <Typography variant="body2" color="text.secondary">
                  {t('pages.bed.planting.dialog.intro')}
                </Typography>
              )}
              {effective.map((form, index) => (
                <Box key={form.id} onFocusCapture={() => setActiveId(form.id)}>
                  <EntryCard
                    index={index}
                    total={effective.length}
                    form={form}
                    species={speciesByKey.get(form.speciesKey ?? '') ?? null}
                    allSpecies={species}
                    favorites={favorites}
                    errors={showErrors ? errorsByEntry[form.id] : {}}
                    preview={previews[form.id]}
                    prefill={prefills[form.id] ?? null}
                    sharedRows={sharing && index > 0}
                    flaggedPoints={layers[index]?.flagged?.length ?? 0}
                    onChange={(patch) => change(form.id, patch)}
                    onSpecies={(key) => chooseSpecies(form.id, key)}
                    onRemove={effective.length > 1 ? () => removeEntry(form.id) : null}
                    onAddCentre={() => addCentre(form.id)}
                    onNudgeLast={(dx, dy) => nudgeLast(form.id, dx, dy)}
                    onRemovePoint={(pointIndex) =>
                      change(form.id, { freePoints: forms[index].freePoints.filter((_, i) => i !== pointIndex) })
                    }
                  />
                </Box>
              ))}
              {forms.length < MAX_ENTRIES ? (
                <Button
                  startIcon={<AddIcon />}
                  onClick={addEntry}
                  sx={{ alignSelf: 'flex-start', minHeight: touchTarget }}
                  data-testid="planting-add-entry"
                >
                  {t('pages.bed.planting.dialog.addEntry')}
                </Button>
              ) : null}
              {canAlternate(forms) ? (
                <FormControlLabel
                  control={
                    <Switch
                      checked={alternate}
                      onChange={(event) => setAlternate(event.target.checked)}
                      slotProps={{ input: { 'data-testid': 'planting-alternate' } as object }}
                    />
                  }
                  label={t('pages.bed.planting.dialog.alternateRows')}
                  sx={{ minHeight: touchTarget }}
                />
              ) : null}
            </Box>

            <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2, position: { md: 'sticky' }, top: { md: 0 } }}>
              <Typography variant="subtitle1" component="h3">
                {t('pages.bed.planting.dialog.preview')}
              </Typography>
              <LayoutCanvas
                bed={geometry}
                layers={layers}
                existing={existing}
                label={t('pages.bed.planting.dialog.canvasLabel', { bed: bedName })}
                interactiveLayerId={freeForm?.id}
                onAdd={freeForm ? onAddPoint : undefined}
                onMove={freeForm ? onMovePoint : undefined}
                testId="planting-canvas"
              />
              {freeForm ? (
                <Typography variant="caption" color="text.secondary">
                  {t('pages.bed.planting.dialog.freeCanvasHelp')}
                </Typography>
              ) : null}
              <TextField
                type="date"
                label={t('pages.bed.planting.dialog.plantedFrom')}
                value={plantedFrom}
                onChange={(event) => setPlantedFrom(event.target.value)}
                required
                slotProps={{
                  inputLabel: { shrink: true },
                  htmlInput: { 'data-testid': 'planting-date' },
                }}
                sx={{ '& .MuiInputBase-root': { minHeight: touchTarget } }}
              />
              {quickAllowed ? (
                <FormControlLabel
                  control={
                    <Switch
                      checked={alreadyPlanted}
                      disabled={marginsSet}
                      onChange={(event) => setAlreadyPlanted(event.target.checked)}
                      slotProps={{ input: { 'data-testid': 'planting-already' } as object }}
                    />
                  }
                  label={t('pages.bed.planting.dialog.alreadyPlanted')}
                  sx={{ minHeight: touchTarget }}
                />
              ) : null}
              {quickAllowed && marginsSet ? (
                <Typography variant="caption" color="text.secondary" data-testid="planting-already-margins">
                  {t('pages.bed.planting.dialog.alreadyPlantedMargins')}
                </Typography>
              ) : null}
              {quick ? (
                <Typography variant="caption" color="text.secondary">
                  {t('pages.bed.planting.dialog.alreadyPlantedHelp')}
                </Typography>
              ) : null}
            </Box>
          </Box>
        ) : null}
      </DialogContent>
      <DialogActions
        sx={{ px: { xs: 2, sm: 3 }, py: 1.5, flexWrap: 'wrap', rowGap: 1, borderTop: 1, borderColor: 'divider' }}
      >
        {waitingForHints ? (
          <Typography
            id="planting-submit-reason"
            variant="body2"
            color="text.secondary"
            role="status"
            sx={{ flex: '1 1 100%' }}
            data-testid="planting-submit-reason"
          >
            {t('pages.bed.planting.dialog.submitWaiting')}
          </Typography>
        ) : null}
        <Button onClick={onClose} disabled={saving} sx={{ minHeight: touchTarget }}>
          {t('common.cancel')}
        </Button>
        <Button
          variant="contained"
          onClick={() => void submit()}
          disabled={saving || catalogue.status !== 'ready' || hintsPending}
          aria-describedby={waitingForHints ? 'planting-submit-reason' : undefined}
          sx={{ minHeight: touchTarget, minWidth: touchTarget }}
          data-testid="planting-submit"
        >
          {mustGiveReason && overrideChecked
            ? t('pages.bed.planting.dialog.plantAnyway')
            : quick
              ? t('pages.bed.planting.dialog.recordPlanted')
              : t('pages.bed.planting.dialog.plan')}
        </Button>
      </DialogActions>
    </Dialog>
  );
}
