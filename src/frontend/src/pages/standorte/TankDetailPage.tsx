import { useEffect, useState, useCallback } from 'react';
import { useTabUrl } from '@/hooks/useTabUrl';
import { useParams, useNavigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import Box from '@mui/material/Box';
import Button from '@mui/material/Button';
import Typography from '@mui/material/Typography';
import Chip from '@mui/material/Chip';
import Card from '@mui/material/Card';
import CardContent from '@mui/material/CardContent';
import Table from '@mui/material/Table';
import TableBody from '@mui/material/TableBody';
import TableCell from '@mui/material/TableCell';
import TableRow from '@mui/material/TableRow';
import Tabs from '@mui/material/Tabs';
import Tab from '@mui/material/Tab';
import Alert from '@mui/material/Alert';
import DeleteIcon from '@mui/icons-material/Delete';
import EditIcon from '@mui/icons-material/Edit';
import IconButton from '@mui/material/IconButton';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import PageTitle from '@/components/layout/PageTitle';
import LoadingSkeleton from '@/components/common/LoadingSkeleton';
import ErrorDisplay from '@/components/common/ErrorDisplay';
import ConfirmDialog from '@/components/common/ConfirmDialog';
import DataTable, { type Column } from '@/components/common/DataTable';
import { useTableLocalState } from '@/hooks/useTableState';
import FormTextField from '@/components/form/FormTextField';
import FormSelectField from '@/components/form/FormSelectField';
import FormNumberField from '@/components/form/FormNumberField';
import FormSwitchField from '@/components/form/FormSwitchField';
import FormActions from '@/components/form/FormActions';
import FormRow from '@/components/form/FormRow';
import UnsavedChangesGuard from '@/components/form/UnsavedChangesGuard';
import { useNotification } from '@/hooks/useNotification';
import { useApiError } from '@/hooks/useApiError';
import TextField from '@mui/material/TextField';
import MenuItem from '@mui/material/MenuItem';
import * as tankApi from '@/api/endpoints/tanks';
import * as sitesApi from '@/api/endpoints/sites';
import CircularProgress from '@mui/material/CircularProgress';
import type {
  Tank,
  TankState,
  TankAlert,
  TankFillEvent,
  MaintenanceLog,
  MaintenanceSchedule,
  DueMaintenance,
  Site,
  Location,
  Sensor,
  LiveStateResponse,
} from '@/api/types';
import TankStateCreateDialog from './TankStateCreateDialog';
import MaintenanceLogDialog from './MaintenanceLogDialog';
import MaintenanceScheduleDialog from './MaintenanceScheduleDialog';
import TankFillCreateDialog from './TankFillCreateDialog';
import SensorCreateDialog from './SensorCreateDialog';

const tankTypes = ['nutrient', 'irrigation', 'reservoir', 'recirculation', 'stock_solution'] as const;
const materials = ['plastic', 'stainless_steel', 'glass', 'ibc'] as const;

const editSchema = z.object({
  name: z.string().min(1).max(200),
  tank_type: z.enum(tankTypes),
  volume_liters: z.number().gt(0),
  material: z.enum(materials),
  location_key: z.string().nullable(),
  has_lid: z.boolean(),
  has_air_pump: z.boolean(),
  has_circulation_pump: z.boolean(),
  has_heater: z.boolean(),
  is_light_proof: z.boolean(),
  has_uv_sterilizer: z.boolean(),
  has_ozone_generator: z.boolean(),
  notes: z.string().nullable(),
});

type EditFormData = z.infer<typeof editSchema>;

const severityColor: Record<string, 'error' | 'warning' | 'info'> = {
  critical: 'error',
  high: 'error',
  medium: 'warning',
  low: 'info',
};

const sourceChipColor: Record<string, 'default' | 'primary' | 'success' | 'secondary'> = {
  manual: 'default',
  ha_auto: 'primary',
  ha_live: 'success',
  mqtt_auto: 'secondary',
};

function getFreshness(recordedAt: string | null): { color: 'success' | 'warning' | 'error'; key: string; minutes?: number } {
  if (!recordedAt) return { color: 'error', key: 'freshOffline' };
  const diffMs = Date.now() - new Date(recordedAt).getTime();
  const minutes = Math.floor(diffMs / 60_000);
  if (minutes < 5) return { color: 'success', key: 'freshLive' };
  if (minutes <= 60) return { color: 'warning', key: 'freshRecent', minutes };
  return { color: 'error', key: 'freshStale' };
}

export default function TankDetailPage() {
  const { key } = useParams<{ key: string }>();
  const { t } = useTranslation();
  const navigate = useNavigate();
  const notification = useNotification();
  const { handleError } = useApiError();

  const [tank, setTank] = useState<Tank | null>(null);
  const [latestState, setLatestState] = useState<TankState | null>(null);
  const [alerts, setAlerts] = useState<TankAlert[]>([]);
  const [states, setStates] = useState<TankState[]>([]);
  const [maintenanceLogs, setMaintenanceLogs] = useState<MaintenanceLog[]>([]);
  const [dueMaintenances, setDueMaintenances] = useState<DueMaintenance[]>([]);
  const [schedules, setSchedules] = useState<MaintenanceSchedule[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [tab, setTab] = useTabUrl(['details', 'states', 'maintenance', 'schedules', 'fills', 'edit']);
  const [saving, setSaving] = useState(false);
  const [deleteOpen, setDeleteOpen] = useState(false);
  const [stateDialogOpen, setStateDialogOpen] = useState(false);
  const [maintenanceDialogOpen, setMaintenanceDialogOpen] = useState(false);
  const [fillDialogOpen, setFillDialogOpen] = useState(false);
  const [fillEvents, setFillEvents] = useState<TankFillEvent[]>([]);
  const [scheduleDialogOpen, setScheduleDialogOpen] = useState(false);
  const [editSchedule, setEditSchedule] = useState<MaintenanceSchedule | undefined>(undefined);
  const [deleteScheduleKey, setDeleteScheduleKey] = useState<string | null>(null);
  const [sites, setSites] = useState<Site[]>([]);
  const [locations, setLocations] = useState<Location[]>([]);
  const [selectedSiteKey, setSelectedSiteKey] = useState('');
  const [siteName, setSiteName] = useState('');
  const [locationName, setLocationName] = useState('');
  const [sensors, setSensors] = useState<Sensor[]>([]);
  const [liveState, setLiveState] = useState<LiveStateResponse | null>(null);
  const [liveLoading, setLiveLoading] = useState(false);
  const [adoptingAll, setAdoptingAll] = useState(false);
  const [sensorDialogOpen, setSensorDialogOpen] = useState(false);
  const [editSensor, setEditSensor] = useState<Sensor | undefined>(undefined);
  const [deleteSensorKey, setDeleteSensorKey] = useState<string | null>(null);

  const statesTableState = useTableLocalState({ defaultSort: { column: 'recordedAt', direction: 'desc' } });
  const dueTableState = useTableLocalState({ defaultSort: { column: 'nextDue', direction: 'asc' } });
  const logsTableState = useTableLocalState({ defaultSort: { column: 'performedAt', direction: 'desc' } });
  const fillsTableState = useTableLocalState({ defaultSort: { column: 'filledAt', direction: 'desc' } });
  const schedulesTableState = useTableLocalState({ defaultSort: { column: 'type', direction: 'asc' } });

  const {
    control,
    handleSubmit,
    reset,
    setValue,
    formState: { isDirty },
  } = useForm<EditFormData>({
    resolver: zodResolver(editSchema),
    defaultValues: {
      name: '',
      tank_type: 'nutrient',
      volume_liters: 50,
      material: 'plastic',
      location_key: null,
      has_lid: false,
      has_air_pump: false,
      has_circulation_pump: false,
      has_heater: false,
      is_light_proof: false,
      has_uv_sterilizer: false,
      has_ozone_generator: false,
      notes: null,
    },
  });

  const load = useCallback(async () => {
    if (!key) return;
    setLoading(true);
    try {
      const [tankData, allSites] = await Promise.all([
        tankApi.getTank(key),
        sitesApi.listSites(0, 200),
      ]);
      setTank(tankData);
      setSites(allSites);
      reset({
        name: tankData.name,
        tank_type: tankData.tank_type,
        volume_liters: tankData.volume_liters,
        material: tankData.material,
        location_key: tankData.location_key,
        has_lid: tankData.has_lid,
        has_air_pump: tankData.has_air_pump,
        has_circulation_pump: tankData.has_circulation_pump,
        has_heater: tankData.has_heater,
        is_light_proof: tankData.is_light_proof,
        has_uv_sterilizer: tankData.has_uv_sterilizer,
        has_ozone_generator: tankData.has_ozone_generator,
        notes: tankData.notes,
      });

      // Resolve location/site names for display and pre-select edit cascade
      if (tankData.location_key) {
        try {
          const loc = await sitesApi.getLocation(tankData.location_key);
          setLocationName(loc.name);
          const site = allSites.find((s) => s.key === loc.site_key);
          setSiteName(site?.name ?? '');
          setSelectedSiteKey(loc.site_key);
          const locs = await sitesApi.listLocations(loc.site_key);
          setLocations(locs);
        } catch {
          setLocationName('');
          setSiteName('');
          setSelectedSiteKey('');
          setLocations([]);
        }
      } else {
        setLocationName('');
        setSiteName('');
        setSelectedSiteKey('');
        setLocations([]);
      }

      const [ls, al, st, ml, dm, sc, fe, sn] = await Promise.all([
        tankApi.getLatestState(key),
        tankApi.getAlerts(key),
        tankApi.getStates(key),
        tankApi.getMaintenanceHistory(key),
        tankApi.getDueMaintenances(key),
        tankApi.getSchedules(key),
        tankApi.getFillEvents(key),
        tankApi.getSensors(key),
      ]);
      setLatestState(ls);
      setAlerts(al);
      setStates(st);
      setMaintenanceLogs(ml);
      setDueMaintenances(dm);
      setSchedules(sc);
      setFillEvents(fe);
      setSensors(sn);
      setError(null);
    } catch (err) {
      setError(String(err));
    } finally {
      setLoading(false);
    }
  }, [key, reset]);

  useEffect(() => {
    load();
  }, [load]);

  const onSave = async (data: EditFormData) => {
    if (!key) return;
    try {
      setSaving(true);
      await tankApi.updateTank(key, { ...data, location_key: data.location_key || null });
      notification.success(t('common.save'));
      load();
    } catch (err) {
      handleError(err);
    } finally {
      setSaving(false);
    }
  };

  const onDelete = async () => {
    if (!key) return;
    try {
      await tankApi.deleteTank(key);
      notification.success(t('common.delete'));
      navigate('/standorte/tanks');
    } catch (err) {
      handleError(err);
    }
  };

  const onDeleteSchedule = async () => {
    if (!key || !deleteScheduleKey) return;
    try {
      await tankApi.deleteSchedule(key, deleteScheduleKey);
      notification.success(t('pages.tanks.scheduleDeleted'));
      setDeleteScheduleKey(null);
      load();
    } catch (err) {
      handleError(err);
    }
  };

  const handleSiteChange = (siteKey: string) => {
    setSelectedSiteKey(siteKey);
    setValue('location_key', null, { shouldDirty: true });
    if (siteKey) {
      sitesApi.listLocations(siteKey).then(setLocations).catch(() => setLocations([]));
    } else {
      setLocations([]);
    }
  };

  const handleLiveQuery = async () => {
    if (!key) return;
    setLiveLoading(true);
    try {
      const result = await tankApi.getLiveState(key);
      setLiveState(result);
    } catch (err) {
      handleError(err);
    } finally {
      setLiveLoading(false);
    }
  };

  const handleAdoptAll = async () => {
    if (!key || !liveState) return;
    setAdoptingAll(true);
    try {
      const payload: Record<string, unknown> = { source: 'ha_live' };
      for (const [metric, entry] of Object.entries(liveState.values)) {
        payload[metric] = entry.value;
      }
      await tankApi.recordState(key, payload as Parameters<typeof tankApi.recordState>[1]);
      notification.success(t('pages.tanks.adopted'));
      setLiveState(null);
      load();
    } catch (err) {
      handleError(err);
    } finally {
      setAdoptingAll(false);
    }
  };

  const onDeleteSensor = async () => {
    if (!deleteSensorKey) return;
    try {
      await tankApi.deleteSensor(deleteSensorKey);
      notification.success(t('pages.tanks.sensorDeleted'));
      setDeleteSensorKey(null);
      load();
    } catch (err) {
      handleError(err);
    }
  };

  // Column definitions for data tables
  const stateColumns: Column<TankState>[] = [
    { id: 'recordedAt', label: t('pages.tanks.recordedAt'), render: (r) => r.recorded_at ? new Date(r.recorded_at).toLocaleString() : '\u2014' },
    { id: 'ph', label: 'pH', render: (r) => r.ph ?? '\u2014', align: 'right' },
    { id: 'ec', label: 'EC (mS/cm)', render: (r) => r.ec_ms ?? '\u2014', align: 'right' },
    { id: 'temp', label: t('pages.tanks.waterTemp'), render: (r) => r.water_temp_celsius != null ? `${r.water_temp_celsius} °C` : '\u2014', align: 'right' },
    { id: 'fillLevel', label: t('pages.tanks.fillLevel'), render: (r) => r.fill_level_percent != null ? `${r.fill_level_percent}%` : '\u2014', align: 'right' },
    { id: 'tds', label: 'TDS (ppm)', render: (r) => r.tds_ppm ?? '\u2014', align: 'right' },
  ];

  const dueColumns: Column<DueMaintenance>[] = [
    { id: 'type', label: t('pages.tanks.maintenanceType'), render: (r) => t(`enums.maintenanceType.${r.maintenance_type}`), searchValue: (r) => t(`enums.maintenanceType.${r.maintenance_type}`) },
    { id: 'nextDue', label: t('pages.tanks.nextDue'), render: (r) => new Date(r.next_due).toLocaleDateString() },
    {
      id: 'status', label: t('pages.tanks.status'), render: (r) => (
        <Chip label={t(`enums.maintenanceStatus.${r.status}`)} size="small" color={r.status === 'overdue' ? 'error' : r.status === 'due_soon' ? 'warning' : 'success'} />
      ), searchValue: (r) => t(`enums.maintenanceStatus.${r.status}`),
    },
    { id: 'priority', label: t('pages.tanks.priority'), render: (r) => t(`enums.maintenancePriority.${r.priority}`), searchValue: (r) => t(`enums.maintenancePriority.${r.priority}`) },
  ];

  const logColumns: Column<MaintenanceLog>[] = [
    { id: 'type', label: t('pages.tanks.maintenanceType'), render: (r) => t(`enums.maintenanceType.${r.maintenance_type}`), searchValue: (r) => t(`enums.maintenanceType.${r.maintenance_type}`) },
    { id: 'performedAt', label: t('pages.tanks.performedAt'), render: (r) => r.performed_at ? new Date(r.performed_at).toLocaleString() : '\u2014' },
    { id: 'performedBy', label: t('pages.tanks.performedBy'), render: (r) => r.performed_by || '\u2014' },
    { id: 'duration', label: t('pages.tanks.duration'), render: (r) => r.duration_minutes != null ? `${r.duration_minutes} min` : '\u2014', align: 'right' },
    { id: 'notes', label: t('pages.tanks.notes'), render: (r) => r.notes || '\u2014' },
  ];

  const scheduleColumns: Column<MaintenanceSchedule>[] = [
    { id: 'type', label: t('pages.tanks.maintenanceType'), render: (r) => t(`enums.maintenanceType.${r.maintenance_type}`), searchValue: (r) => t(`enums.maintenanceType.${r.maintenance_type}`) },
    { id: 'intervalDays', label: t('pages.tanks.intervalDays'), render: (r) => r.interval_days, align: 'right' },
    { id: 'reminderDays', label: t('pages.tanks.reminderDays'), render: (r) => r.reminder_days_before, align: 'right' },
    { id: 'priority', label: t('pages.tanks.priority'), render: (r) => t(`enums.maintenancePriority.${r.priority}`), searchValue: (r) => t(`enums.maintenancePriority.${r.priority}`) },
    {
      id: 'active', label: t('pages.tanks.active'), render: (r) => (
        <Chip label={r.is_active ? t('common.yes') : t('common.no')} size="small" color={r.is_active ? 'success' : 'default'} />
      ), searchValue: (r) => r.is_active ? t('common.yes') : t('common.no'),
    },
    {
      id: 'actions', label: '', render: (r: MaintenanceSchedule) => (
        <Box sx={{ display: 'flex', gap: 0.5 }}>
          <IconButton
            size="small"
            onClick={(e) => { e.stopPropagation(); setEditSchedule(r); setScheduleDialogOpen(true); }}
            aria-label={t('pages.tanks.editSchedule')}
            data-testid={`schedule-edit-${r.key}`}
          >
            <EditIcon fontSize="small" />
          </IconButton>
          <IconButton
            size="small"
            color="error"
            onClick={(e) => { e.stopPropagation(); setDeleteScheduleKey(r.key); }}
            aria-label={t('common.delete')}
            data-testid={`schedule-delete-${r.key}`}
          >
            <DeleteIcon fontSize="small" />
          </IconButton>
        </Box>
      ),
    },
  ];

  if (loading) return <LoadingSkeleton variant="form" />;
  if (error) return <ErrorDisplay error={error} />;
  if (!tank) return <ErrorDisplay error={t('errors.notFound')} />;

  return (
    <Box data-testid="tank-detail-page">
      <UnsavedChangesGuard dirty={isDirty} />
      <Box
        sx={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          mb: 2,
        }}
      >
        <PageTitle title={tank.name} />
        <Button
          variant="outlined"
          color="error"
          startIcon={<DeleteIcon />}
          onClick={() => setDeleteOpen(true)}
          data-testid="tank-delete-button"
        >
          {t('common.delete')}
        </Button>
      </Box>

      <Tabs value={tab} onChange={(_, v) => setTab(v)} sx={{ mb: 2 }} variant="scrollable" scrollButtons="auto">
        <Tab label={t('pages.tanks.tabDetails')} />
        <Tab label={t('pages.tanks.tabStates')} />
        <Tab label={t('pages.tanks.tabMaintenance')} />
        <Tab label={t('pages.tanks.tabSchedules')} />
        <Tab label={t('pages.tanks.tabFills')} />
        <Tab label={t('common.edit')} />
      </Tabs>

      {/* Tab 0: Details */}
      {tab === 0 && (
        <Box>
          {alerts.length > 0 && (
            <Box sx={{ mb: 2 }}>
              {alerts.map((a, i) => (
                <Alert
                  key={i}
                  severity={severityColor[a.severity] ?? 'info'}
                  sx={{ mb: 1 }}
                >
                  {t(`tankAlerts.${a.type}`, { value: a.value, defaultValue: a.message })}
                </Alert>
              ))}
            </Box>
          )}
          <Card sx={{ mb: 2 }}>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                {t('pages.tanks.tabDetails')}
              </Typography>
              <Table size="small" aria-label={t('pages.tanks.tabDetails')}>
                <TableBody>
                  <TableRow>
                    <TableCell component="th">{t('pages.tanks.tankType')}</TableCell>
                    <TableCell>{t(`enums.tankType.${tank.tank_type}`)}</TableCell>
                  </TableRow>
                  <TableRow>
                    <TableCell component="th">{t('pages.tanks.volumeLiters')}</TableCell>
                    <TableCell>{tank.volume_liters} L</TableCell>
                  </TableRow>
                  <TableRow>
                    <TableCell component="th">{t('pages.tanks.material')}</TableCell>
                    <TableCell>{t(`enums.tankMaterial.${tank.material}`)}</TableCell>
                  </TableRow>
                  <TableRow>
                    <TableCell component="th">{t('pages.tanks.site')} / {t('pages.tanks.location')}</TableCell>
                    <TableCell>
                      {siteName && locationName
                        ? `${siteName} / ${locationName}`
                        : '\u2014'}
                    </TableCell>
                  </TableRow>
                  <TableRow>
                    <TableCell component="th">{t('pages.tanks.equipment')}</TableCell>
                    <TableCell>
                      {(() => {
                        const chips = [
                          tank.has_lid && <Chip key="lid" label={t('pages.tanks.hasLid')} size="small" sx={{ mr: 0.5, mb: 0.5 }} />,
                          tank.has_air_pump && <Chip key="air" label={t('pages.tanks.hasAirPump')} size="small" sx={{ mr: 0.5, mb: 0.5 }} />,
                          tank.has_circulation_pump && <Chip key="circ" label={t('pages.tanks.hasCirculationPump')} size="small" sx={{ mr: 0.5, mb: 0.5 }} />,
                          tank.has_heater && <Chip key="heat" label={t('pages.tanks.hasHeater')} size="small" sx={{ mr: 0.5, mb: 0.5 }} />,
                          tank.is_light_proof && <Chip key="light" label={t('pages.tanks.isLightProof')} size="small" sx={{ mr: 0.5, mb: 0.5 }} />,
                          tank.has_uv_sterilizer && <Chip key="uv" label={t('pages.tanks.hasUvSterilizer')} size="small" sx={{ mr: 0.5, mb: 0.5 }} />,
                          tank.has_ozone_generator && <Chip key="ozone" label={t('pages.tanks.hasOzoneGenerator')} size="small" sx={{ mr: 0.5, mb: 0.5 }} />,
                        ].filter(Boolean);
                        return chips.length > 0 ? chips : '\u2014';
                      })()}
                    </TableCell>
                  </TableRow>
                  {tank.notes && (
                    <TableRow>
                      <TableCell component="th">{t('pages.tanks.notes')}</TableCell>
                      <TableCell>{tank.notes}</TableCell>
                    </TableRow>
                  )}
                </TableBody>
              </Table>
            </CardContent>
          </Card>
          {latestState && (
            <Card sx={{ mb: 2 }}>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  {t('pages.tanks.latestState')}
                  <Chip
                    label={t(`pages.tanks.source${latestState.source === 'manual' ? 'Manual' : latestState.source === 'ha_auto' ? 'HaAuto' : latestState.source === 'ha_live' ? 'HaLive' : latestState.source === 'mqtt_auto' ? 'MqttAuto' : 'Manual'}`)}
                    size="small"
                    color={sourceChipColor[latestState.source] ?? 'default'}
                    sx={{ ml: 1 }}
                  />
                </Typography>
                <Table size="small" aria-label={t('pages.tanks.latestState')}>
                  <TableBody>
                    {latestState.ph != null && (
                      <TableRow>
                        <TableCell component="th">pH</TableCell>
                        <TableCell>{latestState.ph}</TableCell>
                      </TableRow>
                    )}
                    {latestState.ec_ms != null && (
                      <TableRow>
                        <TableCell component="th">EC (mS/cm)</TableCell>
                        <TableCell>{latestState.ec_ms}</TableCell>
                      </TableRow>
                    )}
                    {latestState.water_temp_celsius != null && (
                      <TableRow>
                        <TableCell component="th">{t('pages.tanks.waterTemp')}</TableCell>
                        <TableCell>{latestState.water_temp_celsius} °C</TableCell>
                      </TableRow>
                    )}
                    {latestState.fill_level_percent != null && (
                      <TableRow>
                        <TableCell component="th">{t('pages.tanks.fillLevel')}</TableCell>
                        <TableCell>
                          {latestState.fill_level_percent}%
                          {latestState.fill_level_liters != null && ` (${latestState.fill_level_liters} L)`}
                        </TableCell>
                      </TableRow>
                    )}
                    {latestState.dissolved_oxygen_mgl != null && (
                      <TableRow>
                        <TableCell component="th">{t('pages.tanks.dissolvedOxygen')}</TableCell>
                        <TableCell>{latestState.dissolved_oxygen_mgl} mg/L</TableCell>
                      </TableRow>
                    )}
                    {latestState.orp_mv != null && (
                      <TableRow>
                        <TableCell component="th">{t('pages.tanks.orp')}</TableCell>
                        <TableCell>{latestState.orp_mv} mV</TableCell>
                      </TableRow>
                    )}
                    {latestState.recorded_at && (() => {
                      const freshness = getFreshness(latestState.recorded_at);
                      return (
                        <TableRow>
                          <TableCell component="th">{t('pages.tanks.recordedAt')}</TableCell>
                          <TableCell>
                            {new Date(latestState.recorded_at).toLocaleString()}
                            <Chip
                              label={freshness.minutes != null ? t(`pages.tanks.${freshness.key}`, { minutes: freshness.minutes }) : t(`pages.tanks.${freshness.key}`)}
                              size="small"
                              color={freshness.color}
                              variant="outlined"
                              sx={{ ml: 1 }}
                            />
                          </TableCell>
                        </TableRow>
                      );
                    })()}
                  </TableBody>
                </Table>
              </CardContent>
            </Card>
          )}
          {/* Live Query */}
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: liveState ? 2 : 0 }}>
                <Typography variant="h6">{t('pages.tanks.liveValues')}</Typography>
                <Button
                  variant="outlined"
                  size="small"
                  onClick={handleLiveQuery}
                  disabled={liveLoading}
                  startIcon={liveLoading ? <CircularProgress size={16} /> : undefined}
                  data-testid="tank-live-query-button"
                >
                  {t('pages.tanks.liveQuery')}
                </Button>
              </Box>
              {liveState && liveState.source === 'unavailable' && (
                <Alert severity="info" sx={{ mt: 1 }}>{t('pages.tanks.noHaConfigured')}</Alert>
              )}
              {liveState && liveState.source === 'ha_live' && Object.keys(liveState.values).length === 0 && sensors.length === 0 && (
                <Alert severity="info" sx={{ mt: 1 }}>{t('pages.tanks.noSensors')}</Alert>
              )}
              {liveState && liveState.source === 'ha_live' && Object.keys(liveState.values).length > 0 && (
                <>
                  <Table size="small" aria-label={t('pages.tanks.liveValues')}>
                    <TableBody>
                      {Object.entries(liveState.values).map(([metric, entry]) => {
                        const freshness = getFreshness(entry.last_changed);
                        return (
                          <TableRow key={metric}>
                            <TableCell component="th">{metric}{entry.unit ? ` (${entry.unit})` : ''}</TableCell>
                            <TableCell>
                              {entry.value}
                              <Chip
                                label={freshness.minutes != null ? t(`pages.tanks.${freshness.key}`, { minutes: freshness.minutes }) : t(`pages.tanks.${freshness.key}`)}
                                size="small"
                                color={freshness.color}
                                variant="outlined"
                                sx={{ ml: 1 }}
                              />
                            </TableCell>
                          </TableRow>
                        );
                      })}
                    </TableBody>
                  </Table>
                  <Box sx={{ mt: 2, display: 'flex', justifyContent: 'flex-end' }}>
                    <Button
                      variant="contained"
                      onClick={handleAdoptAll}
                      disabled={adoptingAll}
                      startIcon={adoptingAll ? <CircularProgress size={16} /> : undefined}
                      data-testid="tank-adopt-all-button"
                    >
                      {t('pages.tanks.adoptAllReadings')}
                    </Button>
                  </Box>
                </>
              )}
              {liveState && liveState.errors && liveState.errors.length > 0 && (
                <Box sx={{ mt: 1 }}>
                  {liveState.errors.map((err, i) => (
                    <Alert key={i} severity="warning" sx={{ mb: 0.5 }}>
                      {err.entity_id}: {err.error}
                    </Alert>
                  ))}
                </Box>
              )}
            </CardContent>
          </Card>
          {/* Sensors */}
          <Card sx={{ mt: 2 }}>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: sensors.length > 0 ? 2 : 0 }}>
                <Typography variant="h6">{t('pages.tanks.sensors')}</Typography>
                <Button
                  variant="outlined"
                  size="small"
                  onClick={() => { setEditSensor(undefined); setSensorDialogOpen(true); }}
                  data-testid="tank-add-sensor-button"
                >
                  {t('pages.tanks.addSensor')}
                </Button>
              </Box>
              {sensors.length === 0 && (
                <Alert severity="info">{t('pages.tanks.noSensors')}</Alert>
              )}
              {sensors.length > 0 && (
                <Table size="small" aria-label={t('pages.tanks.sensors')}>
                  <TableBody>
                    {sensors.map((s) => (
                      <TableRow key={s.key}>
                        <TableCell>{s.name}</TableCell>
                        <TableCell>{s.metric_type}</TableCell>
                        <TableCell>{s.ha_entity_id || '\u2014'}</TableCell>
                        <TableCell align="right">
                          <Box sx={{ display: 'flex', gap: 0.5, justifyContent: 'flex-end' }}>
                            <IconButton
                              size="small"
                              onClick={() => { setEditSensor(s); setSensorDialogOpen(true); }}
                              aria-label={t('common.edit')}
                            >
                              <EditIcon fontSize="small" />
                            </IconButton>
                            <IconButton
                              size="small"
                              color="error"
                              onClick={() => setDeleteSensorKey(s.key)}
                              aria-label={t('common.delete')}
                            >
                              <DeleteIcon fontSize="small" />
                            </IconButton>
                          </Box>
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              )}
            </CardContent>
          </Card>
        </Box>
      )}

      {/* Tab 1: States */}
      {tab === 1 && (
        <Box>
          <Box sx={{ display: 'flex', justifyContent: 'flex-end', mb: 2 }}>
            <Button
              variant="contained"
              onClick={() => setStateDialogOpen(true)}
              data-testid="tank-record-state-button"
            >
              {t('pages.tanks.recordState')}
            </Button>
          </Box>
          <DataTable
            columns={stateColumns}
            rows={states}
            getRowKey={(r) => r.key}
            tableState={statesTableState}
            variant="simple"
            ariaLabel={t('pages.tanks.tabStates')}
          />
        </Box>
      )}

      {/* Tab 2: Maintenance */}
      {tab === 2 && (
        <Box>
          {dueMaintenances.length > 0 && (
            <Card sx={{ mb: 2 }}>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  {t('pages.tanks.dueMaintenances')}
                </Typography>
                <DataTable
                  columns={dueColumns}
                  rows={dueMaintenances}
                  getRowKey={(r) => r.schedule_key ?? r.maintenance_type}
                  tableState={dueTableState}
                  variant="simple"
                  ariaLabel={t('pages.tanks.dueMaintenances')}
                />
              </CardContent>
            </Card>
          )}
          <Box sx={{ display: 'flex', justifyContent: 'flex-end', mb: 2 }}>
            <Button
              variant="contained"
              onClick={() => setMaintenanceDialogOpen(true)}
              data-testid="tank-log-maintenance-button"
            >
              {t('pages.tanks.logMaintenance')}
            </Button>
          </Box>
          <Typography variant="h6" gutterBottom>
            {t('pages.tanks.maintenanceHistory')}
          </Typography>
          <DataTable
            columns={logColumns}
            rows={maintenanceLogs}
            getRowKey={(r) => r.key}
            tableState={logsTableState}
            variant="simple"
            ariaLabel={t('pages.tanks.maintenanceHistory')}
          />
        </Box>
      )}

      {/* Tab 3: Schedules */}
      {tab === 3 && (
        <Box>
          <Box sx={{ display: 'flex', justifyContent: 'flex-end', mb: 2 }}>
            <Button
              variant="contained"
              onClick={() => { setEditSchedule(undefined); setScheduleDialogOpen(true); }}
              data-testid="tank-create-schedule-button"
            >
              {t('pages.tanks.createSchedule')}
            </Button>
          </Box>
          <DataTable
            columns={scheduleColumns}
            rows={schedules}
            getRowKey={(r) => r.key}
            tableState={schedulesTableState}
            variant="simple"
            ariaLabel={t('pages.tanks.tabSchedules')}
          />
        </Box>
      )}

      {/* Tab 4: Fills */}
      {tab === 4 && (
        <Box>
          <Box sx={{ display: 'flex', justifyContent: 'flex-end', mb: 2 }}>
            <Button
              variant="contained"
              onClick={() => setFillDialogOpen(true)}
              data-testid="tank-record-fill-button"
            >
              {t('pages.tanks.recordFill')}
            </Button>
          </Box>
          <DataTable
            columns={[
              { id: 'filledAt', label: t('pages.tanks.filledAt'), render: (r: TankFillEvent) => r.filled_at ? new Date(r.filled_at).toLocaleString() : '\u2014' },
              { id: 'fillType', label: t('pages.tanks.fillType'), render: (r: TankFillEvent) => t(`enums.fillType.${r.fill_type}`), searchValue: (r: TankFillEvent) => t(`enums.fillType.${r.fill_type}`) },
              { id: 'volume', label: t('pages.tanks.volumeLiters'), render: (r: TankFillEvent) => `${r.volume_liters} L`, align: 'right' as const },
              { id: 'ec', label: 'EC (mS/cm)', render: (r: TankFillEvent) => r.measured_ec_ms != null ? `${r.measured_ec_ms}` : '\u2014', align: 'right' as const },
              { id: 'ph', label: 'pH', render: (r: TankFillEvent) => r.measured_ph ?? '\u2014', align: 'right' as const },
              { id: 'waterSource', label: t('pages.tanks.waterSource'), render: (r: TankFillEvent) => r.water_source ? t(`enums.waterSource.${r.water_source}`) : '\u2014' },
            ]}
            rows={fillEvents}
            getRowKey={(r: TankFillEvent) => r.key}
            tableState={fillsTableState}
            variant="simple"
            ariaLabel={t('pages.tanks.tabFills')}
          />
        </Box>
      )}

      {/* Tab 5: Edit */}
      {tab === 5 && (
        <Box
          component="form"
          onSubmit={handleSubmit(onSave)}
          sx={{ maxWidth: 900, display: 'flex', flexDirection: 'column', gap: 4 }}
        >
          <Typography variant="body2" color="text.secondary">
            {t('pages.tanks.editIntro')}
          </Typography>

          <Card variant="outlined">
            <CardContent component="fieldset" sx={{ border: 'none', p: 0, m: 0, '&:last-child': { pb: 2 }, px: 2, pt: 2 }}>
              <Typography component="legend" variant="h6" sx={{ pt: 1.5, mb: 0.5 }}>
                {t('pages.tanks.sectionIdentification')}
              </Typography>
              <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                {t('pages.tanks.sectionIdentificationDesc')}
              </Typography>
              <FormTextField
                name="name"
                control={control}
                label={t('pages.tanks.name')}
                required
                autoFocus
              />
              <FormRow>
                <FormSelectField
                  name="tank_type"
                  control={control}
                  label={t('pages.tanks.tankType')}
                  options={tankTypes.map((v) => ({
                    value: v,
                    label: t(`enums.tankType.${v}`),
                  }))}
                />
                <FormSelectField
                  name="material"
                  control={control}
                  label={t('pages.tanks.material')}
                  options={materials.map((v) => ({
                    value: v,
                    label: t(`enums.tankMaterial.${v}`),
                  }))}
                />
              </FormRow>
              <FormNumberField
                name="volume_liters"
                control={control}
                label={t('pages.tanks.volumeLiters')}
                helperText={t('pages.tanks.volumeLitersHelper')}
                suffix="L"
                inputMode="decimal"
                min={0.1}
              />
            </CardContent>
          </Card>

          <Card variant="outlined">
            <CardContent component="fieldset" sx={{ border: 'none', p: 0, m: 0, '&:last-child': { pb: 2 }, px: 2, pt: 2 }}>
              <Typography component="legend" variant="h6" sx={{ pt: 1.5, mb: 0.5 }}>
                {t('pages.tanks.sectionLocation')}
              </Typography>
              <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                {t('pages.tanks.sectionLocationDesc')}
              </Typography>
              <FormRow>
                <TextField
                  select
                  label={t('pages.tanks.site')}
                  value={selectedSiteKey}
                  onChange={(e) => handleSiteChange(e.target.value)}
                  fullWidth
                  sx={{ mb: 2 }}
                  data-testid="form-field-site"
                >
                  <MenuItem value="">{'\u2014'}</MenuItem>
                  {sites.map((s) => (
                    <MenuItem key={s.key} value={s.key}>{s.name}</MenuItem>
                  ))}
                </TextField>
                <FormSelectField
                  name="location_key"
                  control={control}
                  label={t('pages.tanks.location')}
                  disabled={!selectedSiteKey}
                  options={[
                    { value: '', label: '\u2014' },
                    ...locations.map((l) => ({ value: l.key, label: l.name })),
                  ]}
                />
              </FormRow>
            </CardContent>
          </Card>

          <Card variant="outlined">
            <CardContent component="fieldset" sx={{ border: 'none', p: 0, m: 0, '&:last-child': { pb: 2 }, px: 2, pt: 2 }}>
              <Typography component="legend" variant="h6" sx={{ pt: 1.5, mb: 0.5 }}>
                {t('pages.tanks.sectionEquipment')}
              </Typography>
              <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                {t('pages.tanks.sectionEquipmentDesc')}
              </Typography>
              <FormRow>
                <FormSwitchField
                  name="has_lid"
                  control={control}
                  label={t('pages.tanks.hasLid')}
                />
                <FormSwitchField
                  name="has_air_pump"
                  control={control}
                  label={t('pages.tanks.hasAirPump')}
                />
              </FormRow>
              <FormRow>
                <FormSwitchField
                  name="has_circulation_pump"
                  control={control}
                  label={t('pages.tanks.hasCirculationPump')}
                />
                <FormSwitchField
                  name="has_heater"
                  control={control}
                  label={t('pages.tanks.hasHeater')}
                />
              </FormRow>
              <FormRow>
                <FormSwitchField
                  name="is_light_proof"
                  control={control}
                  label={t('pages.tanks.isLightProof')}
                />
                <FormSwitchField
                  name="has_uv_sterilizer"
                  control={control}
                  label={t('pages.tanks.hasUvSterilizer')}
                />
              </FormRow>
              <FormSwitchField
                name="has_ozone_generator"
                control={control}
                label={t('pages.tanks.hasOzoneGenerator')}
              />
            </CardContent>
          </Card>

          <Card variant="outlined">
            <CardContent component="fieldset" sx={{ border: 'none', p: 0, m: 0, '&:last-child': { pb: 2 }, px: 2, pt: 2 }}>
              <Typography component="legend" variant="h6" sx={{ pt: 1.5, mb: 0.5 }}>
                {t('pages.tanks.sectionNotes')}
              </Typography>
              <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                {t('pages.tanks.sectionNotesDesc')}
              </Typography>
              <FormTextField
                name="notes"
                control={control}
                label={t('pages.tanks.notes')}
                multiline
                rows={3}
              />
            </CardContent>
          </Card>

          <Typography variant="caption" color="text.secondary">* {t('common.required')}</Typography>
          <FormActions
            onCancel={() => reset()}
            loading={saving}
            disabled={!isDirty}
          />
        </Box>
      )}

      <TankStateCreateDialog
        open={stateDialogOpen}
        onClose={() => setStateDialogOpen(false)}
        tankKey={key ?? ''}
        onCreated={() => {
          setStateDialogOpen(false);
          load();
        }}
      />
      <MaintenanceLogDialog
        open={maintenanceDialogOpen}
        onClose={() => setMaintenanceDialogOpen(false)}
        tankKey={key ?? ''}
        onCreated={() => {
          setMaintenanceDialogOpen(false);
          load();
        }}
      />
      <ConfirmDialog
        open={deleteOpen}
        title={t('common.delete')}
        message={t('common.deleteConfirm', { name: tank.name })}
        onConfirm={onDelete}
        onCancel={() => setDeleteOpen(false)}
        destructive
      />
      <MaintenanceScheduleDialog
        open={scheduleDialogOpen}
        onClose={() => { setScheduleDialogOpen(false); setEditSchedule(undefined); }}
        tankKey={key ?? ''}
        schedule={editSchedule}
        onSaved={() => { setScheduleDialogOpen(false); setEditSchedule(undefined); load(); }}
      />
      <TankFillCreateDialog
        open={fillDialogOpen}
        onClose={() => setFillDialogOpen(false)}
        tankKey={key ?? ''}
        onCreated={() => {
          setFillDialogOpen(false);
          load();
        }}
      />
      <ConfirmDialog
        open={!!deleteScheduleKey}
        title={t('common.delete')}
        message={t('common.deleteConfirm', { name: schedules.find((s) => s.key === deleteScheduleKey)?.maintenance_type ?? '' })}
        onConfirm={onDeleteSchedule}
        onCancel={() => setDeleteScheduleKey(null)}
        destructive
      />
      <SensorCreateDialog
        open={sensorDialogOpen}
        onClose={() => { setSensorDialogOpen(false); setEditSensor(undefined); }}
        context={{ parentType: 'tank', parentKey: key ?? '' }}
        sensor={editSensor}
        onSaved={() => { setSensorDialogOpen(false); setEditSensor(undefined); load(); }}
      />
      <ConfirmDialog
        open={!!deleteSensorKey}
        title={t('common.delete')}
        message={t('pages.tanks.deleteSensorConfirm', { name: sensors.find((s) => s.key === deleteSensorKey)?.name ?? '' })}
        onConfirm={onDeleteSensor}
        onCancel={() => setDeleteSensorKey(null)}
        destructive
      />
    </Box>
  );
}
