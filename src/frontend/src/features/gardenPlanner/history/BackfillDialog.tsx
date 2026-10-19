/**
 * "What stood here in {year}?" (REQ-053 GP-FR-131): a grower fills in a year the app never saw, so
 * the crop-rotation check has a history. A year takes a plant family (or a species, which names its
 * family), an optional season and a role - main crop, green manure or a fallow year. The server
 * stamps the care event; the author can take it back from the timeline.
 */
import { useEffect, useMemo, useState } from 'react';
import { useTranslation } from 'react-i18next';
import Autocomplete from '@mui/material/Autocomplete';
import Button from '@mui/material/Button';
import Dialog from '@mui/material/Dialog';
import DialogActions from '@mui/material/DialogActions';
import DialogContent from '@mui/material/DialogContent';
import DialogContentText from '@mui/material/DialogContentText';
import DialogTitle from '@mui/material/DialogTitle';
import MenuItem from '@mui/material/MenuItem';
import Stack from '@mui/material/Stack';
import TextField from '@mui/material/TextField';
import useMediaQuery from '@mui/material/useMediaQuery';
import { useTheme } from '@mui/material/styles';
import { listAllBotanicalFamilies } from '@/api/endpoints/botanicalFamilies';
import { listAllSpecies } from '@/api/endpoints/species';
import type { BotanicalFamily, Species } from '@/api/types';
import { useApiError } from '@/hooks/useApiError';
import { backfillYear } from './historyApi';
import {
  backfillErrors,
  backfillYears,
  buildBackfillBody,
  emptyBackfillForm,
  type BackfillForm,
} from './backfillForm';
import type { BackfillResult, PlanRole, Season } from './historyTypes';

const SEASONS: readonly Season[] = ['spring', 'main', 'autumn'];
const ROLES: readonly PlanRole[] = ['main_crop', 'green_manure', 'fallow'];
const TOUCH = { '& .MuiInputBase-root': { minHeight: 48 } };

interface BackfillDialogProps {
  bedKey: string;
  /** The year to start with. */
  initialYear: number;
  onClose: () => void;
  onSaved: (result: BackfillResult) => void;
}

function speciesLabel(species: Species): string {
  const common = species.common_names?.[0];
  return common ? `${common} (${species.scientific_name})` : species.scientific_name;
}

export default function BackfillDialog({ bedKey, initialYear, onClose, onSaved }: BackfillDialogProps) {
  const { t } = useTranslation();
  const theme = useTheme();
  const fullScreen = useMediaQuery(theme.breakpoints.down('sm'));
  const { handleError } = useApiError();
  const now = useMemo(() => new Date(), []);
  const years = useMemo(() => backfillYears(now), [now]);
  const [form, setForm] = useState<BackfillForm>(() => emptyBackfillForm(initialYear));
  const [families, setFamilies] = useState<BotanicalFamily[]>([]);
  const [species, setSpecies] = useState<Species[]>([]);
  const [showErrors, setShowErrors] = useState(false);
  const [saving, setSaving] = useState(false);
  const fallow = form.planRole === 'fallow';
  const errors = showErrors ? backfillErrors(form, now) : {};
  const chosenSpecies = species.find((entry) => entry.key === form.speciesKey) ?? null;

  useEffect(() => {
    let cancelled = false;
    // The catalogues only narrow the choice; a failed request leaves the dialog unusable for a family
    // pick but is reported once, not per field.
    Promise.all([listAllBotanicalFamilies(), listAllSpecies()])
      .then(([familyList, speciesList]) => {
        if (cancelled) return;
        setFamilies([...familyList].sort((a, b) => a.name.localeCompare(b.name)));
        setSpecies(speciesList.items);
      })
      .catch((error: unknown) => {
        if (!cancelled) handleError(error);
      });
    return () => {
      cancelled = true;
    };
  }, [handleError]);

  const patch = (change: Partial<BackfillForm>) => setForm((current) => ({ ...current, ...change }));

  const submit = async () => {
    if (Object.keys(backfillErrors(form, new Date())).length > 0) {
      setShowErrors(true);
      return;
    }
    setSaving(true);
    try {
      const result = await backfillYear(bedKey, buildBackfillBody(form, chosenSpecies?.family_key ?? null));
      onSaved(result);
    } catch (error) {
      handleError(error);
    } finally {
      setSaving(false);
    }
  };

  return (
    <Dialog
      open
      onClose={saving ? undefined : onClose}
      fullScreen={fullScreen}
      fullWidth
      maxWidth="sm"
      aria-labelledby="backfill-title"
      data-testid="backfill-dialog"
    >
      <DialogTitle id="backfill-title">{t('pages.bed.history.backfill.title', { year: form.year })}</DialogTitle>
      <DialogContent>
        <DialogContentText sx={{ mb: 2 }}>{t('pages.bed.history.backfill.description')}</DialogContentText>
        <Stack spacing={2} sx={{ pt: 1 }}>
          <TextField
            select
            label={t('pages.bed.history.backfill.year')}
            value={form.year}
            onChange={(event) => patch({ year: Number(event.target.value) })}
            sx={TOUCH}
            slotProps={{ htmlInput: { 'data-testid': 'backfill-year' } }}
          >
            {years.map((year) => (
              <MenuItem key={year} value={year}>
                {year}
              </MenuItem>
            ))}
          </TextField>

          <TextField
            select
            label={t('pages.bed.history.backfill.role')}
            value={form.planRole}
            onChange={(event) => patch({ planRole: event.target.value as PlanRole })}
            helperText={t(`pages.bed.history.backfill.roleHints.${form.planRole}`)}
            sx={TOUCH}
            slotProps={{ htmlInput: { 'data-testid': 'backfill-role' } }}
          >
            {ROLES.map((role) => (
              <MenuItem key={role} value={role}>
                {t(`pages.bed.history.backfill.roles.${role}`)}
              </MenuItem>
            ))}
          </TextField>

          {!fallow && (
            <>
              <Autocomplete
                options={species}
                value={chosenSpecies}
                getOptionLabel={speciesLabel}
                isOptionEqualToValue={(option, value) => option.key === value.key}
                onChange={(_event, value) =>
                  patch({ speciesKey: value?.key ?? '', familyKey: value ? '' : form.familyKey })
                }
                renderInput={(params) => (
                  <TextField
                    {...params}
                    label={t('pages.bed.history.backfill.species')}
                    helperText={t('pages.bed.history.backfill.speciesHint')}
                    sx={TOUCH}
                  />
                )}
                data-testid="backfill-species"
              />
              <TextField
                select
                label={t('pages.bed.history.backfill.family')}
                value={chosenSpecies ? (chosenSpecies.family_key ?? '') : form.familyKey}
                onChange={(event) => patch({ familyKey: event.target.value })}
                disabled={chosenSpecies !== null && chosenSpecies.family_key !== null}
                required
                error={Boolean(errors.family)}
                helperText={
                  errors.family
                    ? t('pages.bed.history.backfill.errors.family')
                    : chosenSpecies && chosenSpecies.family_key
                      ? t('pages.bed.history.backfill.familyFromSpecies')
                      : undefined
                }
                sx={TOUCH}
                slotProps={{ htmlInput: { 'data-testid': 'backfill-family' } }}
              >
                <MenuItem value="">{t('pages.bed.history.backfill.noFamily')}</MenuItem>
                {families.map((family) => (
                  <MenuItem key={family.key} value={family.key}>
                    {family.name}
                  </MenuItem>
                ))}
              </TextField>
            </>
          )}

          <TextField
            select
            label={t('pages.bed.history.backfill.season')}
            value={form.season}
            onChange={(event) => patch({ season: event.target.value as Season | '' })}
            helperText={t('pages.bed.history.backfill.seasonHint')}
            sx={TOUCH}
            slotProps={{ htmlInput: { 'data-testid': 'backfill-season' } }}
          >
            <MenuItem value="">{t('pages.bed.history.backfill.seasonNone')}</MenuItem>
            {SEASONS.map((season) => (
              <MenuItem key={season} value={season}>
                {t(`pages.bed.history.timeline.seasons.${season}`)}
              </MenuItem>
            ))}
          </TextField>
        </Stack>
      </DialogContent>
      <DialogActions sx={{ px: 3, pb: 2 }}>
        <Button onClick={onClose} disabled={saving} sx={{ minHeight: 48 }}>
          {t('common.cancel')}
        </Button>
        <Button
          variant="contained"
          onClick={() => void submit()}
          disabled={saving}
          sx={{ minHeight: 48 }}
          data-testid="backfill-submit"
        >
          {t('pages.bed.history.backfill.submit')}
        </Button>
      </DialogActions>
    </Dialog>
  );
}
