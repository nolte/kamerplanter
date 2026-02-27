import { useEffect, useState, useCallback } from 'react';
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
import UnsavedChangesGuard from '@/components/form/UnsavedChangesGuard';
import { useNotification } from '@/hooks/useNotification';
import { useApiError } from '@/hooks/useApiError';
import * as tankApi from '@/api/endpoints/tanks';
import type {
  Tank,
  TankState,
  TankAlert,
  MaintenanceLog,
  MaintenanceSchedule,
  DueMaintenance,
} from '@/api/types';
import TankStateCreateDialog from './TankStateCreateDialog';
import MaintenanceLogDialog from './MaintenanceLogDialog';

const tankTypes = ['nutrient', 'irrigation', 'reservoir', 'recirculation'] as const;
const materials = ['plastic', 'stainless_steel', 'glass', 'ibc'] as const;

const editSchema = z.object({
  name: z.string().min(1).max(200),
  tank_type: z.enum(tankTypes),
  volume_liters: z.number().gt(0),
  material: z.enum(materials),
  has_lid: z.boolean(),
  has_air_pump: z.boolean(),
  has_circulation_pump: z.boolean(),
  has_heater: z.boolean(),
  notes: z.string().nullable(),
});

type EditFormData = z.infer<typeof editSchema>;

const severityColor: Record<string, 'error' | 'warning' | 'info'> = {
  critical: 'error',
  high: 'error',
  medium: 'warning',
  low: 'info',
};

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
  const [tab, setTab] = useState(0);
  const [saving, setSaving] = useState(false);
  const [deleteOpen, setDeleteOpen] = useState(false);
  const [stateDialogOpen, setStateDialogOpen] = useState(false);
  const [maintenanceDialogOpen, setMaintenanceDialogOpen] = useState(false);

  const statesTableState = useTableLocalState({ defaultSort: { column: 'recordedAt', direction: 'desc' } });
  const dueTableState = useTableLocalState({ defaultSort: { column: 'nextDue', direction: 'asc' } });
  const logsTableState = useTableLocalState({ defaultSort: { column: 'performedAt', direction: 'desc' } });
  const schedulesTableState = useTableLocalState({ defaultSort: { column: 'type', direction: 'asc' } });

  const {
    control,
    handleSubmit,
    reset,
    formState: { isDirty },
  } = useForm<EditFormData>({
    resolver: zodResolver(editSchema),
    defaultValues: {
      name: '',
      tank_type: 'nutrient',
      volume_liters: 50,
      material: 'plastic',
      has_lid: false,
      has_air_pump: false,
      has_circulation_pump: false,
      has_heater: false,
      notes: null,
    },
  });

  const load = useCallback(async () => {
    if (!key) return;
    setLoading(true);
    try {
      const t = await tankApi.getTank(key);
      setTank(t);
      reset({
        name: t.name,
        tank_type: t.tank_type,
        volume_liters: t.volume_liters,
        material: t.material,
        has_lid: t.has_lid,
        has_air_pump: t.has_air_pump,
        has_circulation_pump: t.has_circulation_pump,
        has_heater: t.has_heater,
        notes: t.notes,
      });
      const [ls, al, st, ml, dm, sc] = await Promise.all([
        tankApi.getLatestState(key),
        tankApi.getAlerts(key),
        tankApi.getStates(key),
        tankApi.getMaintenanceHistory(key),
        tankApi.getDueMaintenances(key),
        tankApi.getSchedules(key),
      ]);
      setLatestState(ls);
      setAlerts(al);
      setStates(st);
      setMaintenanceLogs(ml);
      setDueMaintenances(dm);
      setSchedules(sc);
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
      await tankApi.updateTank(key, data);
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

  // Column definitions for data tables
  const stateColumns: Column<TankState>[] = [
    { id: 'recordedAt', label: t('pages.tanks.recordedAt'), render: (r) => r.recorded_at ? new Date(r.recorded_at).toLocaleString() : '-' },
    { id: 'ph', label: 'pH', render: (r) => r.ph ?? '-', align: 'right' },
    { id: 'ec', label: 'EC (mS)', render: (r) => r.ec_ms ?? '-', align: 'right' },
    { id: 'temp', label: t('pages.tanks.waterTemp'), render: (r) => r.water_temp_celsius != null ? `${r.water_temp_celsius} °C` : '-', align: 'right' },
    { id: 'fillLevel', label: t('pages.tanks.fillLevel'), render: (r) => r.fill_level_percent != null ? `${r.fill_level_percent}%` : '-', align: 'right' },
    { id: 'tds', label: 'TDS (ppm)', render: (r) => r.tds_ppm ?? '-', align: 'right' },
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
    { id: 'performedAt', label: t('pages.tanks.performedAt'), render: (r) => r.performed_at ? new Date(r.performed_at).toLocaleString() : '-' },
    { id: 'performedBy', label: t('pages.tanks.performedBy'), render: (r) => r.performed_by || '-' },
    { id: 'duration', label: t('pages.tanks.duration'), render: (r) => r.duration_minutes != null ? `${r.duration_minutes} min` : '-', align: 'right' },
    { id: 'notes', label: t('pages.tanks.notes'), render: (r) => r.notes || '-' },
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
        >
          {t('common.delete')}
        </Button>
      </Box>

      <Tabs value={tab} onChange={(_, v) => setTab(v)} sx={{ mb: 2 }}>
        <Tab label={t('pages.tanks.tabDetails')} />
        <Tab label={t('pages.tanks.tabStates')} />
        <Tab label={t('pages.tanks.tabMaintenance')} />
        <Tab label={t('pages.tanks.tabSchedules')} />
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
                  {a.message}
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
                    <TableCell component="th">{t('pages.tanks.equipment')}</TableCell>
                    <TableCell>
                      {tank.has_lid && <Chip label={t('pages.tanks.hasLid')} size="small" sx={{ mr: 0.5 }} />}
                      {tank.has_air_pump && <Chip label={t('pages.tanks.hasAirPump')} size="small" sx={{ mr: 0.5 }} />}
                      {tank.has_circulation_pump && <Chip label={t('pages.tanks.hasCirculationPump')} size="small" sx={{ mr: 0.5 }} />}
                      {tank.has_heater && <Chip label={t('pages.tanks.hasHeater')} size="small" sx={{ mr: 0.5 }} />}
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
            <Card>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  {t('pages.tanks.latestState')}
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
                    {latestState.recorded_at && (
                      <TableRow>
                        <TableCell component="th">{t('pages.tanks.recordedAt')}</TableCell>
                        <TableCell>{new Date(latestState.recorded_at).toLocaleString()}</TableCell>
                      </TableRow>
                    )}
                  </TableBody>
                </Table>
              </CardContent>
            </Card>
          )}
        </Box>
      )}

      {/* Tab 1: States */}
      {tab === 1 && (
        <Box>
          <Box sx={{ display: 'flex', justifyContent: 'flex-end', mb: 2 }}>
            <Button
              variant="contained"
              onClick={() => setStateDialogOpen(true)}
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

      {/* Tab 4: Edit */}
      {tab === 4 && (
        <Card>
          <CardContent>
            <form onSubmit={handleSubmit(onSave)}>
              <FormTextField
                name="name"
                control={control}
                label={t('pages.tanks.name')}
                required
              />
              <FormSelectField
                name="tank_type"
                control={control}
                label={t('pages.tanks.tankType')}
                options={tankTypes.map((v) => ({
                  value: v,
                  label: t(`enums.tankType.${v}`),
                }))}
              />
              <FormNumberField
                name="volume_liters"
                control={control}
                label={t('pages.tanks.volumeLiters')}
                min={0.1}
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
              <FormTextField
                name="notes"
                control={control}
                label={t('pages.tanks.notes')}
                multiline
                rows={3}
              />
              <FormActions
                onCancel={() => reset()}
                loading={saving}
                disabled={!isDirty}
              />
            </form>
          </CardContent>
        </Card>
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
      />
    </Box>
  );
}
