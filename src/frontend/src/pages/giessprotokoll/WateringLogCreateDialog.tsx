import { useState, useEffect, useMemo } from 'react';
import { useTranslation } from 'react-i18next';
import Dialog from '@mui/material/Dialog';
import useMediaQuery from '@mui/material/useMediaQuery';
import { useTheme } from '@mui/material/styles';
import DialogTitle from '@mui/material/DialogTitle';
import DialogContent from '@mui/material/DialogContent';
import Box from '@mui/material/Box';
import Button from '@mui/material/Button';
import Divider from '@mui/material/Divider';
import IconButton from '@mui/material/IconButton';
import Typography from '@mui/material/Typography';
import Tooltip from '@mui/material/Tooltip';
import Alert from '@mui/material/Alert';
import Autocomplete from '@mui/material/Autocomplete';
import TextField from '@mui/material/TextField';
import Chip from '@mui/material/Chip';
import DeleteIcon from '@mui/icons-material/Delete';
import AddIcon from '@mui/icons-material/Add';
import { useForm, useFieldArray, Controller } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import Form from '@/components/form/Form';
import FormTextField from '@/components/form/FormTextField';
import FormSelectField from '@/components/form/FormSelectField';
import FormNumberField from '@/components/form/FormNumberField';
import FormSwitchField from '@/components/form/FormSwitchField';
import FormActions from '@/components/form/FormActions';
import { useNotification } from '@/hooks/useNotification';
import { useApiError } from '@/hooks/useApiError';
import { getFieldViolations } from '@/api/errors';
import * as wateringLogApi from '@/api/endpoints/watering-logs';
import * as plantApi from '@/api/endpoints/plantInstances';
import * as fertApi from '@/api/endpoints/fertilizers';
import type { PlantInstance, Fertilizer } from '@/api/types';
import { getPlantLabel } from '@/utils/plantDisplay';

const applicationMethods = ['fertigation', 'drench', 'foliar', 'top_dress'] as const;
const waterSources = ['tank', 'tap', 'osmose', 'rainwater', 'distilled', 'well'] as const;

const fertilizerLineSchema = z.object({
  fertilizer_key: z.string().min(1),
  ml_per_liter: z.number().gt(0),
});

/**
 * Client-side shape of the create form.
 *
 * ## Why the cross-field rule is *not* restated here
 *
 * The domain requires at least one of `slot_keys` / `plant_keys` (see
 * `find_watering_log_violations` in the backend, which is the single statement
 * of the watering log's cross-field rules). `plant_keys` and `slot_keys_input`
 * below therefore accept "empty" on purpose. The rule is enforced at the API
 * boundary, which answers 422 naming both fields, and `onSubmit` anchors that
 * answer on the two inputs — so the user still gets a field-level message,
 * just one round trip later.
 *
 * The alternative — a `superRefine` copy of the predicate here — was weighed
 * and rejected (#970):
 *
 * 1. **Nothing can compare the two copies.** The backend's own guard against
 *    this class works because both sides are Python and call the same function
 *    (`TestRequestSchemaAndDomainModelAgree` pins request schema against domain
 *    model from outside). A TypeScript copy is out of that reach; the drift
 *    would be found by a user, not by CI.
 * 2. **The two drift directions fail differently, and only one is bearable.**
 *    A stale copy here that is *stricter* than the domain blocks a submission
 *    the server would have accepted: the user cannot do a legal thing and has
 *    no way around it. Rendering the server's answer instead can only be
 *    *behind* the domain — an unknown rule falls back to the generic
 *    validation toast with the dialog left open. Degraded and visible beats
 *    wrong and blocking.
 * 3. **A message is not a predicate.** The client must hold a German message
 *    either way, because the backend's `reason` is English. Keyed on the
 *    violation `code` (which the backend promises to keep stable), an
 *    out-of-date message is wrong *text*; an out-of-date predicate is a wrong
 *    *decision*.
 *
 * Single-field constraints such as `volume_liters > 0` are a different case and
 * are mirrored: they are also expressed on the input element itself (`min`), the
 * user is entitled to see them before submitting, and being stricter than the
 * server about a numeric range cannot lock anyone out of a valid state.
 *
 * TC-004-114 pins the whole chain end to end — domain rule → violation code and
 * fields → 422 envelope → field mapping → i18n key → rendered helper text — so
 * a change on the domain side that this dialog cannot render goes red instead
 * of quietly degrading to the toast.
 */
const schema = z.object({
  plant_keys: z.array(z.string()).min(0),
  slot_keys_input: z.string(),
  application_method: z.enum(applicationMethods),
  is_supplemental: z.boolean(),
  volume_liters: z.number().gt(0),
  water_source: z.string().nullable(),
  ec_before: z.number().min(0).nullable(),
  ec_after: z.number().min(0).nullable(),
  ph_before: z.number().min(0).max(14).nullable(),
  ph_after: z.number().min(0).max(14).nullable(),
  runoff_ec: z.number().min(0).nullable(),
  runoff_ph: z.number().min(0).max(14).nullable(),
  runoff_volume_liters: z.number().min(0).nullable(),
  performed_by: z.string().nullable(),
  fertilizers_used: z.array(fertilizerLineSchema),
  notes: z.string().nullable(),
});

type FormData = z.infer<typeof schema>;

/**
 * Request-body field (as the 422 envelope names it) → the form field that shows
 * its message.
 *
 * Only fields that actually *render* an error belong here: every entry maps to a
 * `Form*Field` (or, for `plant_keys`, the wrapper below) whose helper text
 * carries `error.message`. An entry pointing at a field with no error surface
 * would consume the violation and display nothing — the silent-swallow the 422
 * handling exists to remove.
 *
 * The one name that differs is `slot_keys`: the form edits it as a single
 * comma-separated string (`slot_keys_input`) and splits it on submit, so the
 * request field and the form field genuinely are two different things.
 */
const SERVER_FIELD_TO_FORM_FIELD: Record<string, keyof FormData> = {
  plant_keys: 'plant_keys',
  slot_keys: 'slot_keys_input',
  volume_liters: 'volume_liters',
  application_method: 'application_method',
  is_supplemental: 'is_supplemental',
};

/**
 * Violation `code` (stable, from `find_watering_log_violations`) → i18n key.
 *
 * Keyed on `code` rather than on the field, because one field can break several
 * rules and each needs its own wording; and translated here rather than taken
 * from the envelope, because the backend's `reason` is English.
 *
 * A code with no entry is deliberately *not* rendered on the field: showing the
 * English reason in a German form is worse than the generic validation toast
 * `handleError` raises anyway, and this is the fallback that keeps a new
 * backend rule from breaking the dialog.
 */
const VIOLATION_MESSAGE_KEYS: Record<string, string> = {
  watering_target_required: 'pages.wateringLogs.errors.targetRequired',
  supplemental_cannot_fertigate: 'pages.wateringLogs.errors.supplementalCannotFertigate',
};

export interface ChannelPreset {
  channelId: string;
  channelLabel: string;
  nutrientPlanKey: string;
  applicationMethod: typeof applicationMethods[number];
  targetEcMs: number | null;
  targetPh: number | null;
  fertilizers: Array<{ fertilizer_key: string; ml_per_liter: number }>;
  volumeLiters: number | null;
}

interface Props {
  open: boolean;
  onClose: () => void;
  onCreated: () => void;
  plantKeys?: string[];
  slotKeys?: string[];
  channelPreset?: ChannelPreset;
  /** Pre-loaded fertilizers — skips internal fetch when provided */
  availableFertilizers?: Fertilizer[];
}

export default function WateringLogCreateDialog({
  open,
  onClose,
  onCreated,
  plantKeys: initialPlantKeys,
  slotKeys,
  channelPreset,
  availableFertilizers,
}: Props) {
  const theme = useTheme();
  const fullScreen = useMediaQuery(theme.breakpoints.down('sm'));
  const { t } = useTranslation();
  const notification = useNotification();
  const { handleError } = useApiError();
  const [saving, setSaving] = useState(false);

  // Options for plant and fertilizer selection
  const [plantOptions, setPlantOptions] = useState<PlantInstance[]>([]);
  const [fertilizerOptions, setFertilizerOptions] = useState<Fertilizer[]>([]);

  useEffect(() => {
    if (!open) return;
    let cancelled = false;
    async function loadOptions() {
      const [plants, fertilizers] = await Promise.all([
        plantApi.listAllPlantInstances().catch(() => []),
        availableFertilizers
          ? Promise.resolve(availableFertilizers)
          : fertApi.fetchAllFertilizers().catch(() => []),
      ]);
      if (cancelled) return;
      setPlantOptions(plants);
      setFertilizerOptions(fertilizers);
    }
    loadOptions();
    return () => { cancelled = true; };
  }, [open, availableFertilizers]);

  const buildDefaults = (): FormData => ({
    plant_keys: initialPlantKeys ?? [],
    slot_keys_input: slotKeys?.join(', ') ?? '',
    application_method: channelPreset?.applicationMethod ?? 'drench',
    is_supplemental: false,
    volume_liters: channelPreset?.volumeLiters ?? 1,
    water_source: null,
    ec_before: null,
    ec_after: null,
    ph_before: channelPreset?.targetPh ?? null,
    ph_after: null,
    runoff_ec: null,
    runoff_ph: null,
    runoff_volume_liters: null,
    performed_by: null,
    fertilizers_used: channelPreset?.fertilizers ?? [],
    notes: null,
  });

  const { control, handleSubmit, reset, setError } = useForm<FormData>({
    resolver: zodResolver(schema),
    defaultValues: buildDefaults(),
  });

  // Reset form when dialog opens or preset/options change
  useEffect(() => {
    if (!open) return;
    reset(buildDefaults());
  }, [open, channelPreset, fertilizerOptions]); // eslint-disable-line react-hooks/exhaustive-deps

  const { fields, append, remove } = useFieldArray({
    control,
    name: 'fertilizers_used',
  });

  const fertilizerSelectOptions = useMemo(
    () => fertilizerOptions.map((f) => ({
      value: f.key,
      label: f.product_name,
    })),
    [fertilizerOptions],
  );

  /**
   * Put the API's field-scoped 422 detail onto the inputs it is about.
   *
   * Without this the dialog answered a rejected cross-field rule with nothing
   * but "Bitte überprüfen Sie Ihre Eingaben." — a toast that names no field, on
   * a form of twenty inputs (#970). The information to do better was in the
   * response all along; `handleError` only maps it when a setter is handed in,
   * and translating by `code` needs the `code`, which the setter contract does
   * not carry.
   *
   * Violations whose field or code this dialog cannot render are skipped by
   * design, so the generic toast remains the floor rather than the ceiling.
   */
  const applyServerFieldErrors = (error: unknown) => {
    for (const violation of getFieldViolations(error)) {
      const formField = SERVER_FIELD_TO_FORM_FIELD[violation.field];
      const messageKey = VIOLATION_MESSAGE_KEYS[violation.code];
      if (!formField || !messageKey) continue;
      setError(formField, { type: violation.code, message: t(messageKey) });
    }
  };

  const onSubmit = async (data: FormData) => {
    try {
      setSaving(true);
      const slotKeysArray = data.slot_keys_input
        .split(',')
        .map((s) => s.trim())
        .filter(Boolean);
      await wateringLogApi.createWateringLog({
        plant_keys: data.plant_keys.length > 0 ? data.plant_keys : undefined,
        slot_keys: slotKeysArray.length > 0 ? slotKeysArray : undefined,
        application_method: data.application_method,
        is_supplemental: data.is_supplemental,
        volume_liters: data.volume_liters,
        water_source: data.water_source as typeof waterSources[number] | null,
        nutrient_plan_key: channelPreset?.nutrientPlanKey ?? undefined,
        channel_id: channelPreset?.channelId ?? undefined,
        ec_before: data.ec_before,
        ec_after: data.ec_after,
        ph_before: data.ph_before,
        ph_after: data.ph_after,
        runoff_ec: data.runoff_ec,
        runoff_ph: data.runoff_ph,
        runoff_volume_liters: data.runoff_volume_liters,
        performed_by: data.performed_by,
        fertilizers_used: data.fertilizers_used,
        notes: data.notes,
      });
      notification.success(t('pages.wateringLogs.logged'));
      reset();
      onCreated();
    } catch (err) {
      applyServerFieldErrors(err);
      handleError(err);
    } finally {
      setSaving(false);
    }
  };

  return (
    <Dialog
      open={open}
      onClose={onClose}
      maxWidth="sm"
      fullWidth
      fullScreen={fullScreen}
      data-testid="watering-log-create-dialog"
      aria-labelledby="watering-log-create-dialog-title">
      <DialogTitle sx={{ position: 'sticky', top: 0, bgcolor: 'background.paper', zIndex: 1, borderBottom: 1, borderColor: 'divider' }} id="watering-log-create-dialog-title">
        {t('pages.wateringLogs.create')}
      </DialogTitle>
      <DialogContent sx={{ overflowY: 'auto' }}>
        {channelPreset && (
          <Alert severity="info" sx={{ mb: 2 }}>
            {t('pages.wateringLogs.channelPresetInfo', { channel: channelPreset.channelLabel })}
            {channelPreset.targetEcMs != null && ` — EC: ${channelPreset.targetEcMs} mS`}
            {channelPreset.targetPh != null && ` — pH: ${channelPreset.targetPh}`}
          </Alert>
        )}
        <Form onSubmit={handleSubmit(onSubmit)}>
          {/* Section: Basics */}
          <Typography variant="subtitle2" color="text.secondary" sx={{ mb: 1, mt: 0.5 }}>
            {t('pages.wateringLogs.sectionBasics')}
          </Typography>

          {/* Plant selection (multi-select autocomplete) */}
          <Controller
            name="plant_keys"
            control={control}
            render={({ field, fieldState: { error } }) => (
              // Wrapped rather than tagged: this field is an `Autocomplete`, not
              // a `Form*Field`, so nothing emitted the `form-field-<name>` hook
              // every other input in this form carries — and the inner
              // `TextField` already owns `plant-keys-input`, which the E2E page
              // object types into. The wrapper adds the missing hook without
              // taking that one away, and the helper text renders inside it.
              <Box data-testid="form-field-plant_keys">
                <Autocomplete
                  multiple
                  options={plantOptions}
                  getOptionLabel={(option) => getPlantLabel(option)}
                  value={plantOptions.filter((p) => field.value.includes(p.key))}
                  onChange={(_, newValue) => {
                    field.onChange(newValue.map((p) => p.key));
                  }}
                  renderInput={(params) => (
                    <TextField
                      {...params}
                      label={t('pages.wateringLogs.plants')}
                      margin="dense"
                      fullWidth
                      autoFocus
                      // The server's cross-field verdict lands here (see
                      // `applyServerFieldErrors`); the schema itself never marks
                      // this field, so without the wiring the message had no way
                      // onto the input at all.
                      error={!!error}
                      helperText={error?.message}
                      data-testid="plant-keys-input"
                      sx={{ mb: 2 }}
                    />
                  )}
                  renderValue={(value, getItemProps) =>
                    value.map((option, index) => {
                      const { key, ...tagProps } = getItemProps({ index });
                      return (
                        <Chip
                          key={key}
                          label={getPlantLabel(option)}
                          size="small"
                          color="success"
                          variant="outlined"
                          sx={{ maxWidth: 'none' }}
                          {...tagProps}
                        />
                      );
                    })
                  }
                  disabled={!!initialPlantKeys}
                  data-testid="plant-keys-autocomplete"
                  isOptionEqualToValue={(option, value) => option.key === value.key}
                />
              </Box>
            )}
          />

          {!slotKeys && (
            <FormTextField
              name="slot_keys_input"
              control={control}
              label={t('pages.wateringLogs.slotKeys')}
              helperText={t('pages.wateringLogs.slotKeysHelper')}
            />
          )}

          <Box sx={{ display: 'grid', gridTemplateColumns: { xs: '1fr', sm: '1fr 1fr' }, gap: { xs: 0, sm: 2 } }}>
            <FormSelectField
              name="application_method"
              control={control}
              label={t('pages.wateringLogs.applicationMethod')}
              required
              options={applicationMethods.map((v) => ({
                value: v,
                label: t(`enums.applicationMethod.${v}`),
              }))}
            />
            <FormSelectField
              name="water_source"
              control={control}
              label={t('pages.wateringLogs.waterSource')}
              options={waterSources.map((v) => ({
                value: v,
                label: t(`enums.waterSource.${v}`),
              }))}
            />
          </Box>

          <Box sx={{ display: 'grid', gridTemplateColumns: { xs: '1fr', sm: '1fr 1fr' }, gap: { xs: 0, sm: 2 } }}>
            <FormNumberField
              name="volume_liters"
              control={control}
              label={t('pages.wateringLogs.volumeLiters')}
              helperText={t('pages.wateringLogs.volumeLitersHelper')}
              suffix="L"
              min={0.01}
              inputMode="decimal"
              required
            />
            <Box sx={{ display: 'flex', alignItems: 'flex-start', pt: { xs: 0, sm: 0 } }}>
              <FormSwitchField
                name="is_supplemental"
                control={control}
                label={t('pages.wateringLogs.isSupplemental')}
                helperText={t('pages.wateringLogs.isSupplementalHelper')}
              />
            </Box>
          </Box>

          {/* Section: Measurements */}
          <Divider sx={{ my: 1.5 }} />
          <Typography variant="subtitle2" color="text.secondary" sx={{ mb: 1 }}>
            {t('pages.wateringLogs.sectionMeasurements')}
          </Typography>
          <Box sx={{ display: 'grid', gridTemplateColumns: { xs: '1fr', sm: '1fr 1fr' }, gap: { xs: 0, sm: 2 } }}>
            <FormNumberField
              name="ec_before"
              control={control}
              label={t('pages.wateringLogs.ecBefore')}
              helperText={t('pages.wateringLogs.ecHelper')}
              suffix="mS/cm"
              min={0}
              inputMode="decimal"
            />
            <FormNumberField
              name="ec_after"
              control={control}
              label={t('pages.wateringLogs.ecAfter')}
              suffix="mS/cm"
              min={0}
              inputMode="decimal"
            />
          </Box>
          <Box sx={{ display: 'grid', gridTemplateColumns: { xs: '1fr', sm: '1fr 1fr' }, gap: { xs: 0, sm: 2 } }}>
            <FormNumberField
              name="ph_before"
              control={control}
              label={t('pages.wateringLogs.phBefore')}
              helperText={t('pages.wateringLogs.phHelper')}
              min={0}
              max={14}
              inputMode="decimal"
            />
            <FormNumberField
              name="ph_after"
              control={control}
              label={t('pages.wateringLogs.phAfter')}
              min={0}
              max={14}
              inputMode="decimal"
            />
          </Box>

          {/* Section: Runoff */}
          <Divider sx={{ my: 1.5 }} />
          <Typography variant="subtitle2" color="text.secondary" sx={{ mb: 1 }}>
            {t('pages.wateringLogs.sectionRunoff')}
          </Typography>
          <Box sx={{ display: 'grid', gridTemplateColumns: { xs: '1fr', sm: '1fr 1fr' }, gap: { xs: 0, sm: 2 } }}>
            <FormNumberField
              name="runoff_ec"
              control={control}
              label={t('pages.wateringLogs.runoffEc')}
              helperText={t('pages.wateringLogs.runoffEcHelper')}
              suffix="mS/cm"
              min={0}
              inputMode="decimal"
            />
            <FormNumberField
              name="runoff_ph"
              control={control}
              label={t('pages.wateringLogs.runoffPh')}
              min={0}
              max={14}
              inputMode="decimal"
            />
          </Box>
          <FormNumberField
            name="runoff_volume_liters"
            control={control}
            label={t('pages.wateringLogs.runoffVolume')}
            suffix="L"
            min={0}
            inputMode="decimal"
          />

          {/* Section: Fertilizers */}
          <Divider sx={{ my: 1.5 }} />
          <Typography variant="subtitle2" color="text.secondary" sx={{ mb: 1 }}>
            {t('pages.wateringLogs.fertilizersUsed')}
          </Typography>
          {fields.map((field, index) => (
            <Box
              key={field.id}
              sx={{
                display: 'grid',
                gridTemplateColumns: { xs: '1fr auto', sm: '2fr 1fr auto' },
                gap: 1,
                alignItems: 'flex-start',
                mb: 0.5,
              }}
            >
              <FormSelectField
                name={`fertilizers_used.${index}.fertilizer_key`}
                control={control}
                label={t('pages.wateringLogs.fertilizerKey')}
                options={fertilizerSelectOptions}
                required
              />
              <Box sx={{ display: { xs: 'none', sm: 'block' } }}>
                <FormNumberField
                  name={`fertilizers_used.${index}.ml_per_liter`}
                  control={control}
                  label={t('pages.wateringLogs.mlPerLiter')}
                  suffix="ml/L"
                  min={0.01}
                  inputMode="decimal"
                />
              </Box>
              <Tooltip title={t('common.delete')}>
                <IconButton
                  onClick={() => remove(index)}
                  sx={{ mt: 1 }}
                  aria-label={t('common.delete')}
                  data-testid={`remove-fertilizer-${index}`}
                  size="small"
                >
                  <DeleteIcon />
                </IconButton>
              </Tooltip>
              {/* ml/L field on mobile (full width) */}
              <Box sx={{ display: { xs: 'block', sm: 'none' }, gridColumn: '1 / -1' }}>
                <FormNumberField
                  name={`fertilizers_used.${index}.ml_per_liter`}
                  control={control}
                  label={t('pages.wateringLogs.mlPerLiter')}
                  suffix="ml/L"
                  min={0.01}
                  inputMode="decimal"
                />
              </Box>
            </Box>
          ))}
          <Button
            size="small"
            variant="outlined"
            startIcon={<AddIcon />}
            onClick={() => append({ fertilizer_key: '', ml_per_liter: 1 })}
            sx={{ mb: 2 }}
            data-testid="add-fertilizer-button"
          >
            {t('pages.wateringLogs.addFertilizer')}
          </Button>

          {/* Additional info */}
          <Divider sx={{ my: 1.5 }} />
          <FormTextField
            name="performed_by"
            control={control}
            label={t('pages.wateringLogs.performedBy')}
          />
          <FormTextField
            name="notes"
            control={control}
            label={t('pages.wateringLogs.notes')}
            multiline
            minRows={2}
          />
          <FormActions
            onCancel={onClose}
            loading={saving}
            saveLabel={t('common.create')}
          />
        </Form>
      </DialogContent>
    </Dialog>
  );
}
