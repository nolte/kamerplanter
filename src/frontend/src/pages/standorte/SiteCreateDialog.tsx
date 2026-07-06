import { useEffect, useMemo, useState, useCallback } from 'react';
import { useTranslation } from 'react-i18next';
import Dialog from '@mui/material/Dialog';
import useMediaQuery from '@mui/material/useMediaQuery';
import { useTheme } from '@mui/material/styles';
import DialogTitle from '@mui/material/DialogTitle';
import DialogContent from '@mui/material/DialogContent';
import Typography from '@mui/material/Typography';
import Alert from '@mui/material/Alert';
import { useForm, useWatch } from 'react-hook-form';
import FormTextField from '@/components/form/FormTextField';
import FormNumberField from '@/components/form/FormNumberField';
import FormSelectField from '@/components/form/FormSelectField';
import FormRow from '@/components/form/FormRow';
import FormActions from '@/components/form/FormActions';
import ExpertiseFieldWrapper from '@/components/common/ExpertiseFieldWrapper';
import ShowAllFieldsToggle from '@/components/common/ShowAllFieldsToggle';
import WaterSourceSection, { TAP_WATER_DEFAULTS, RO_WATER_DEFAULTS } from '@/components/water/WaterSourceSection';
import { useExpertiseLevel } from '@/hooks/useExpertiseLevel';
import { useAppDispatch } from '@/store/hooks';
import { resetShowAllFields } from '@/store/slices/uiSlice';
import { useNotification } from '@/hooks/useNotification';
import { useApiError } from '@/hooks/useApiError';
import { siteFieldConfig } from '@/config/fieldConfigs';
import * as api from '@/api/endpoints/sites';
import type { SiteWaterConfig } from '@/api/types';
import { buildSiteResolver, gpsToPayload, siteTypeOptions, type SiteFormData } from './siteForm';

const DEFAULT_VALUES: SiteFormData = {
  name: '',
  type: 'indoor',
  gps_lat: '',
  gps_lon: '',
  climate_zone: '',
  total_area_m2: 0,
  timezone: 'UTC',
};

interface Props {
  open: boolean;
  onClose: () => void;
  onCreated: () => void;
}

export default function SiteCreateDialog({ open, onClose, onCreated }: Props) {
  const theme = useTheme();
  const fullScreen = useMediaQuery(theme.breakpoints.down('sm'));
  const { t } = useTranslation();
  const notification = useNotification();
  const { handleError } = useApiError();
  const dispatch = useAppDispatch();
  const [saving, setSaving] = useState(false);
  const { showAllOverride, toggleShowAll, level } = useExpertiseLevel();

  const handleClose = useCallback(() => {
    dispatch(resetShowAllFields());
    onClose();
  }, [dispatch, onClose]);
  const [waterConfig, setWaterConfig] = useState<SiteWaterConfig>({
    has_ro_system: false,
    tap_water_profile: { ...TAP_WATER_DEFAULTS },
    ro_water_profile: { ...RO_WATER_DEFAULTS },
  });

  const resolver = useMemo(() => buildSiteResolver(t), [t]);
  const typeOptions = useMemo(() => siteTypeOptions(t), [t]);
  const { control, handleSubmit, reset } = useForm<SiteFormData>({
    resolver,
    defaultValues: DEFAULT_VALUES,
  });
  // REQ-046 follow-up — the weather/frost section only ever unlocks for
  // outdoor/greenhouse sites (see WeatherSourceSection in SiteDetailPage).
  // Watching the live type keeps the discreet hint below the GPS fields in
  // sync as the user picks a different type, without waiting for submit.
  const watchedType = useWatch({ control, name: 'type' });
  const weatherEnabledForType = watchedType === 'outdoor' || watchedType === 'greenhouse';
  useEffect(() => {
    if (!open) {
      reset(DEFAULT_VALUES);
    }
  }, [open, reset]);


  const onSubmit = async (data: SiteFormData) => {
    try {
      setSaving(true);
      await api.createSite({
        name: data.name,
        type: data.type,
        gps_coordinates: gpsToPayload(data),
        climate_zone: data.climate_zone,
        total_area_m2: data.total_area_m2,
        timezone: data.timezone,
        water_config: waterConfig,
      });
      notification.success(t('common.create'));
      reset();
      setWaterConfig({ has_ro_system: false, tap_water_profile: { ...TAP_WATER_DEFAULTS }, ro_water_profile: { ...RO_WATER_DEFAULTS } });
      onCreated();
    } catch (err) {
      handleError(err);
    } finally {
      setSaving(false);
    }
  };

  const fc = siteFieldConfig;

  return (
    <Dialog fullScreen={fullScreen} open={open} onClose={handleClose} maxWidth="sm" fullWidth aria-labelledby="site-create-dialog-title" data-testid="site-create-dialog">
      <DialogTitle id="site-create-dialog-title">{t('pages.sites.create')}</DialogTitle>
      <DialogContent>
        <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
          {t('pages.sites.createIntro')}
        </Typography>
        <form onSubmit={handleSubmit(onSubmit)}>
          {/* beginner */}
          <FormTextField name="name" control={control} label={t('pages.sites.name')} helperText={t('pages.sites.nameHelper')} required autoFocus />
          <ExpertiseFieldWrapper minLevel={fc.type.level}>
            <FormSelectField name="type" control={control} label={t('pages.sites.type')} options={typeOptions} helperText={t('pages.sites.typeHelper')} required />
          </ExpertiseFieldWrapper>
          {/* intermediate */}
          <ExpertiseFieldWrapper minLevel={fc.gps.level}>
            <Typography variant="body2" color="text.secondary" sx={{ mt: 1, mb: 0.5 }}>
              {t('pages.sites.gpsHelper')}
            </Typography>
            <FormRow>
              <FormNumberField name="gps_lat" control={control} label={t('pages.sites.gpsLat')} min={-90} max={90} />
              <FormNumberField name="gps_lon" control={control} label={t('pages.sites.gpsLon')} min={-180} max={180} />
            </FormRow>
            {!weatherEnabledForType && (
              <Alert severity="info" variant="outlined" icon={false} sx={{ py: 0.5, mb: 1.5 }} data-testid="site-weather-type-hint">
                <Typography variant="caption">
                  {t('pages.sites.weatherTypeHint', {
                    outdoorLabel: t('enums.siteType.outdoor'),
                    greenhouseLabel: t('enums.siteType.greenhouse'),
                  })}
                </Typography>
              </Alert>
            )}
          </ExpertiseFieldWrapper>
          <ExpertiseFieldWrapper minLevel={fc.climate_zone.level}>
            <FormTextField name="climate_zone" control={control} label={t('pages.sites.climateZone')} helperText={t('pages.sites.climateZoneHelper')} />
          </ExpertiseFieldWrapper>
          <ExpertiseFieldWrapper minLevel={fc.total_area_m2.level}>
            <FormNumberField name="total_area_m2" control={control} label={t('pages.sites.totalArea')} helperText={t('pages.sites.totalAreaHelper')} min={0} />
          </ExpertiseFieldWrapper>
          {/* water config (intermediate+) */}
          <ExpertiseFieldWrapper minLevel={fc.water_config.level}>
            <WaterSourceSection value={waterConfig} onChange={setWaterConfig} />
          </ExpertiseFieldWrapper>
          {/* expert */}
          <ExpertiseFieldWrapper minLevel={fc.timezone.level}>
            <FormTextField name="timezone" control={control} label={t('pages.sites.timezone')} helperText={t('pages.sites.timezoneHelper')} />
          </ExpertiseFieldWrapper>
          {level !== 'expert' && (
            <ShowAllFieldsToggle showAll={showAllOverride} onToggle={toggleShowAll} />
          )}
          <FormActions onCancel={handleClose} loading={saving} saveLabel={t('common.create')} />
        </form>
      </DialogContent>
    </Dialog>
  );
}
