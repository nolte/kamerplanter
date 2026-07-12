import { useEffect, useMemo, useState } from 'react';
import { useTranslation } from 'react-i18next';
import type { TFunction } from 'i18next';
import Dialog from '@mui/material/Dialog';
import DialogTitle from '@mui/material/DialogTitle';
import DialogContent from '@mui/material/DialogContent';
import useMediaQuery from '@mui/material/useMediaQuery';
import { useTheme } from '@mui/material/styles';
import Box from '@mui/material/Box';
import Typography from '@mui/material/Typography';
import Divider from '@mui/material/Divider';
import Alert from '@mui/material/Alert';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import FormTextField from '@/components/form/FormTextField';
import FormSelectField from '@/components/form/FormSelectField';
import FormNumberField from '@/components/form/FormNumberField';
import FormRow from '@/components/form/FormRow';
import FormActions from '@/components/form/FormActions';
import UnsavedChangesGuard from '@/components/form/UnsavedChangesGuard';
import HelpTooltip from '@/components/common/HelpTooltip';
import { useNotification } from '@/hooks/useNotification';
import { useApiError } from '@/hooks/useApiError';
import * as api from '@/api/endpoints/environment';
import * as sitesApi from '@/api/endpoints/sites';
import type { ActuatorProtocol, ActuatorType, Location, Site } from '@/api/types';

const fieldWithHelpSx = { display: 'flex', alignItems: 'flex-start', gap: 0.5, flex: 1 } as const;

const ACTUATOR_TYPES: ActuatorType[] = [
  'light',
  'exhaust_fan',
  'circulation_fan',
  'heater',
  'cooler',
  'humidifier',
  'dehumidifier',
  'co2_doser',
  'irrigation_valve',
  'pump',
  'dosing_pump',
  'chiller',
  'air_pump',
  'uv_sterilizer',
  'shade_screen',
  'roof_vent',
  'energy_screen',
  'fogger',
  'generic_switch',
];

const PROTOCOLS: ActuatorProtocol[] = ['home_assistant', 'mqtt', 'manual'];

/**
 * Built inside the component (via `useMemo`) so every validation message is
 * translated instead of surfacing a raw, untranslated i18n-key-shaped string
 * as `helperText` (e.g. the previous literal "haEntityRequired") — see
 * `FormTextField`/`FormSelectField`, which render `fieldState.error.message`
 * verbatim without an extra `t()` pass.
 */
function buildSchema(t: TFunction) {
  return z
    .object({
      site_key: z.string().min(1, t('pages.environmentControl.validation.siteRequired')),
      location_key: z.string().min(1, t('pages.environmentControl.validation.locationRequired')),
      name: z.string().min(1, t('pages.environmentControl.validation.nameRequired')),
      actuator_type: z.enum(ACTUATOR_TYPES as [ActuatorType, ...ActuatorType[]]),
      protocol: z.enum(['home_assistant', 'mqtt', 'manual']),
      ha_entity_id: z.string().nullable(),
      mqtt_command_topic: z.string().nullable(),
      power_watts: z.number().min(0, t('pages.environmentControl.validation.powerNonNegative')).nullable(),
      notes: z.string().nullable(),
    })
    .refine((d) => d.protocol !== 'home_assistant' || !!d.ha_entity_id, {
      path: ['ha_entity_id'],
      message: t('pages.environmentControl.validation.haEntityRequired'),
    })
    .refine((d) => d.protocol !== 'mqtt' || !!d.mqtt_command_topic, {
      path: ['mqtt_command_topic'],
      message: t('pages.environmentControl.validation.mqttTopicRequired'),
    });
}

type FormData = z.infer<ReturnType<typeof buildSchema>>;

interface Props {
  open: boolean;
  onClose: () => void;
  onCreated: () => void;
  /** Whether the Home Assistant integration is available (REQ-005 §4a visibility). */
  haEnabled?: boolean;
}

const DEFAULTS: FormData = {
  site_key: '',
  location_key: '',
  name: '',
  actuator_type: 'light',
  protocol: 'home_assistant',
  ha_entity_id: null,
  mqtt_command_topic: null,
  power_watts: null,
  notes: null,
};

export default function ActuatorDialog({ open, onClose, onCreated, haEnabled = true }: Props) {
  const { t } = useTranslation();
  const theme = useTheme();
  const fullScreen = useMediaQuery(theme.breakpoints.down('sm'));
  const notification = useNotification();
  const { handleError } = useApiError();

  const [sites, setSites] = useState<Site[]>([]);
  const [locations, setLocations] = useState<Location[]>([]);

  // Re-built whenever the active language changes so validation messages stay
  // translated (see `buildSchema` doc comment above).
  const schema = useMemo(() => buildSchema(t), [t]);

  const {
    control,
    handleSubmit,
    reset,
    setError,
    watch,
    setValue,
    formState: { isDirty, isSubmitting },
  } = useForm<FormData>({ resolver: zodResolver(schema), defaultValues: DEFAULTS });

  const siteKey = watch('site_key');
  const protocol = watch('protocol');

  const protocolOptions = useMemo(
    () => PROTOCOLS.filter((p) => haEnabled || p !== 'home_assistant'),
    [haEnabled],
  );

  useEffect(() => {
    if (!open) return;
    let cancelled = false;
    const load = async () => {
      try {
        const data = await sitesApi.listSites();
        if (!cancelled) setSites(data);
      } catch (error) {
        if (!cancelled) handleError(error);
      }
    };
    void load();
    return () => {
      cancelled = true;
    };
  }, [open, handleError]);

  useEffect(() => {
    if (!siteKey) {
      setLocations([]);
      return;
    }
    let cancelled = false;
    const load = async () => {
      try {
        const data = await sitesApi.listLocations(siteKey);
        if (cancelled) return;
        setLocations(data);
        // A location from a previously selected site is no longer valid.
        setValue('location_key', '');
      } catch (error) {
        if (!cancelled) handleError(error);
      }
    };
    void load();
    return () => {
      cancelled = true;
    };
  }, [siteKey, handleError, setValue]);

  const onSubmit = async (data: FormData) => {
    try {
      await api.createActuator(data.location_key, {
        name: data.name,
        actuator_type: data.actuator_type,
        protocol: data.protocol,
        ha_entity_id: data.ha_entity_id,
        mqtt_command_topic: data.mqtt_command_topic,
        power_watts: data.power_watts,
        notes: data.notes,
      });
      reset(DEFAULTS);
      onCreated();
    } catch (error) {
      handleError(error, (name, message) => setError(name as keyof FormData, { message }));
      notification.error(t('errors.generic'));
    }
  };

  const handleClose = () => {
    reset(DEFAULTS);
    onClose();
  };

  return (
    <Dialog open={open} onClose={handleClose} fullScreen={fullScreen} fullWidth maxWidth="sm">
      <DialogTitle>{t('pages.environmentControl.createActuator')}</DialogTitle>
      <DialogContent>
        <UnsavedChangesGuard dirty={isDirty} />
        <form onSubmit={handleSubmit(onSubmit)} noValidate>
          {/* Section 1 — where the actuator lives (UI-NFR-008 R-037: grouped fields
              with a heading; identification fields come first). */}
          <Typography variant="subtitle1" sx={{ mb: 1.5 }}>
            {t('pages.environmentControl.sectionLocation')}
          </Typography>
          <FormRow>
            <FormSelectField
              name="site_key"
              control={control}
              label={t('pages.environmentControl.fields.site')}
              required
              autoFocus
              options={sites.map((s) => ({ value: s.key, label: s.name }))}
            />
            <FormSelectField
              name="location_key"
              control={control}
              label={t('pages.environmentControl.fields.location')}
              required
              disabled={!siteKey}
              options={locations.map((l) => ({ value: l.key, label: l.name }))}
            />
          </FormRow>
          <FormTextField
            name="name"
            control={control}
            label={t('pages.environmentControl.fields.name')}
            required
          />

          <Divider sx={{ my: 2 }} />

          {/* Section 2 — type + protocol drive which extra field(s) appear below,
              so the intro text calls that out explicitly for the user. */}
          <Typography variant="subtitle1" sx={{ mb: 0.5 }}>
            {t('pages.environmentControl.sectionConfig')}
          </Typography>
          <Typography variant="body2" color="text.secondary" sx={{ mb: 1.5 }}>
            {t('pages.environmentControl.sectionConfigIntro')}
          </Typography>
          <FormRow>
            <Box sx={fieldWithHelpSx}>
              <FormSelectField
                name="actuator_type"
                control={control}
                label={t('pages.environmentControl.fields.actuatorType')}
                required
                options={ACTUATOR_TYPES.map((v) => ({
                  value: v,
                  label: t(`enums.actuatorType.${v}`),
                }))}
              />
              <HelpTooltip term="aktor" iconOnly />
            </Box>
            <FormSelectField
              name="protocol"
              control={control}
              label={t('pages.environmentControl.fields.protocol')}
              required
              options={protocolOptions.map((v) => ({
                value: v,
                label: t(`enums.actuatorProtocol.${v}`),
              }))}
            />
          </FormRow>
          {protocol === 'home_assistant' && haEnabled && (
            <FormTextField
              name="ha_entity_id"
              control={control}
              label={t('pages.environmentControl.fields.haEntityId')}
              helperText={t('pages.environmentControl.fields.haEntityHelp')}
            />
          )}
          {protocol === 'mqtt' && (
            <FormTextField
              name="mqtt_command_topic"
              control={control}
              label={t('pages.environmentControl.fields.mqttTopic')}
              helperText={t('pages.environmentControl.fields.mqttTopicHelp')}
            />
          )}
          {protocol === 'manual' && (
            <Alert severity="info" sx={{ mb: 1.5 }} data-testid="manual-protocol-hint">
              {t('pages.environmentControl.fields.manualProtocolHint')}
            </Alert>
          )}

          <Divider sx={{ my: 2 }} />

          {/* Section 3 — everything below is optional. */}
          <Typography variant="subtitle1" sx={{ mb: 1.5 }}>
            {t('pages.environmentControl.sectionDetails')}
          </Typography>
          <FormNumberField
            name="power_watts"
            control={control}
            label={t('pages.environmentControl.fields.powerWatts')}
            helperText={t('pages.environmentControl.fields.powerWattsHelp')}
            step="any"
            min={0}
            suffix="W"
          />
          <FormTextField
            name="notes"
            control={control}
            label={t('pages.environmentControl.fields.notes')}
            multiline
            minRows={2}
          />
          <FormActions onCancel={handleClose} loading={isSubmitting} />
        </form>
      </DialogContent>
    </Dialog>
  );
}
