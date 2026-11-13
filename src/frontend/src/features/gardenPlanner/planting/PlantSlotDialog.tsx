/**
 * The dialog of the plan tool "Pflanze setzen" (REQ-053 GP-UX-071, #2913): ONE plant into ONE free planting spot.
 * The spot is the one clicked on the plan; reached from the properties panel of a bed (the keyboard path) the grower
 * picks one of the bed's free spots here. Species (favourites first, names in the UI language), an optional
 * cultivar, the planting day (today, UTC) and the hints of the bed for that species - crop rotation and neighbours -
 * before anything is written.
 *
 * It creates no planting run and lays nothing out: the bed's planting dialog does that. A single plant has no
 * "Trotzdem pflanzen": when the server refuses the spot for a critical crop-rotation finding or an incompatible
 * neighbour (it predicts that through the slot check), the dialog says so and points to the bed's planting dialog,
 * which can plant anyway with a reason.
 */
import { useEffect, useId, useMemo, useState } from 'react';
import { useTranslation } from 'react-i18next';
import Alert from '@mui/material/Alert';
import Box from '@mui/material/Box';
import Button from '@mui/material/Button';
import CircularProgress from '@mui/material/CircularProgress';
import Dialog from '@mui/material/Dialog';
import DialogActions from '@mui/material/DialogActions';
import DialogContent from '@mui/material/DialogContent';
import DialogTitle from '@mui/material/DialogTitle';
import MenuItem from '@mui/material/MenuItem';
import TextField from '@mui/material/TextField';
import Typography from '@mui/material/Typography';
import useMediaQuery from '@mui/material/useMediaQuery';
import { useTheme } from '@mui/material/styles';
import { listAllSpecies } from '@/api/endpoints/species';
import { validatePlanting as validateSlotPlanting } from '@/api/endpoints/plantInstances';
import type { Species } from '@/api/types';
import { useApiError } from '@/hooks/useApiError';
import { useServerFavorites } from '@/hooks/useServerFavorites';
import { useAppDispatch } from '@/store/hooks';
import { generateInstanceId } from '@/utils/idGenerator';
import { getSpeciesLabel, getSpeciesOptionLabel } from '@/utils/plantDisplay';
import type { SunExposure } from '../model/types';
import { plantIntoSlot, type PlantRefusal } from '../state/plantIntoSlot';
import HintsPanel from './HintsPanel';
import { today } from './plantStateClock';
import { siteFitOf } from './siteFitOf';
import SpeciesPicker from './SpeciesPicker';
import { useBedHints } from './useBedHints';
import { useCultivars } from './useCultivars';

const PREFIX = 'pages.gardenPlan.editor.plantSlot';
const TARGET_PX = 48;
const NO_OP = () => undefined;

export interface PlantSlotOption {
  key: string;
  /** The spot as the grower knows it: its slot id. */
  label: string;
}

export interface PlantedInSlot {
  plantKey: string;
  slotKey: string;
  speciesName: string;
  /** The plan was read again: the spot shows the plant. `false` = it shows once the plan is reloaded. */
  refreshed: boolean;
}

interface PlantSlotDialogProps {
  bedKey: string;
  bedName: string;
  /** The free point slots offered; one = the spot clicked on the plan. */
  slots: readonly PlantSlotOption[];
  /** The spot preselected (the clicked one); `null` = the first of `slots`. */
  initialSlotKey?: string | null;
  /** The sun class of the bed: with the species' light requirement it gives the site-fit hint (GP-FR-160). */
  bedSun?: SunExposure;
  onClose: () => void;
  onPlanted: (result: PlantedInSlot) => void;
  /** Opens the bed's page, where its planting dialog can plant anyway with a reason; absent = not offered. */
  onOpenBed?: () => void;
}

/** The slot check of the server for this spot and species: `null` while it runs or when it could not be read. */
function useSlotVerdict(slotKey: string | null, speciesKey: string | null): { blocked: boolean; checking: boolean } {
  const [verdict, setVerdict] = useState<{ id: string; valid: boolean | null } | null>(null);
  const id = slotKey && speciesKey ? `${slotKey}|${speciesKey}` : null;
  useEffect(() => {
    if (!slotKey || !speciesKey) return undefined;
    let cancelled = false;
    const requestId = `${slotKey}|${speciesKey}`;
    validateSlotPlanting(slotKey, speciesKey)
      .then((answer) => {
        if (!cancelled) setVerdict({ id: requestId, valid: answer.valid });
      })
      .catch(() => {
        // Not readable: the create answers for itself, and a refusal is shown then.
        if (!cancelled) setVerdict({ id: requestId, valid: null });
      });
    return () => {
      cancelled = true;
    };
  }, [slotKey, speciesKey]);
  const current = verdict !== null && verdict.id === id ? verdict : null;
  return useMemo(
    () => ({ blocked: current?.valid === false, checking: id !== null && current === null }),
    [current, id],
  );
}

/** The text of a refusal; the server's own message is English (NFR-003) and never shown. */
function refusalKey(code: PlantRefusal): string {
  return code === 'rotation' || code === 'companion' ? `${PREFIX}.blocked.${code}` : `${PREFIX}.refused.${code}`;
}

export default function PlantSlotDialog({
  bedKey,
  bedName,
  slots,
  initialSlotKey = null,
  bedSun = 'unknown',
  onClose,
  onPlanted,
  onOpenBed,
}: PlantSlotDialogProps) {
  const { t, i18n } = useTranslation();
  const theme = useTheme();
  const fullScreen = useMediaQuery(theme.breakpoints.down('sm'));
  const dispatch = useAppDispatch();
  const { handleError } = useApiError();
  const { favorites } = useServerFavorites('species');
  const titleId = useId();
  const statusId = useId();

  const [catalogue, setCatalogue] = useState<
    { status: 'loading' } | { status: 'ready'; items: Species[] } | { status: 'error' }
  >({ status: 'loading' });
  const [slotKey, setSlotKey] = useState<string | null>(initialSlotKey ?? slots[0]?.key ?? null);
  const [speciesKey, setSpeciesKey] = useState<string | null>(null);
  const [cultivarKey, setCultivarKey] = useState<string | null>(null);
  const [plantedOn, setPlantedOn] = useState(today);
  const [showErrors, setShowErrors] = useState(false);
  const [saving, setSaving] = useState(false);
  const [refusal, setRefusal] = useState<PlantRefusal | null>(null);

  useEffect(() => {
    let cancelled = false;
    listAllSpecies()
      .then((response) => {
        if (!cancelled) setCatalogue({ status: 'ready', items: response.items });
      })
      .catch(() => {
        if (!cancelled) setCatalogue({ status: 'error' });
      });
    return () => {
      cancelled = true;
    };
  }, []);

  const species = useMemo(() => (catalogue.status === 'ready' ? catalogue.items : []), [catalogue]);
  const chosen = useMemo(() => species.find((item) => item.key === speciesKey), [species, speciesKey]);
  const speciesNames = useMemo(
    () => new Map(species.map((item) => [item.key, getSpeciesOptionLabel(item, i18n.language)])),
    [species, i18n.language],
  );
  const cultivars = useCultivars(speciesKey);
  const hintKeys = useMemo(() => [speciesKey], [speciesKey]);
  const hintStates = useBedHints(bedKey, hintKeys);
  const verdict = useSlotVerdict(slotKey, speciesKey);
  const hintSpecies = useMemo(
    () =>
      speciesKey
        ? [
            {
              key: speciesKey,
              name: speciesNames.get(speciesKey) ?? speciesKey,
              state: hintStates[speciesKey],
              siteFit: siteFitOf(chosen, bedSun),
            },
          ]
        : [],
    [speciesKey, speciesNames, hintStates, chosen, bedSun],
  );
  const slotLabel = slots.find((slot) => slot.key === slotKey)?.label ?? '';
  const fixedSlot = slots.length === 1;
  const blocked = verdict.blocked || refusal === 'rotation' || refusal === 'companion';
  const dateMissing = plantedOn.trim() === '';

  const submit = async () => {
    setShowErrors(true);
    if (!speciesKey || !slotKey || dateMissing || blocked) return;
    setSaving(true);
    setRefusal(null);
    // The announcement names the plant as the plant pages do: the common name in the UI language, with the cultivar.
    const cultivar = cultivars.find((item) => item.key === cultivarKey) ?? null;
    const speciesName = getSpeciesLabel(chosen, i18n.language, cultivar) ?? speciesNames.get(speciesKey) ?? speciesKey;
    const outcome = await dispatch(
      plantIntoSlot({
        bedKey,
        slotKey,
        speciesKey,
        cultivarKey,
        plantedOn,
        instanceId: generateInstanceId(chosen?.scientific_name ?? ''),
      }),
    );
    setSaving(false);
    if (outcome.ok) {
      onPlanted({ plantKey: outcome.plantKey, slotKey, speciesName, refreshed: outcome.refreshed });
      return;
    }
    setRefusal(outcome.code);
    // Anything the dialog has no own sentence for goes through the app's error handling as well.
    if (outcome.code === 'failed' && outcome.error !== undefined) handleError(outcome.error);
  };

  const submitReason = verdict.checking ? t(`${PREFIX}.checking`) : null;

  return (
    <Dialog
      open
      onClose={saving ? undefined : onClose}
      fullScreen={fullScreen}
      fullWidth
      maxWidth="sm"
      aria-labelledby={titleId}
      data-testid="garden-plan-plant-dialog"
    >
      <DialogTitle id={titleId}>
        {slotLabel
          ? t(`${PREFIX}.title`, { bed: bedName, slot: slotLabel })
          : t(`${PREFIX}.titleBed`, { bed: bedName })}
      </DialogTitle>
      <DialogContent sx={{ display: 'flex', flexDirection: 'column', gap: 2, pt: '8px !important' }}>
        <Typography variant="body2" color="text.secondary">
          {t(`${PREFIX}.intro`)}
        </Typography>
        {!fixedSlot ? (
          <TextField
            select
            required
            label={t(`${PREFIX}.slot`)}
            value={slotKey ?? ''}
            onChange={(event) => {
              setSlotKey(event.target.value || null);
              setRefusal(null);
            }}
            helperText={t(`${PREFIX}.slotHelp`, { count: slots.length })}
            sx={{ '& .MuiInputBase-root': { minHeight: TARGET_PX } }}
            slotProps={{ htmlInput: { 'data-testid': 'garden-plan-plant-dialog-slot' } }}
          >
            {slots.map((slot) => (
              <MenuItem key={slot.key} value={slot.key} sx={{ minHeight: TARGET_PX }}>
                {slot.label}
              </MenuItem>
            ))}
          </TextField>
        ) : null}
        {catalogue.status === 'error' ? (
          <Alert severity="error" data-testid="garden-plan-plant-dialog-catalogue-error">
            {t(`${PREFIX}.catalogueError`)}
          </Alert>
        ) : catalogue.status === 'loading' ? (
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }} role="status">
            <CircularProgress size={16} />
            <Typography variant="body2">{t(`${PREFIX}.loading`)}</Typography>
          </Box>
        ) : (
          <SpeciesPicker
            species={species}
            value={speciesKey}
            favorites={favorites}
            label={t(`${PREFIX}.species`)}
            error={showErrors && !speciesKey ? t(`${PREFIX}.speciesRequired`) : undefined}
            autoFocus
            testId="garden-plan-plant-dialog-species"
            onChange={(key) => {
              setSpeciesKey(key);
              setCultivarKey(null);
              setRefusal(null);
            }}
          />
        )}
        {cultivars.length > 0 ? (
          <TextField
            select
            label={t(`${PREFIX}.cultivar`)}
            value={cultivarKey ?? ''}
            onChange={(event) => setCultivarKey(event.target.value || null)}
            sx={{ '& .MuiInputBase-root': { minHeight: TARGET_PX } }}
            slotProps={{ htmlInput: { 'data-testid': 'garden-plan-plant-dialog-cultivar' } }}
          >
            <MenuItem value="" sx={{ minHeight: TARGET_PX }}>
              {t(`${PREFIX}.noCultivar`)}
            </MenuItem>
            {cultivars.map((cultivar) => (
              <MenuItem key={cultivar.key} value={cultivar.key} sx={{ minHeight: TARGET_PX }}>
                {cultivar.name}
              </MenuItem>
            ))}
          </TextField>
        ) : null}
        <TextField
          type="date"
          required
          label={t(`${PREFIX}.plantedOn`)}
          value={plantedOn}
          onChange={(event) => setPlantedOn(event.target.value)}
          error={showErrors && dateMissing}
          helperText={showErrors && dateMissing ? t(`${PREFIX}.plantedOnRequired`) : undefined}
          slotProps={{ inputLabel: { shrink: true }, htmlInput: { 'data-testid': 'garden-plan-plant-dialog-date' } }}
          sx={{ '& .MuiInputBase-root': { minHeight: TARGET_PX } }}
        />
        {speciesKey ? (
          <HintsPanel
            species={hintSpecies}
            bedSun={bedSun}
            speciesNames={speciesNames}
            mix={[]}
            severity="OK"
            overridable={false}
            overrideChecked={false}
            overrideReason=""
            showReasonError={false}
            onOverrideChecked={NO_OP}
            onOverrideReason={NO_OP}
          />
        ) : null}
        {blocked ? (
          <Alert
            severity="error"
            data-testid="garden-plan-plant-dialog-blocked"
            action={
              onOpenBed ? (
                <Button
                  color="inherit"
                  size="small"
                  onClick={onOpenBed}
                  sx={{ minHeight: TARGET_PX }}
                  data-testid="garden-plan-plant-dialog-open-bed"
                >
                  {t(`${PREFIX}.openBed`)}
                </Button>
              ) : undefined
            }
          >
            {t(
              refusal === 'rotation' || refusal === 'companion'
                ? refusalKey(refusal)
                : `${PREFIX}.blocked.check`,
            )}
          </Alert>
        ) : null}
        {refusal !== null && refusal !== 'rotation' && refusal !== 'companion' ? (
          <Alert severity="error" role="alert" data-testid="garden-plan-plant-dialog-error">
            {t(refusalKey(refusal))}
          </Alert>
        ) : null}
      </DialogContent>
      <DialogActions sx={{ px: { xs: 2, sm: 3 }, py: 1.5, flexWrap: 'wrap', rowGap: 1 }}>
        {submitReason ? (
          <Typography
            id={statusId}
            variant="body2"
            color="text.secondary"
            role="status"
            sx={{ flex: '1 1 100%' }}
          >
            {submitReason}
          </Typography>
        ) : null}
        <Button onClick={onClose} disabled={saving} sx={{ minHeight: TARGET_PX }} data-testid="garden-plan-plant-dialog-cancel">
          {t('common.cancel')}
        </Button>
        <Button
          variant="contained"
          onClick={() => void submit()}
          disabled={saving || catalogue.status !== 'ready' || blocked || verdict.checking}
          aria-describedby={submitReason ? statusId : undefined}
          sx={{ minHeight: TARGET_PX }}
          data-testid="garden-plan-plant-dialog-submit"
        >
          {t(`${PREFIX}.submit`)}
        </Button>
      </DialogActions>
    </Dialog>
  );
}
