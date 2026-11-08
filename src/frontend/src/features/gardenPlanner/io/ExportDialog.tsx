/**
 * The export dialog of the garden plan (REQ-053 GP-UX-050): format, paper, scale, layers, a preview, progress and
 * the reason when it fails. On a phone only the JSON backup and the PDF with their standard options are offered.
 * The bed list as CSV (GP-FR-145/175) has its column selection, the Excel variant and the assignment opt-in (SR-024,
 * default off); like SVG it is not offered on a phone, where GP-UX-050 limits the dialog to JSON and PDF.
 * The PDF can add the parcel list (GP-FR-176) as an extra page; the members a bed is assigned to are a second,
 * separate opt-in under it (SR-024, default off), offered only while the parcel list is chosen.
 * The PNG (GP-FR-144) is drawn in the browser from the loaded plan: 1×/2×/4×, capped to the canvas limits with a
 * hint, and the watermark "Kamerplanter · date" as an option that is off by default. It is not offered on a phone.
 * Lazy: the route chunk stays inside its budget (UI-NFR-003).
 */
import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import { useTranslation } from 'react-i18next';
import Alert from '@mui/material/Alert';
import Box from '@mui/material/Box';
import Button from '@mui/material/Button';
import Checkbox from '@mui/material/Checkbox';
import Dialog from '@mui/material/Dialog';
import DialogActions from '@mui/material/DialogActions';
import DialogContent from '@mui/material/DialogContent';
import DialogTitle from '@mui/material/DialogTitle';
import FormControl from '@mui/material/FormControl';
import FormControlLabel from '@mui/material/FormControlLabel';
import FormGroup from '@mui/material/FormGroup';
import FormLabel from '@mui/material/FormLabel';
import MenuItem from '@mui/material/MenuItem';
import Radio from '@mui/material/Radio';
import RadioGroup from '@mui/material/RadioGroup';
import Skeleton from '@mui/material/Skeleton';
import Switch from '@mui/material/Switch';
import TextField from '@mui/material/TextField';
import ToggleButton from '@mui/material/ToggleButton';
import ToggleButtonGroup from '@mui/material/ToggleButtonGroup';
import Typography from '@mui/material/Typography';
import useMediaQuery from '@mui/material/useMediaQuery';
import { useTheme } from '@mui/material/styles';
import { useAppSelector } from '@/store/hooks';
import { selectGardenPlanState } from '../state/gardenPlanSlice';
import { fitViewport, planContentBounds } from '../routes/fitViewport';
import { useRendererLabels } from '../renderer/useRendererLabels';
import { useLayerPrefs } from '../editor/useLayerPrefs';
import { useAttentionFilter } from '../editor/useAttentionFilter';
import { markerLodBedKeys } from '../renderer/scene';
import { usePlanPlantStates } from '../planting/usePlanPlantStates';
import { usePlantStateLayer } from '../planting/usePlantStateLayer';
import { lightTheme } from '@/theme/theme';
import OffscreenPlanSvg from './OffscreenPlanSvg';
import {
  MAX_CANVAS_AREA_PX,
  PNG_BASE_EDGE_PX,
  planPngFilename,
  rasterizeSvg,
  resolvePngSize,
  serializePlanSvg,
} from './pngExport';
import {
  BED_LIST_DEFAULT_COLUMNS,
  BED_LIST_SITE_CONDITION_COLUMNS,
  DEFAULT_BED_LIST_CSV_OPTIONS,
  orderedBedListColumns,
  type BedListColumn,
  type BedListCsvOptions,
} from './bedListCsv';
import { describeExportFailure, fetchBedListCsv, fetchPlanExport, saveBlob } from './ioApi';
import { usePlanPreview } from './usePlanPreview';
import {
  DEFAULT_EXPORT_OPTIONS,
  DEFAULT_PNG_EXPORT_OPTIONS,
  EXPORT_LAYERS,
  EXPORT_SCALES,
  MAX_EXPORT_KEYS,
  PNG_RESOLUTIONS,
  type ExportFormat,
  type ExportLayer,
  type ExportOptions,
  type ExportOrientation,
  type ExportPaper,
  type ExportScale,
  type ExportScope,
  type PlanSelection,
  type PngExportOptions,
  type PngResolution,
} from './types';

const PREFIX = 'pages.gardenPlan.io.export';

interface ExportDialogProps {
  open: boolean;
  siteKey: string;
  /** What is selected on the plan; the JSON backup can be limited to it (GP-FR-172). */
  selection?: PlanSelection;
  onClose: () => void;
}

const NO_SELECTION: PlanSelection = { locationKeys: [], objectKeys: [] };
const NO_BED_KEYS: readonly string[] = [];

/** The keys a partial export names: beds and (for a selection only) garden objects as `object:<key>`. */
function scopeKeys(scope: ExportScope, selection: PlanSelection): string[] {
  if (scope === 'site') return [];
  const locations = [...selection.locationKeys];
  return scope === 'subtree'
    ? locations
    : [...locations, ...selection.objectKeys.map((key) => `object:${key}`)];
}

/** The format buttons of the dialog: the three server exports, the bed list as CSV and the PNG drawn in the browser. */
type DialogFormat = ExportFormat | 'csv' | 'png';

/** The formats that are not a server plan export and keep their own options. */
type LocalFormat = 'csv' | 'png';

function errorKey(code: string | null, status: number | null): string {
  if (code === 'plan.empty') return 'empty';
  if (code === 'export.too_many_rows') return 'tooManyRows';
  if (code === 'export.unknown_column') return 'unknownColumn';
  if (code === 'export.no_columns') return 'noColumns';
  if (code === 'plan.does_not_fit') return 'doesNotFit';
  if (status === 429) return 'rateLimited';
  if (status === 403) return 'forbidden';
  return 'failed';
}

function formatSize(bytes: number): string {
  return bytes < 1024 * 1024
    ? `${Math.max(1, Math.round(bytes / 1024))} KB`
    : `${(bytes / 1024 / 1024).toFixed(1)} MB`;
}

export default function ExportDialog({
  open,
  siteKey,
  selection = NO_SELECTION,
  onClose,
}: ExportDialogProps) {
  const { t, i18n } = useTranslation();
  const theme = useTheme();
  const phone = useMediaQuery(theme.breakpoints.down('sm'));
  const [options, setOptions] = useState<ExportOptions>(DEFAULT_EXPORT_OPTIONS);
  const [localChosen, setLocalChosen] = useState<LocalFormat | null>(null);
  const [csv, setCsv] = useState<BedListCsvOptions>(DEFAULT_BED_LIST_CSV_OPTIONS);
  const [png, setPng] = useState<PngExportOptions>(DEFAULT_PNG_EXPORT_OPTIONS);
  // While set, the plan is drawn off screen for one PNG export (GP-FR-144).
  const [pngRunning, setPngRunning] = useState(false);
  const [busy, setBusy] = useState(false);
  const [failure, setFailure] = useState<string | null>(null);
  const storePlan = useAppSelector(selectGardenPlanState).plan;
  // Only the plan of this site is drawn: the file is named after `siteKey`, so a plan of another site never is.
  const plan = storePlan && storePlan.siteKey === siteKey ? storePlan : null;
  const labels = useRendererLabels();
  // Set when Download starts a PNG and cleared by the first result: a second report of the same run is ignored.
  const pngActive = useRef(false);
  // The id of the current run (Download counts it up) and whether a run is still on: a drawing that finishes after
  // its run ended, or after a newer one started, downloads nothing.
  const pngRun = useRef(0);
  const pngRunningNow = useRef(false);
  useEffect(() => {
    pngRunningNow.current = pngRunning;
  }, [pngRunning]);

  // On a phone the standard options apply and neither SVG, CSV nor PNG is offered (GP-UX-050).
  const csvMode = localChosen === 'csv' && !phone;
  const pngMode = localChosen === 'png' && !phone;
  const localMode = csvMode || pngMode;
  // The PNG shows the whole plan, fitted into the base box; 2x and 4x multiply that size.
  const pngViewport = useMemo(() => {
    const bounds = plan ? planContentBounds(plan) : null;
    return bounds ? fitViewport(bounds, PNG_BASE_EDGE_PX, PNG_BASE_EDGE_PX) : null;
  }, [plan]);
  const pngSize = pngViewport
    ? resolvePngSize(pngViewport.widthPx, pngViewport.heightPx, png.resolution)
    : null;
  // The PNG draws what the editor draws with the user's layer switches: the site-condition layers from the plan
  // itself, and the plant states with their phase colours (GP-UX-061, GP-FR-067) read for the beds at marker LOD of
  // the export's viewport, while PNG is chosen. Zones, "last watered" and companions stay out of the PNG.
  const { prefs: layerPrefs } = useLayerPrefs();
  const [attentionOnly] = useAttentionFilter();
  const plantStateOn = pngMode && layerPrefs.plantState && plan !== null;
  const stateBedKeys = useMemo(
    () => (plantStateOn && plan && pngViewport ? markerLodBedKeys(plan, pngViewport) : NO_BED_KEYS),
    [plantStateOn, plan, pngViewport],
  );
  const planStates = usePlanPlantStates(siteKey, stateBedKeys, plantStateOn);
  const { phaseColors, plantStateLayer } = usePlantStateLayer(plan, planStates, plantStateOn, attentionOnly);
  const pngRenderOptions = useMemo(
    () => ({
      sunLayer: layerPrefs.sun,
      moistureLayer: layerPrefs.moisture,
      frostLayer: layerPrefs.frost,
      ...(plantStateLayer ? { plantStateLayer, phaseColors } : {}),
    }),
    [layerPrefs.sun, layerPrefs.moisture, layerPrefs.frost, plantStateLayer, phaseColors],
  );
  // A run whose drawing can no longer mount (the plan went away after Download) ends here instead of hanging busy.
  // (`pngActive` stays set; nothing can report without a mounted drawing, and the next Download sets it anew.)
  if (pngRunning && (!plan || !pngViewport)) {
    setPngRunning(false);
    setBusy(false);
    setFailure('pngFailed');
  }
  const base: ExportOptions = phone
    ? { ...DEFAULT_EXPORT_OPTIONS, format: options.format === 'json' ? 'json' : 'pdf' }
    : options;
  // A partial backup needs something selected, and at most as many keys as the server takes.
  const available: Record<ExportScope, boolean> = {
    site: true,
    selection:
      scopeKeys('selection', selection).length > 0 &&
      scopeKeys('selection', selection).length <= MAX_EXPORT_KEYS,
    subtree: selection.locationKeys.length > 0 && selection.locationKeys.length <= MAX_EXPORT_KEYS,
  };
  const scope: ExportScope =
    base.format === 'json' && available[options.scope] ? options.scope : 'site';
  const effective: ExportOptions = { ...base, scope, keys: scopeKeys(scope, selection) };
  // Neither the CSV nor the PNG asks the server for a preview.
  const preview = usePlanPreview(siteKey, effective, open && !localMode);
  const patch = (change: Partial<ExportOptions>) => {
    setFailure(null);
    setOptions((previous) => ({ ...previous, ...change }));
  };
  const patchCsv = (change: Partial<BedListCsvOptions>) => {
    setFailure(null);
    setCsv((previous) => ({ ...previous, ...change }));
  };
  const chooseFormat = (value: DialogFormat) => {
    if (value === 'csv' || value === 'png') {
      setLocalChosen(value);
      setFailure(null);
    } else {
      setLocalChosen(null);
      patch({ format: value });
    }
  };
  const patchPng = (change: Partial<PngExportOptions>) => {
    setFailure(null);
    setPng((previous) => ({ ...previous, ...change }));
  };
  const toggleColumn = (column: BedListColumn) =>
    patchCsv({
      columns: csv.columns.includes(column)
        ? csv.columns.filter((entry) => entry !== column)
        : [...csv.columns, column],
    });
  const toggleLayer = (layer: ExportLayer) =>
    patch({
      layers: effective.layers.includes(layer)
        ? effective.layers.filter((entry) => entry !== layer)
        : EXPORT_LAYERS.filter((entry) => entry === layer || effective.layers.includes(entry)),
    });

  const { language } = i18n;
  // The off-screen drawing is in the document: inline its styles, draw it at the chosen size and download it.
  const exportPng = useCallback(
    async (svg: SVGSVGElement) => {
      if (!pngActive.current) return;
      pngActive.current = false;
      const run = pngRun.current;
      const current = () => pngRun.current === run && pngRunningNow.current;
      try {
        if (!pngViewport || !pngSize) throw new Error('png-export: nothing to draw');
        const svgText = serializePlanSvg(svg, {
          widthPx: pngViewport.widthPx,
          heightPx: pngViewport.heightPx,
          factor: pngSize.factor,
        });
        const today = new Date();
        const blob = await rasterizeSvg(svgText, {
          widthPx: pngSize.widthPx,
          heightPx: pngSize.heightPx,
          factor: pngSize.factor,
          // Fixed, not the page theme: the PNG is white like the preview and the server's exports.
          background: lightTheme.palette.common.white,
          watermark: png.watermark
            ? t(`${PREFIX}.png.watermarkText`, {
                date: new Intl.DateTimeFormat(language, { dateStyle: 'medium' }).format(today),
              })
            : null,
          watermarkColor: lightTheme.palette.text.secondary,
        });
        // The run was ended while the image was drawn (its plan went away): no file, the dialog already says why.
        if (!current()) return;
        saveBlob(blob, planPngFilename(siteKey, today));
        onClose();
      } catch {
        if (current()) setFailure('pngFailed');
      } finally {
        if (current()) {
          setPngRunning(false);
          setBusy(false);
        }
      }
    },
    [pngViewport, pngSize, png.watermark, t, language, siteKey, onClose],
  );
  const pngDrawingFailed = useCallback(() => {
    if (!pngActive.current) return;
    pngActive.current = false;
    setFailure('pngFailed');
    setPngRunning(false);
    setBusy(false);
  }, []);

  const download = async () => {
    setBusy(true);
    setFailure(null);
    if (pngMode) {
      pngActive.current = true;
      pngRun.current += 1;
      setPngRunning(true);
      return;
    }
    try {
      const file = csvMode
        ? await fetchBedListCsv(siteKey, csv)
        : await fetchPlanExport(siteKey, effective);
      saveBlob(file.blob, file.filename);
      onClose();
    } catch (error) {
      const reason = await describeExportFailure(error);
      setFailure(errorKey(reason.code, reason.status));
    } finally {
      setBusy(false);
    }
  };

  const shownError =
    failure ??
    (!localMode && preview.status === 'error' ? errorKey(preview.code, preview.httpStatus) : null);
  const scaled = !localMode && effective.format !== 'json';
  // The parcel list and its assignment opt-in belong to the PDF only; a phone keeps the standard options (GP-UX-050).
  const parcelList = scaled && effective.format === 'pdf' && effective.parcelList === true;
  const parcelAssignment = parcelList && effective.includeAssignment === true;
  const shownFormat: DialogFormat = csvMode ? 'csv' : pngMode ? 'png' : effective.format;
  let downloadBlocked: boolean;
  if (csvMode) downloadBlocked = csv.columns.length === 0;
  else if (pngMode) downloadBlocked = pngSize === null;
  else downloadBlocked = preview.status === 'error' && preview.code === 'plan.empty';
  const number = new Intl.NumberFormat(i18n.language, { maximumFractionDigits: 2 });
  const columnBox = (column: BedListColumn) => (
    <FormControlLabel
      key={column}
      control={
        <Checkbox
          checked={csv.columns.includes(column)}
          onChange={() => toggleColumn(column)}
          slotProps={{ input: { 'data-testid': `plan-export-csv-column-${column}` } as object }}
        />
      }
      label={t(`${PREFIX}.csv.columns.${column}`)}
      sx={{ minHeight: 44 }}
    />
  );

  return (
    <Dialog
      open={open}
      onClose={busy ? undefined : onClose}
      fullScreen={phone}
      maxWidth="md"
      fullWidth
      aria-labelledby="plan-export-title"
      data-testid="plan-export-dialog"
    >
      <DialogTitle id="plan-export-title">{t(`${PREFIX}.title`)}</DialogTitle>
      <DialogContent sx={{ display: 'flex', flexDirection: 'column', gap: 2, pt: 1 }}>
        <FormControl>
          <FormLabel id="plan-export-format-label">{t(`${PREFIX}.format`)}</FormLabel>
          <ToggleButtonGroup
            exclusive
            fullWidth
            value={shownFormat}
            onChange={(_, value: DialogFormat | null) => value && chooseFormat(value)}
            aria-labelledby="plan-export-format-label"
            sx={{ mt: 0.5 }}
          >
            <ToggleButton value="pdf" sx={{ minHeight: 48 }} data-testid="plan-export-format-pdf">
              {t(`${PREFIX}.formats.pdf`)}
            </ToggleButton>
            {!phone && (
              <ToggleButton value="svg" sx={{ minHeight: 48 }} data-testid="plan-export-format-svg">
                {t(`${PREFIX}.formats.svg`)}
              </ToggleButton>
            )}
            <ToggleButton value="json" sx={{ minHeight: 48 }} data-testid="plan-export-format-json">
              {t(`${PREFIX}.formats.json`)}
            </ToggleButton>
            {!phone && (
              <ToggleButton value="png" sx={{ minHeight: 48 }} data-testid="plan-export-format-png">
                {t(`${PREFIX}.formats.png`)}
              </ToggleButton>
            )}
            {!phone && (
              <ToggleButton value="csv" sx={{ minHeight: 48 }} data-testid="plan-export-format-csv">
                {t(`${PREFIX}.formats.csv`)}
              </ToggleButton>
            )}
          </ToggleButtonGroup>
          <Typography variant="body2" color="text.secondary" sx={{ mt: 0.5 }}>
            {t(`${PREFIX}.formatHints.${shownFormat}`)}
          </Typography>
        </FormControl>

        {csvMode && (
          <>
            <FormControl component="fieldset" variant="standard">
              <FormLabel component="legend">{t(`${PREFIX}.csv.defaultColumns`)}</FormLabel>
              <FormGroup
                sx={{ display: 'grid', gridTemplateColumns: { xs: '1fr', sm: 'repeat(2, 1fr)' } }}
              >
                {BED_LIST_DEFAULT_COLUMNS.map(columnBox)}
              </FormGroup>
            </FormControl>
            <FormControl component="fieldset" variant="standard">
              <FormLabel component="legend">{t(`${PREFIX}.csv.siteConditionColumns`)}</FormLabel>
              <FormGroup
                sx={{ display: 'grid', gridTemplateColumns: { xs: '1fr', sm: 'repeat(2, 1fr)' } }}
              >
                {BED_LIST_SITE_CONDITION_COLUMNS.map(columnBox)}
              </FormGroup>
            </FormControl>
            {csv.columns.length === 0 && (
              <Alert severity="info" data-testid="plan-export-csv-no-columns">
                {t(`${PREFIX}.csv.noColumns`)}
              </Alert>
            )}
            <FormControl component="fieldset" variant="standard">
              <FormControlLabel
                control={
                  <Switch
                    checked={csv.excel}
                    onChange={(event) => patchCsv({ excel: event.target.checked })}
                    slotProps={{ input: { 'data-testid': 'plan-export-csv-excel' } as object }}
                  />
                }
                label={t(`${PREFIX}.csv.excel`)}
                sx={{ minHeight: 44 }}
              />
              <Typography variant="body2" color="text.secondary">
                {t(`${PREFIX}.csv.excelHint`)}
              </Typography>
            </FormControl>
            <FormControl component="fieldset" variant="standard">
              <FormControlLabel
                control={
                  <Switch
                    checked={csv.includeAssignment}
                    onChange={(event) => patchCsv({ includeAssignment: event.target.checked })}
                    slotProps={{
                      input: {
                        'data-testid': 'plan-export-csv-assignment',
                        'aria-describedby': 'plan-export-csv-assignment-hint',
                      } as object,
                    }}
                  />
                }
                label={t(`${PREFIX}.csv.includeAssignment`)}
                sx={{ minHeight: 44 }}
              />
              <Typography
                id="plan-export-csv-assignment-hint"
                variant="body2"
                color="text.secondary"
                data-testid="plan-export-csv-assignment-hint"
              >
                {t(`${PREFIX}.csv.assignmentHint`)}
              </Typography>
            </FormControl>
          </>
        )}

        {pngMode && (
          <>
            <FormControl>
              <FormLabel id="plan-export-png-resolution-label">{t(`${PREFIX}.png.resolution`)}</FormLabel>
              <ToggleButtonGroup
                exclusive
                value={png.resolution}
                onChange={(_, value: PngResolution | null) => value && patchPng({ resolution: value })}
                aria-labelledby="plan-export-png-resolution-label"
                sx={{ mt: 0.5 }}
              >
                {PNG_RESOLUTIONS.map((factor) => (
                  <ToggleButton
                    key={factor}
                    value={factor}
                    sx={{ minHeight: 48, minWidth: 64 }}
                    data-testid={`plan-export-png-resolution-${factor}`}
                  >
                    {t(`${PREFIX}.png.factor`, { factor })}
                  </ToggleButton>
                ))}
              </ToggleButtonGroup>
              <Typography variant="body2" color="text.secondary" sx={{ mt: 0.5 }}>
                {t(`${PREFIX}.png.resolutionHint`)}
              </Typography>
            </FormControl>
            {pngSize?.capped && (
              <Alert severity="info" data-testid="plan-export-png-capped">
                {t(`${PREFIX}.png.capped`, {
                  requested: png.resolution,
                  factor: number.format(pngSize.factor),
                  megapixels: number.format(Math.round(MAX_CANVAS_AREA_PX / 100_000) / 10),
                })}
              </Alert>
            )}
            <FormControl component="fieldset" variant="standard">
              <FormControlLabel
                control={
                  <Switch
                    checked={png.watermark}
                    onChange={(event) => patchPng({ watermark: event.target.checked })}
                    slotProps={{
                      input: {
                        'data-testid': 'plan-export-png-watermark',
                        'aria-describedby': 'plan-export-png-watermark-hint',
                      } as object,
                    }}
                  />
                }
                label={t(`${PREFIX}.png.watermark`)}
                sx={{ minHeight: 44 }}
              />
              <Typography id="plan-export-png-watermark-hint" variant="body2" color="text.secondary">
                {t(`${PREFIX}.png.watermarkHint`)}
              </Typography>
            </FormControl>
          </>
        )}

        {!localMode && effective.format === 'json' && (
          <FormControl>
            <FormLabel id="plan-export-scope-label">{t(`${PREFIX}.scope`)}</FormLabel>
            <RadioGroup
              aria-labelledby="plan-export-scope-label"
              value={effective.scope}
              onChange={(event) => patch({ scope: event.target.value as ExportScope })}
            >
              {(['site', 'selection', 'subtree'] as const).map((name) => (
                <FormControlLabel
                  key={name}
                  value={name}
                  disabled={!available[name]}
                  control={
                    <Radio
                      slotProps={{
                        input: { 'data-testid': `plan-export-scope-${name}` } as object,
                      }}
                    />
                  }
                  label={t(`${PREFIX}.scopes.${name}`)}
                  sx={{ minHeight: 44 }}
                />
              ))}
            </RadioGroup>
            <Typography variant="body2" color="text.secondary" data-testid="plan-export-scope-hint">
              {t(`${PREFIX}.scopeHints.${effective.scope}`, { n: effective.keys.length })}
              {!available.selection &&
                ` ${t(`${PREFIX}.scopeNeedsSelection`, { max: MAX_EXPORT_KEYS })}`}
            </Typography>
          </FormControl>
        )}

        {scaled && !phone && (
          <Box
            sx={{
              display: 'grid',
              gap: 2,
              gridTemplateColumns: { xs: '1fr', sm: 'repeat(3, 1fr)' },
            }}
          >
            <TextField
              select
              label={t(`${PREFIX}.paper`)}
              value={effective.paper}
              onChange={(event) => patch({ paper: event.target.value as ExportPaper })}
              slotProps={{ htmlInput: { 'data-testid': 'plan-export-paper' } }}
            >
              <MenuItem value="a4">A4</MenuItem>
              <MenuItem value="a3">A3</MenuItem>
            </TextField>
            <TextField
              select
              label={t(`${PREFIX}.orientation`)}
              value={effective.orientation}
              onChange={(event) => patch({ orientation: event.target.value as ExportOrientation })}
              slotProps={{ htmlInput: { 'data-testid': 'plan-export-orientation' } }}
            >
              <MenuItem value="landscape">{t(`${PREFIX}.orientations.landscape`)}</MenuItem>
              <MenuItem value="portrait">{t(`${PREFIX}.orientations.portrait`)}</MenuItem>
            </TextField>
            <TextField
              select
              label={t(`${PREFIX}.scale`)}
              value={effective.scale}
              onChange={(event) => patch({ scale: event.target.value as ExportScale })}
              helperText={
                effective.scale === 'auto' && preview.status === 'svg' && preview.scale
                  ? t(`${PREFIX}.scaleChosen`, { scale: preview.scale })
                  : t(`${PREFIX}.scaleHelp`)
              }
              slotProps={{ htmlInput: { 'data-testid': 'plan-export-scale' } }}
            >
              {EXPORT_SCALES.map((scale) => (
                <MenuItem key={scale} value={scale}>
                  {scale === 'auto' ? t(`${PREFIX}.scaleAuto`) : scale}
                </MenuItem>
              ))}
            </TextField>
          </Box>
        )}

        {scaled && !phone && (
          <FormControl component="fieldset" variant="standard">
            <FormLabel component="legend">{t(`${PREFIX}.layers`)}</FormLabel>
            <FormGroup row>
              {EXPORT_LAYERS.map((layer) => (
                <FormControlLabel
                  key={layer}
                  control={
                    <Checkbox
                      checked={effective.layers.includes(layer)}
                      onChange={() => toggleLayer(layer)}
                      slotProps={{
                        input: { 'data-testid': `plan-export-layer-${layer}` } as object,
                      }}
                    />
                  }
                  label={t(`${PREFIX}.layerNames.${layer}`)}
                  sx={{ minHeight: 44 }}
                />
              ))}
              {effective.format === 'pdf' && (
                <FormControlLabel
                  control={
                    <Checkbox
                      checked={effective.bedList}
                      onChange={(event) => patch({ bedList: event.target.checked })}
                      slotProps={{ input: { 'data-testid': 'plan-export-bed-list' } as object }}
                    />
                  }
                  label={t(`${PREFIX}.bedList`)}
                  sx={{ minHeight: 44 }}
                />
              )}
              {effective.format === 'pdf' && (
                <FormControlLabel
                  control={
                    <Checkbox
                      checked={parcelList}
                      onChange={(event) =>
                        patch(
                          event.target.checked
                            ? { parcelList: true }
                            : { parcelList: false, includeAssignment: false },
                        )
                      }
                      slotProps={{
                        input: {
                          'data-testid': 'plan-export-parcel-list',
                          'aria-describedby': 'plan-export-parcel-list-hint',
                        } as object,
                      }}
                    />
                  }
                  label={t(`${PREFIX}.parcelList.label`)}
                  sx={{ minHeight: 44 }}
                />
              )}
            </FormGroup>
          </FormControl>
        )}

        {scaled && !phone && effective.format === 'pdf' && (
          <Typography
            id="plan-export-parcel-list-hint"
            variant="body2"
            color="text.secondary"
            sx={{ mt: -1 }}
          >
            {t(`${PREFIX}.parcelList.hint`)}
          </Typography>
        )}

        {scaled && !phone && parcelList && (
          <FormControl component="fieldset" variant="standard" sx={{ pl: { xs: 0, sm: 4 } }}>
            <FormControlLabel
              control={
                <Switch
                  checked={parcelAssignment}
                  onChange={(event) => patch({ includeAssignment: event.target.checked })}
                  slotProps={{
                    input: {
                      'data-testid': 'plan-export-parcel-assignment',
                      'aria-describedby': 'plan-export-parcel-assignment-hint',
                    } as object,
                  }}
                />
              }
              label={t(`${PREFIX}.parcelList.includeAssignment`)}
              sx={{ minHeight: 44 }}
            />
            <Typography
              id="plan-export-parcel-assignment-hint"
              variant="body2"
              color="text.secondary"
              data-testid="plan-export-parcel-assignment-hint"
            >
              {t(`${PREFIX}.parcelList.assignmentHint`)}
            </Typography>
          </FormControl>
        )}

        {phone && effective.format !== 'json' && (
          <Typography variant="body2" color="text.secondary" data-testid="plan-export-phone-note">
            {t(`${PREFIX}.phoneNote`)}
          </Typography>
        )}

        <Typography variant="caption" color="text.secondary" data-testid="plan-export-privacy">
          {t(
            csvMode && csv.includeAssignment
              ? `${PREFIX}.csv.privacyWithAssignment`
              : parcelAssignment
                ? `${PREFIX}.parcelList.privacyWithAssignment`
                : `${PREFIX}.privacy`,
          )}
        </Typography>

        {shownError !== null && (
          <Alert severity="warning" data-testid="plan-export-error">
            {t(`${PREFIX}.errors.${shownError}`)}
          </Alert>
        )}
        {!localMode && preview.status === 'svg' && preview.suggestA3 && effective.paper === 'a4' && (
          <Alert severity="info" data-testid="plan-export-suggest-a3">
            {t(`${PREFIX}.suggestA3`)}
          </Alert>
        )}

        <Box
          sx={{ border: 1, borderColor: 'divider', borderRadius: 1, p: 1, minHeight: 160 }}
          data-testid="plan-export-preview"
          role="group"
          aria-label={t(`${PREFIX}.preview`)}
          aria-busy={!localMode && (preview.status === 'loading' || preview.status === 'idle')}
        >
          <Typography variant="subtitle2" component="h3" sx={{ mb: 1 }}>
            {t(`${PREFIX}.preview`)}
          </Typography>
          {csvMode && (
            <Typography variant="body2" data-testid="plan-export-csv-summary">
              {csv.columns.length === 0
                ? t(`${PREFIX}.csv.noColumns`)
                : t(`${PREFIX}.csv.summary`, {
                    columns: orderedBedListColumns(csv.columns)
                      .map((column) => t(`${PREFIX}.csv.columns.${column}`))
                      .concat(csv.includeAssignment ? [t(`${PREFIX}.csv.columns.assigned_to`)] : [])
                      .join(', '),
                  })}
            </Typography>
          )}
          {pngMode && (
            <Typography variant="body2" data-testid="plan-export-png-summary">
              {pngSize
                ? t(`${PREFIX}.png.summary`, { width: pngSize.widthPx, height: pngSize.heightPx })
                : t(`${PREFIX}.png.${plan ? 'nothingToDraw' : 'notLoaded'}`)}
            </Typography>
          )}
          {!localMode && (preview.status === 'loading' || preview.status === 'idle') && (
            <Skeleton
              variant="rectangular"
              height={140}
              role="status"
              aria-label={t(`${PREFIX}.previewLoading`)}
            />
          )}
          {!localMode && preview.status === 'svg' && (
            <Box
              component="img"
              src={preview.url}
              alt={t(`${PREFIX}.previewAlt`, { scale: preview.scale ?? '' })}
              sx={{ width: '100%', maxHeight: 320, objectFit: 'contain', bgcolor: 'common.white' }}
            />
          )}
          {!localMode && preview.status === 'json' && (
            <Typography variant="body2" data-testid="plan-export-json-summary">
              {t(`${PREFIX}.jsonSummary`, {
                locations: preview.summary.locations,
                objects: preview.summary.gardenObjects,
                slots: preview.summary.slots,
                size: formatSize(preview.summary.bytes),
              })}
            </Typography>
          )}
          {!localMode && preview.status === 'error' && (
            <Typography variant="body2" color="text.secondary">
              {t(`${PREFIX}.previewUnavailable`)}
            </Typography>
          )}
        </Box>
      </DialogContent>
      <DialogActions>
        <Button onClick={onClose} disabled={busy} sx={{ minHeight: 44 }}>
          {t('common.cancel')}
        </Button>
        <Button
          variant="contained"
          onClick={download}
          loading={busy}
          disabled={downloadBlocked}
          sx={{ minHeight: 44 }}
          data-testid="plan-export-download"
        >
          {t(`${PREFIX}.download`)}
        </Button>
      </DialogActions>
      {pngRunning && plan && pngViewport && (
        <OffscreenPlanSvg
          plan={plan}
          viewport={pngViewport}
          labels={labels}
          options={pngRenderOptions}
          onReady={exportPng}
          onError={pngDrawingFailed}
        />
      )}
    </Dialog>
  );
}
