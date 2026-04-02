import { useEffect, useState, useCallback } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import Box from '@mui/material/Box';
import Card from '@mui/material/Card';
import CardContent from '@mui/material/CardContent';
import Button from '@mui/material/Button';
import Chip from '@mui/material/Chip';
import IconButton from '@mui/material/IconButton';
import Typography from '@mui/material/Typography';
import AddIcon from '@mui/icons-material/Add';
import DeleteIcon from '@mui/icons-material/Delete';
import EditIcon from '@mui/icons-material/Edit';
import SensorsIcon from '@mui/icons-material/Sensors';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import MobileCard from '@/components/common/MobileCard';
import PageTitle from '@/components/layout/PageTitle';
import LoadingSkeleton from '@/components/common/LoadingSkeleton';
import ErrorDisplay from '@/components/common/ErrorDisplay';
import EmptyState from '@/components/common/EmptyState';
import ConfirmDialog from '@/components/common/ConfirmDialog';
import DataTable, { type Column } from '@/components/common/DataTable';
import { useTableLocalState } from '@/hooks/useTableState';
import FormTextField from '@/components/form/FormTextField';
import FormNumberField from '@/components/form/FormNumberField';
import FormActions from '@/components/form/FormActions';
import FormRow from '@/components/form/FormRow';
import UnsavedChangesGuard from '@/components/form/UnsavedChangesGuard';
import WaterSourceSection, { TAP_WATER_DEFAULTS, RO_WATER_DEFAULTS } from '@/components/water/WaterSourceSection';
import LocationTreeSection from './LocationTreeSection';
import SiteRunsSection from './SiteRunsSection';
import SensorCreateDialog from './SensorCreateDialog';
import { useNotification } from '@/hooks/useNotification';
import { useApiError } from '@/hooks/useApiError';
import { useAppDispatch, useAppSelector } from '@/store/hooks';
import { fetchSite, clearCurrent } from '@/store/slices/sitesSlice';
import { setBreadcrumbs } from '@/store/slices/uiSlice';
import * as api from '@/api/endpoints/sites';
import * as tankApi from '@/api/endpoints/tanks';
import type { Sensor, SiteWaterConfig } from '@/api/types';

const schema = z.object({
  name: z.string().min(1),
  climate_zone: z.string(),
  total_area_m2: z.number().min(0),
  timezone: z.string(),
});

type FormData = z.infer<typeof schema>;

export default function SiteDetailPage() {
  const { key } = useParams<{ key: string }>();
  const { t } = useTranslation();
  const dispatch = useAppDispatch();
  const navigate = useNavigate();
  const notification = useNotification();
  const { handleError } = useApiError();
  const { currentSite: current, loading, error } = useAppSelector((s) => s.sites);
  const [saving, setSaving] = useState(false);
  const [deleteOpen, setDeleteOpen] = useState(false);
  const [sensors, setSensors] = useState<Sensor[]>([]);
  const [sensorDialogOpen, setSensorDialogOpen] = useState(false);
  const [editSensor, setEditSensor] = useState<Sensor | undefined>(undefined);
  const [deleteSensorKey, setDeleteSensorKey] = useState<string | null>(null);
  const [waterConfig, setWaterConfig] = useState<SiteWaterConfig>({
    has_ro_system: false,
    tap_water_profile: { ...TAP_WATER_DEFAULTS },
    ro_water_profile: { ...RO_WATER_DEFAULTS },
  });
  const sensorTableState = useTableLocalState({ defaultSort: { column: 'name', direction: 'asc' } });

  const { control, handleSubmit, reset, formState: { isDirty } } = useForm<FormData>({
    resolver: zodResolver(schema),
    defaultValues: { name: '', climate_zone: '', total_area_m2: 0, timezone: 'UTC' },
  });

  const loadSensors = useCallback(async () => {
    if (!key) return;
    try {
      const s = await api.getSiteSensors(key);
      setSensors(s);
    } catch {
      // Sensors may not be available
    }
  }, [key]);

  useEffect(() => {
    if (key) {
      dispatch(fetchSite(key));
      loadSensors();
    }
    return () => { dispatch(clearCurrent()); };
  }, [key, dispatch, loadSensors]);

  useEffect(() => {
    if (current) {
      reset({ name: current.name, climate_zone: current.climate_zone, total_area_m2: current.total_area_m2, timezone: current.timezone ?? 'UTC' });
      const wc = current.water_config;
      setWaterConfig({
        has_ro_system: wc?.has_ro_system ?? false,
        tap_water_profile: wc?.tap_water_profile ?? { ...TAP_WATER_DEFAULTS },
        ro_water_profile: wc?.ro_water_profile ?? { ...RO_WATER_DEFAULTS },
      });
    }
  }, [current, reset]);

  // Dynamic breadcrumbs
  useEffect(() => {
    if (!current) return;
    dispatch(setBreadcrumbs([
      { label: 'nav.dashboard', path: '/dashboard' },
      { label: 'nav.sites', path: '/standorte/sites' },
      { label: current.name },
    ]));
  }, [current, dispatch]);

  // Clear dynamic breadcrumbs on unmount
  useEffect(() => () => { dispatch(setBreadcrumbs([])); }, [dispatch]);

  const onSubmit = async (data: FormData) => {
    if (!key) return;
    try {
      setSaving(true);
      await api.updateSite(key, {
        ...data,
        water_config: waterConfig,
      });
      notification.success(t('common.save'));
      dispatch(fetchSite(key));
    } catch (err) {
      handleError(err);
    } finally {
      setSaving(false);
    }
  };

  const onDelete = async () => {
    if (!key) return;
    try {
      await api.deleteSite(key);
      notification.success(t('common.delete'));
      navigate('/standorte/sites');
    } catch (err) {
      handleError(err);
    }
    setDeleteOpen(false);
  };

  if (loading) return <LoadingSkeleton variant="form" />;
  if (error) return <ErrorDisplay error={error} onRetry={() => navigate(-1)} />;

  const PANEL_GAP = 4;

  return (
    <Box data-testid="site-detail-page">
      <UnsavedChangesGuard dirty={isDirty} />
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <PageTitle title={current?.name ?? t('entities.site')} />
        <Button color="error" startIcon={<DeleteIcon />} onClick={() => setDeleteOpen(true)}>
          {t('common.delete')}
        </Button>
      </Box>

      <Box component="form" onSubmit={handleSubmit(onSubmit)} sx={{ maxWidth: 900, display: 'flex', flexDirection: 'column', gap: PANEL_GAP }}>
        <Typography variant="body2" color="text.secondary">
          {t('pages.sites.editIntro')}
        </Typography>

        <Card variant="outlined">
          <CardContent component="fieldset" sx={{ border: 'none', p: 0, m: 0, '&:last-child': { pb: 2 }, px: 2, pt: 2 }}>
            <Typography component="legend" variant="h6" sx={{ pt: 1.5, mb: 0.5 }}>
              {t('pages.sites.sectionBasicData')}
            </Typography>
            <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
              {t('pages.sites.sectionBasicDataDesc')}
            </Typography>
            <FormTextField name="name" control={control} label={t('pages.sites.name')} required autoFocus />
            <FormRow>
              <FormTextField name="climate_zone" control={control} label={t('pages.sites.climateZone')} />
              <FormNumberField name="total_area_m2" control={control} label={t('pages.sites.totalArea')} helperText={t('pages.sites.totalAreaHelper')} min={0} />
            </FormRow>
            <FormTextField name="timezone" control={control} label={t('pages.sites.timezone')} helperText={t('pages.sites.timezoneHelper')} />
          </CardContent>
        </Card>

        <Card variant="outlined">
          <CardContent>
            <WaterSourceSection
              value={waterConfig}
              onChange={setWaterConfig}
              warnings={current?.water_config_warnings}
            />
          </CardContent>
        </Card>

        <Typography variant="caption" color="text.secondary">* {t('common.required')}</Typography>
        <FormActions onCancel={() => navigate(-1)} loading={saving} />
      </Box>

      {/* Sensors */}
      <Box sx={{ mt: 4 }}>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
          <Typography variant="h6" sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <SensorsIcon />
            {t('pages.sensors.title')}
          </Typography>
          <Button startIcon={<AddIcon />} onClick={() => { setEditSensor(undefined); setSensorDialogOpen(true); }} data-testid="add-sensor-button">
            {t('pages.sensors.add')}
          </Button>
        </Box>
        {sensors.length === 0 ? (
          <EmptyState
            message={t('pages.sensors.noSensors')}
            actionLabel={t('pages.sensors.add')}
            onAction={() => { setEditSensor(undefined); setSensorDialogOpen(true); }}
          />
        ) : (
          <DataTable<Sensor>
            columns={[
              { id: 'name', label: t('pages.sensors.name'), render: (r) => r.name },
              { id: 'metricType', label: t('pages.sensors.metricType'), render: (r) => r.metric_type },
              { id: 'haEntityId', label: t('pages.sensors.haEntityId'), render: (r) => r.ha_entity_id || '—' },
              { id: 'active', label: t('pages.sensors.active'), render: (r) => (
                <Chip label={r.is_active ? t('common.yes') : t('common.no')} size="small" color={r.is_active ? 'success' : 'default'} />
              )},
              { id: 'actions', label: '', render: (r) => (
                <Box sx={{ display: 'flex', gap: 0.5 }}>
                  <IconButton size="small" onClick={(e) => { e.stopPropagation(); setEditSensor(r); setSensorDialogOpen(true); }}>
                    <EditIcon fontSize="small" />
                  </IconButton>
                  <IconButton size="small" onClick={(e) => { e.stopPropagation(); setDeleteSensorKey(r.key); }}>
                    <DeleteIcon fontSize="small" />
                  </IconButton>
                </Box>
              )},
            ] satisfies Column<Sensor>[]}
            rows={sensors}
            getRowKey={(r) => r.key}
            tableState={sensorTableState}
            ariaLabel={t('pages.sensors.title')}
            mobileCardRenderer={(r) => (
              <MobileCard
                title={r.name}
                subtitle={r.ha_entity_id || undefined}
                chips={
                  <Chip
                    label={r.is_active ? t('common.yes') : t('common.no')}
                    size="small"
                    color={r.is_active ? 'success' : 'default'}
                  />
                }
                fields={[
                  { label: t('pages.sensors.metricType'), value: r.metric_type },
                ]}
              />
            )}
          />
        )}
      </Box>

      {key && (
        <SensorCreateDialog
          open={sensorDialogOpen}
          onClose={() => { setSensorDialogOpen(false); setEditSensor(undefined); }}
          context={{ parentType: 'site', parentKey: key }}
          sensor={editSensor}
          onSaved={() => { setSensorDialogOpen(false); setEditSensor(undefined); loadSensors(); }}
        />
      )}

      <ConfirmDialog
        open={!!deleteSensorKey}
        title={t('common.delete')}
        message={t('common.deleteConfirm', { name: sensors.find((s) => s.key === deleteSensorKey)?.name })}
        onConfirm={async () => {
          if (deleteSensorKey) {
            try {
              await tankApi.deleteSensor(deleteSensorKey);
              notification.success(t('pages.sensors.deleted'));
              loadSensors();
            } catch (err) {
              handleError(err);
            }
          }
          setDeleteSensorKey(null);
        }}
        onCancel={() => setDeleteSensorKey(null)}
        destructive
      />

      {key && <LocationTreeSection siteKey={key} />}
      {key && <SiteRunsSection siteKey={key} />}

      <ConfirmDialog
        open={deleteOpen}
        title={t('common.delete')}
        message={t('common.deleteConfirm', { name: current?.name })}
        onConfirm={onDelete}
        onCancel={() => setDeleteOpen(false)}
        destructive
      />
    </Box>
  );
}
