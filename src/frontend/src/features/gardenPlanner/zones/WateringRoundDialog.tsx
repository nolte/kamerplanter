import { useMemo, useState, type FormEvent } from 'react';
import { useTranslation } from 'react-i18next';
import Alert from '@mui/material/Alert';
import Button from '@mui/material/Button';
import Dialog from '@mui/material/Dialog';
import DialogActions from '@mui/material/DialogActions';
import DialogContent from '@mui/material/DialogContent';
import DialogTitle from '@mui/material/DialogTitle';
import FormControl from '@mui/material/FormControl';
import FormControlLabel from '@mui/material/FormControlLabel';
import FormHelperText from '@mui/material/FormHelperText';
import FormLabel from '@mui/material/FormLabel';
import Radio from '@mui/material/Radio';
import RadioGroup from '@mui/material/RadioGroup';
import TextField from '@mui/material/TextField';
import Typography from '@mui/material/Typography';
import InfoOutlinedIcon from '@mui/icons-material/InfoOutlined';
import { isApiError } from '@/api/errors';
import type { PlanModel } from '../model/planModel';
import { logZoneWatering } from './zonesApi';
import { ROUND_ALLOCATIONS, type PlanZone, type RoundAllocation, type WateringRoundResult } from './zoneTypes';

const PREFIX = 'pages.gardenPlan.editor.zones';

interface Props {
  open: boolean;
  zone: PlanZone;
  plan: PlanModel;
  onClose: () => void;
  /** The round was written: the caller reads the status and the layer again. */
  onLogged: () => void;
}

/**
 * The watering round of a zone (REQ-053 GP-FR-117, ZG-004): one total, divided `by_area` or `equal` over the beds
 * (`by_demand` follows later, #2466). The dialog says in so many words that the amounts are allocated, not
 * measured, and lists the beds without an area that `by_area` leaves out. "Rain - skipped" is not here: the
 * backend has no route for it yet.
 */
export function WateringRoundDialog({ open, zone, plan, onClose, onLogged }: Props) {
  const { t, i18n } = useTranslation();
  const [volume, setVolume] = useState('');
  const [allocation, setAllocation] = useState<RoundAllocation>('by_area');
  const [summary, setSummary] = useState('');
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<WateringRoundResult | null>(null);

  const bedName = (key: string) => plan.locations[key]?.name ?? key;
  const noAreaBeds = useMemo(
    () => zone.location_keys.filter((key) => !((plan.locations[key]?.area_m2 ?? 0) > 0)),
    [zone.location_keys, plan.locations],
  );
  const liters = new Intl.NumberFormat(i18n.language, { maximumFractionDigits: 2 });
  const parsed = Number(volume.replace(',', '.'));
  const volumeValid = volume.trim() !== '' && Number.isFinite(parsed) && parsed > 0;
  const noBeds = zone.location_keys.length === 0;

  const submit = (event: FormEvent) => {
    event.preventDefault();
    if (!volumeValid || noBeds || busy) return;
    setBusy(true);
    setError(null);
    logZoneWatering(zone.key, {
      volume_liters: parsed,
      allocation,
      summary: summary.trim() === '' ? null : summary.trim(),
    })
      .then((answer) => {
        setResult(answer);
        onLogged();
      })
      .catch((failure: unknown) => {
        const code = isApiError(failure) ? failure.errorCode : '';
        setError(
          code === 'irrigation_zone.no_bed_area'
            ? t(`${PREFIX}.round.noBedArea`)
            : isApiError(failure) && failure.statusCode === 403
              ? t(`${PREFIX}.errors.forbidden`)
              : t(`${PREFIX}.errors.generic`),
        );
      })
      .finally(() => setBusy(false));
  };

  return (
    <Dialog open={open} onClose={busy ? undefined : onClose} fullWidth maxWidth="sm" data-testid="garden-plan-round-dialog">
      <DialogTitle>{t(`${PREFIX}.round.title`, { name: zone.name })}</DialogTitle>
      {result ? (
        <>
          <DialogContent data-testid="garden-plan-round-result">
            <Typography variant="subtitle2" component="h3">
              {t(`${PREFIX}.round.resultTitle`)}
            </Typography>
            <Alert severity="info" icon={<InfoOutlinedIcon />} sx={{ my: 1 }} data-testid="garden-plan-round-result-marker">
              {t(`${PREFIX}.round.resultMarker`, { allocation: t(`enums.careEventAllocation.${result.allocation}`) })}
            </Alert>
            <ul>
              {result.shares.map((share) => (
                <li key={share.location_key}>
                  {t(`${PREFIX}.round.share`, { bed: bedName(share.location_key), liters: liters.format(share.liters) })}
                </li>
              ))}
            </ul>
            {result.skipped_location_keys.length > 0 && (
              <Typography variant="body2" data-testid="garden-plan-round-result-skipped">
                {t(`${PREFIX}.round.skipped`, { beds: result.skipped_location_keys.map(bedName).join(', ') })}
              </Typography>
            )}
          </DialogContent>
          <DialogActions>
            <Button onClick={onClose} sx={{ minHeight: 44 }} data-testid="garden-plan-round-done">
              {t(`${PREFIX}.round.close`)}
            </Button>
          </DialogActions>
        </>
      ) : (
        <form onSubmit={submit} noValidate>
          <DialogContent sx={{ display: 'grid', gap: 2 }}>
            {noBeds && <Alert severity="warning">{t(`${PREFIX}.round.noBeds`)}</Alert>}
            <TextField
              label={t(`${PREFIX}.round.volume`)}
              value={volume}
              onChange={(event) => setVolume(event.target.value)}
              type="text"
              required
              error={volume !== '' && !volumeValid}
              helperText={volume !== '' && !volumeValid ? t(`${PREFIX}.round.invalidVolume`) : undefined}
              slotProps={{ htmlInput: { inputMode: 'decimal', 'data-testid': 'garden-plan-round-volume' } }}
              sx={{ '& .MuiInputBase-root': { minHeight: 48 } }}
            />
            <FormControl>
              <FormLabel id="garden-plan-round-allocation-label">{t(`${PREFIX}.round.allocation`)}</FormLabel>
              <RadioGroup
                aria-labelledby="garden-plan-round-allocation-label"
                value={allocation}
                onChange={(event) => setAllocation(event.target.value as RoundAllocation)}
              >
                {ROUND_ALLOCATIONS.map((option) => (
                  <FormControlLabel
                    key={option}
                    value={option}
                    control={<Radio slotProps={{ input: { 'data-testid': `garden-plan-round-allocation-${option}` } as object }} />}
                    label={t(`${PREFIX}.round.allocationOption.${option}`)}
                    sx={{ minHeight: 44 }}
                  />
                ))}
              </RadioGroup>
              <FormHelperText>{t(`${PREFIX}.round.allocationHelp.${allocation}`)}</FormHelperText>
            </FormControl>
            <Alert severity="info" icon={<InfoOutlinedIcon />} data-testid="garden-plan-round-marker">
              {t(`${PREFIX}.round.marker`)}
            </Alert>
            {allocation === 'by_area' && noAreaBeds.length > 0 && !noBeds && (
              <Typography variant="body2" data-testid="garden-plan-round-no-area">
                {t(`${PREFIX}.round.noAreaBeds`, { beds: noAreaBeds.map(bedName).join(', ') })}
              </Typography>
            )}
            <TextField
              label={t(`${PREFIX}.round.summary`)}
              value={summary}
              onChange={(event) => setSummary(event.target.value)}
              multiline
              minRows={2}
              slotProps={{ htmlInput: { maxLength: 500, 'data-testid': 'garden-plan-round-summary' } }}
            />
            {error && (
              <Alert severity="error" role="alert" data-testid="garden-plan-round-error">
                {error}
              </Alert>
            )}
          </DialogContent>
          <DialogActions>
            <Button onClick={onClose} disabled={busy} sx={{ minHeight: 44 }} data-testid="garden-plan-round-cancel">
              {t(`${PREFIX}.round.cancel`)}
            </Button>
            <Button
              type="submit"
              variant="contained"
              disabled={!volumeValid || noBeds || busy}
              sx={{ minHeight: 44 }}
              data-testid="garden-plan-round-submit"
            >
              {t(`${PREFIX}.round.${busy ? 'submitting' : 'submit'}`)}
            </Button>
          </DialogActions>
        </form>
      )}
    </Dialog>
  );
}
