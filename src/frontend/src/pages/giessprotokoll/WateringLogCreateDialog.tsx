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
import FormTextField from '@/components/form/FormTextField';
import FormSelectField from '@/components/form/FormSelectField';
import FormNumberField from '@/components/form/FormNumberField';
import FormSwitchField from '@/components/form/FormSwitchField';
import FormActions from '@/components/form/FormActions';
import { useNotification } from '@/hooks/useNotification';
import { useApiError } from '@/hooks/useApiError';
import * as wateringLogApi from '@/api/endpoints/watering-logs';
import * as plantApi from '@/api/endpoints/plantInstances';
import * as fertApi from '@/api/endpoints/fertilizers';
import type { PlantInstance, Fertilizer } from '@/api/types';

const applicationMethods = ['fertigation', 'drench', 'foliar', 'top_dress'] as const;
const waterSources = ['tank', 'tap', 'osmose', 'rainwater', 'distilled', 'well'] as const;

const fertilizerLineSchema = z.object({
  fertilizer_key: z.string().min(1),
  ml_per_liter: z.number().gt(0),
});

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
        plantApi.listPlantInstances(0, 500).catch(() => []),
        availableFertilizers
          ? Promise.resolve(availableFertilizers)
          : fertApi.fetchFertilizers(0, 500).catch(() => []),
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

  const { control, handleSubmit, reset } = useForm<FormData>({
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
      notification.success(t('common.create'));
      reset();
      onCreated();
    } catch (err) {
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
    >
      <DialogTitle>{t('pages.wateringLogs.create')}</DialogTitle>
      <DialogContent>
        {channelPreset && (
          <Alert severity="info" sx={{ mb: 2 }}>
            {t('pages.wateringLogs.channelPresetInfo', { channel: channelPreset.channelLabel })}
            {channelPreset.targetEcMs != null && ` — EC: ${channelPreset.targetEcMs} mS`}
            {channelPreset.targetPh != null && ` — pH: ${channelPreset.targetPh}`}
          </Alert>
        )}
        <form onSubmit={handleSubmit(onSubmit)}>
          {/* Section: Basics */}
          <Typography variant="subtitle2" color="text.secondary" sx={{ mb: 1, mt: 0.5 }}>
            {t('pages.wateringLogs.sectionBasics')}
          </Typography>

          {/* Plant selection (multi-select autocomplete) */}
          <Controller
            name="plant_keys"
            control={control}
            render={({ field }) => (
              <Autocomplete
                multiple
                options={plantOptions}
                getOptionLabel={(option) => option.plant_name || option.instance_id}
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
                    data-testid="plant-keys-input"
                    sx={{ mb: 2 }}
                  />
                )}
                renderTags={(value, getTagProps) =>
                  value.map((option, index) => {
                    const { key, ...tagProps } = getTagProps({ index });
                    return (
                      <Chip
                        key={key}
                        label={option.plant_name || option.instance_id}
                        size="small"
                        color="success"
                        variant="outlined"
                        {...tagProps}
                      />
                    );
                  })
                }
                disabled={!!initialPlantKeys}
                data-testid="plant-keys-autocomplete"
                isOptionEqualToValue={(option, value) => option.key === value.key}
              />
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
            />
            <Box sx={{ display: 'flex', alignItems: 'flex-start', pt: { xs: 0, sm: 0 } }}>
              <FormSwitchField
                name="is_supplemental"
                control={control}
                label={t('pages.wateringLogs.isSupplemental')}
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
        </form>
      </DialogContent>
    </Dialog>
  );
}
