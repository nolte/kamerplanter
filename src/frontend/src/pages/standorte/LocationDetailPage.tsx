import { useEffect, useState } from 'react';
import { useParams, useNavigate, Link as RouterLink } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import Box from '@mui/material/Box';
import Button from '@mui/material/Button';
import Typography from '@mui/material/Typography';
import DeleteIcon from '@mui/icons-material/Delete';
import AddIcon from '@mui/icons-material/Add';
import { useForm, useWatch } from 'react-hook-form';
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
import FormTimeField from '@/components/form/FormTimeField';
import FormSwitchField from '@/components/form/FormSwitchField';
import FormActions from '@/components/form/FormActions';
import FormRow from '@/components/form/FormRow';
import UnsavedChangesGuard from '@/components/form/UnsavedChangesGuard';
import MuiBreadcrumbs from '@mui/material/Breadcrumbs';
import Card from '@mui/material/Card';
import CardContent from '@mui/material/CardContent';
import Chip from '@mui/material/Chip';
import Link from '@mui/material/Link';
import WaterDropIcon from '@mui/icons-material/WaterDrop';
import LocationCreateDialog from './LocationCreateDialog';
import SlotCreateDialog from './SlotCreateDialog';
import WateringEventCreateDialog from './WateringEventCreateDialog';
import { useNotification } from '@/hooks/useNotification';
import { useApiError } from '@/hooks/useApiError';
import * as api from '@/api/endpoints/sites';
import * as tankApi from '@/api/endpoints/tanks';
import * as wateringApi from '@/api/endpoints/watering-events';
import type { Location, Slot, Tank, WateringEvent, WateringStats } from '@/api/types';

const timeRegex = /^\d{2}:\d{2}$/;

const schema = z.object({
  name: z.string().min(1),
  site_key: z.string(),
  area_m2: z.number().min(0),
  light_type: z.enum(['natural', 'led', 'hps', 'cmh', 'mixed']),
  irrigation_system: z.enum(['manual', 'drip', 'hydro', 'mist', 'nft', 'ebb_flow']),
  lights_on: z.string().regex(timeRegex).nullable().optional(),
  lights_off: z.string().regex(timeRegex).nullable().optional(),
  use_dynamic_sunrise: z.boolean(),
});

type FormData = z.infer<typeof schema>;

export default function LocationDetailPage() {
  const { key } = useParams<{ key: string }>();
  const { t } = useTranslation();
  const navigate = useNavigate();
  const notification = useNotification();
  const { handleError } = useApiError();
  const [location, setLocation] = useState<Location | null>(null);
  const [slots, setSlots] = useState<Slot[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);
  const [deleteOpen, setDeleteOpen] = useState(false);
  const [slotCreateOpen, setSlotCreateOpen] = useState(false);
  const [wateringEvents, setWateringEvents] = useState<WateringEvent[]>([]);
  const [wateringStats, setWateringStats] = useState<WateringStats | null>(null);
  const [wateringCreateOpen, setWateringCreateOpen] = useState(false);
  const [assignedTank, setAssignedTank] = useState<Tank | null>(null);
  const [childLocations, setChildLocations] = useState<Location[]>([]);
  const [sublocationCreateOpen, setSublocationCreateOpen] = useState(false);
  const [ancestorChain, setAncestorChain] = useState<{ key: string; name: string }[]>([]);
  const [siteName, setSiteName] = useState<string>('');
  const slotTableState = useTableLocalState({ defaultSort: { column: 'slotId', direction: 'asc' } });
  const childTableState = useTableLocalState({ defaultSort: { column: 'name', direction: 'asc' } });
  const wateringTableState = useTableLocalState({ defaultSort: { column: 'wateredAt', direction: 'desc' } });

  const { control, handleSubmit, reset, formState: { isDirty } } = useForm<FormData>({
    resolver: zodResolver(schema),
    defaultValues: {
      name: '',
      site_key: '',
      area_m2: 0,
      light_type: 'natural',
      irrigation_system: 'manual',
      lights_on: null,
      lights_off: null,
      use_dynamic_sunrise: false,
    },
  });

  const lightType = useWatch({ control, name: 'light_type' });
  const isArtificial = lightType === 'led' || lightType === 'hps' || lightType === 'cmh';
  const isNaturalOrMixed = lightType === 'natural' || lightType === 'mixed';

  const load = async () => {
    if (!key) return;
    setLoading(true);
    try {
      const loc = await api.getLocation(key);
      setLocation(loc);
      // Build ancestor breadcrumb chain
      const ancestors: { key: string; name: string }[] = [];
      let current = loc;
      while (current.parent_location_key) {
        try {
          const parent = await api.getLocation(current.parent_location_key);
          ancestors.unshift({ key: parent.key, name: parent.name });
          current = parent;
        } catch {
          break;
        }
      }
      setAncestorChain(ancestors);
      // Fetch site name for breadcrumb
      try {
        const site = await api.getSite(loc.site_key);
        setSiteName(site.name);
      } catch {
        setSiteName('');
      }
      reset({
        name: loc.name,
        site_key: loc.site_key,
        area_m2: loc.area_m2,
        light_type: loc.light_type,
        irrigation_system: loc.irrigation_system,
        lights_on: loc.lights_on,
        lights_off: loc.lights_off,
        use_dynamic_sunrise: loc.use_dynamic_sunrise,
      });
      const [s, children] = await Promise.all([
        api.listSlots(key),
        api.listLocationChildren(key),
      ]);
      setSlots(s);
      setChildLocations(children);
      // Load assigned tank:
      // Primary: Location.tank_key (denormalized).
      // Fallback: find tank whose location_key matches this location.
      if (loc.tank_key) {
        try {
          const t = await tankApi.getTank(loc.tank_key);
          setAssignedTank(t);
        } catch {
          setAssignedTank(null);
        }
      } else {
        try {
          const allTanks = await tankApi.listTanks(0, 200);
          const match = allTanks.find((t) => t.location_key === key);
          setAssignedTank(match ?? null);
        } catch {
          setAssignedTank(null);
        }
      }
      // Load watering events and stats
      try {
        const [we, ws] = await Promise.all([
          wateringApi.getLocationWateringEvents(key),
          wateringApi.getLocationWateringStats(key),
        ]);
        setWateringEvents(we);
        setWateringStats(ws);
      } catch {
        // Watering data may not be available
      }
    } catch (err) {
      setError(String(err));
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { load(); }, [key]); // eslint-disable-line react-hooks/exhaustive-deps

  const onSubmit = async (data: FormData) => {
    if (!key) return;
    try {
      setSaving(true);
      await api.updateLocation(key, {
        ...data,
        lights_on: data.lights_on || undefined,
        lights_off: data.lights_off || undefined,
      });
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
      await api.deleteLocation(key);
      notification.success(t('common.delete'));
      navigate(-1);
    } catch (err) {
      handleError(err);
    }
    setDeleteOpen(false);
  };

  const slotColumns: Column<Slot>[] = [
    { id: 'slotId', label: t('pages.slots.slotId'), render: (r) => r.slot_id },
    { id: 'position', label: t('pages.slots.position'), render: (r) => `(${r.position[0]}, ${r.position[1]})` },
    { id: 'capacity', label: t('pages.slots.capacity'), render: (r) => r.capacity_plants, align: 'right' as const },
    { id: 'occupied', label: t('pages.slots.occupied'), render: (r) => (
      <Chip label={r.currently_occupied ? t('common.yes') : t('common.no')} size="small" color={r.currently_occupied ? 'warning' : 'default'} />
    )},
  ];

  if (loading) return <LoadingSkeleton variant="form" />;
  if (error) return <ErrorDisplay error={error} onRetry={() => navigate(-1)} />;

  return (
    <>
      <UnsavedChangesGuard dirty={isDirty} />

      {/* Dynamic hierarchy breadcrumb */}
      {location && (ancestorChain.length > 0 || location.parent_location_key) && (
        <MuiBreadcrumbs aria-label="location-hierarchy" sx={{ mb: 1 }}>
          {siteName && (
            <Link component={RouterLink} to={`/standorte/sites/${location.site_key}`} underline="hover" color="inherit">
              {siteName}
            </Link>
          )}
          {ancestorChain.map((a) => (
            <Link key={a.key} component={RouterLink} to={`/standorte/locations/${a.key}`} underline="hover" color="inherit">
              {a.name}
            </Link>
          ))}
          <Typography color="text.primary">{location.name}</Typography>
        </MuiBreadcrumbs>
      )}

      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <PageTitle title={location?.name ?? t('entities.location')} />
        <Button color="error" startIcon={<DeleteIcon />} onClick={() => setDeleteOpen(true)}>
          {t('common.delete')}
        </Button>
      </Box>

      <Box component="form" onSubmit={handleSubmit(onSubmit)} sx={{ maxWidth: 900 }}>
        <FormRow>
          <FormTextField name="name" control={control} label={t('pages.locations.name')} required />
          <FormNumberField name="area_m2" control={control} label={t('pages.locations.area')} helperText={t('pages.locations.areaHelper')} min={0} />
        </FormRow>
        <FormRow>
          <FormSelectField
            name="light_type"
            control={control}
            label={t('pages.locations.lightType')}
            options={['natural', 'led', 'hps', 'cmh', 'mixed'].map((v) => ({
              value: v, label: t(`enums.lightType.${v}`),
            }))}
          />
          <FormSelectField
            name="irrigation_system"
            control={control}
            label={t('pages.locations.irrigationSystem')}
            options={['manual', 'drip', 'hydro', 'mist', 'nft', 'ebb_flow'].map((v) => ({
              value: v, label: t(`enums.irrigationSystem.${v}`),
            }))}
          />
        </FormRow>

        {(isArtificial || isNaturalOrMixed) && (
          <Box sx={{ display: 'flex', gap: 2 }}>
            <FormTimeField
              name="lights_on"
              control={control}
              label={t('pages.locations.lightsOn')}
              helperText={t('pages.locations.lightsOnHelper')}
            />
            <FormTimeField
              name="lights_off"
              control={control}
              label={t('pages.locations.lightsOff')}
              helperText={t('pages.locations.lightsOffHelper')}
            />
          </Box>
        )}

        {isNaturalOrMixed && (
          <FormSwitchField
            name="use_dynamic_sunrise"
            control={control}
            label={t('pages.locations.useDynamicSunrise')}
          />
        )}

        <FormActions onCancel={() => navigate(-1)} loading={saving} />
      </Box>

      {/* Assigned Tank */}
      <Box sx={{ mt: 3, maxWidth: 600 }}>
        <Typography variant="subtitle2" color="text.secondary">
          {t('pages.locations.assignedTank')}
        </Typography>
        {assignedTank ? (
          <Chip
            label={`${assignedTank.name} (${assignedTank.volume_liters} L)`}
            size="small"
            color="primary"
            variant="outlined"
            onClick={() => navigate(`/standorte/tanks/${assignedTank.key}`)}
            sx={{ mt: 0.5 }}
          />
        ) : (
          <Typography variant="body2" color="text.secondary" sx={{ mt: 0.5 }}>
            {t('pages.locations.noTank')}
          </Typography>
        )}
      </Box>

      {/* Sub-Locations */}
      <Box sx={{ mt: 4 }}>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
          <Typography variant="h6">{t('pages.locations.sublocations')}</Typography>
          <Button startIcon={<AddIcon />} onClick={() => setSublocationCreateOpen(true)}>
            {t('pages.locations.addSublocation')}
          </Button>
        </Box>
        {childLocations.length === 0 ? (
          <Typography variant="body2" color="text.secondary">
            {t('pages.locations.noSublocations')}
          </Typography>
        ) : (
          <DataTable<Location>
            columns={[
              { id: 'name', label: t('pages.locations.name'), render: (r) => r.name },
              { id: 'locationType', label: t('pages.locations.locationType'), render: (r) => r.location_type_key || '—' },
              { id: 'area', label: t('pages.locations.area'), render: (r) => `${r.area_m2} m²`, align: 'right', searchValue: (r) => String(r.area_m2) },
            ]}
            rows={childLocations}
            getRowKey={(r) => r.key}
            onRowClick={(r) => navigate(`/standorte/locations/${r.key}`)}
            tableState={childTableState}
            ariaLabel={t('pages.locations.sublocations')}
          />
        )}
      </Box>

      <Box sx={{ mt: 4 }}>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
          <Typography variant="h6">{t('pages.slots.title')}</Typography>
          <Button startIcon={<AddIcon />} onClick={() => setSlotCreateOpen(true)}>
            {t('pages.slots.create')}
          </Button>
        </Box>
        <DataTable columns={slotColumns} rows={slots} getRowKey={(r) => r.key} onRowClick={(r) => navigate(`/standorte/slots/${r.key}`)} tableState={slotTableState} ariaLabel={t('pages.slots.title')} />
      </Box>

      {/* Watering Events Section */}
      <Box sx={{ mt: 4 }}>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
          <Typography variant="h6" sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <WaterDropIcon />
            {t('pages.wateringEvents.title')}
          </Typography>
          <Button
            variant="contained"
            startIcon={<AddIcon />}
            onClick={() => setWateringCreateOpen(true)}
            data-testid="create-watering-button"
          >
            {t('pages.wateringEvents.create')}
          </Button>
        </Box>

        {wateringStats && (
          <Box sx={{ display: 'flex', gap: 2, mb: 2, flexWrap: 'wrap' }}>
            <Card sx={{ minWidth: 150 }}>
              <CardContent sx={{ py: 1.5, '&:last-child': { pb: 1.5 } }}>
                <Typography variant="caption" color="text.secondary">
                  {t('pages.wateringEvents.totalEvents')}
                </Typography>
                <Typography variant="h6">{wateringStats.total_events}</Typography>
              </CardContent>
            </Card>
            <Card sx={{ minWidth: 150 }}>
              <CardContent sx={{ py: 1.5, '&:last-child': { pb: 1.5 } }}>
                <Typography variant="caption" color="text.secondary">
                  {t('pages.wateringEvents.totalVolume')}
                </Typography>
                <Typography variant="h6">{wateringStats.total_volume} L</Typography>
              </CardContent>
            </Card>
            {wateringStats.by_method.map((m) => (
              <Card key={m.method} sx={{ minWidth: 150 }}>
                <CardContent sx={{ py: 1.5, '&:last-child': { pb: 1.5 } }}>
                  <Typography variant="caption" color="text.secondary">
                    {t(`enums.applicationMethod.${m.method}`)}
                  </Typography>
                  <Typography variant="h6">{m.count}× / {m.total_volume} L</Typography>
                </CardContent>
              </Card>
            ))}
          </Box>
        )}

        <DataTable<WateringEvent>
          columns={[
            {
              id: 'wateredAt',
              label: t('pages.wateringEvents.wateredAt'),
              render: (r) => r.watered_at ? new Date(r.watered_at).toLocaleString() : '—',
              searchValue: (r) => r.watered_at ? new Date(r.watered_at).toLocaleString() : '',
            },
            {
              id: 'applicationMethod',
              label: t('pages.wateringEvents.applicationMethod'),
              render: (r) => t(`enums.applicationMethod.${r.application_method}`),
              searchValue: (r) => t(`enums.applicationMethod.${r.application_method}`),
            },
            {
              id: 'volume',
              label: t('pages.wateringEvents.volumeLiters'),
              render: (r) => `${r.volume_liters} L`,
              align: 'right',
            },
            {
              id: 'slots',
              label: t('pages.wateringEvents.slotKeys'),
              render: (r) => String(r.slot_keys.length),
              align: 'right',
            },
            {
              id: 'waterSource',
              label: t('pages.wateringEvents.waterSource'),
              render: (r) => r.water_source ? t(`enums.waterSource.${r.water_source}`) : '—',
            },
          ]}
          rows={wateringEvents}
          getRowKey={(r) => r.key}
          tableState={wateringTableState}
          ariaLabel={t('pages.wateringEvents.title')}
        />

        <WateringEventCreateDialog
          open={wateringCreateOpen}
          onClose={() => setWateringCreateOpen(false)}
          onCreated={() => {
            setWateringCreateOpen(false);
            load();
          }}
          slotKeys={slots.map((s) => s.key)}
        />
      </Box>

      {key && (
        <SlotCreateDialog
          locationKey={key}
          open={slotCreateOpen}
          onClose={() => setSlotCreateOpen(false)}
          onCreated={() => { setSlotCreateOpen(false); load(); }}
        />
      )}

      {key && location && (
        <LocationCreateDialog
          siteKey={location.site_key}
          parentLocationKey={key}
          open={sublocationCreateOpen}
          onClose={() => setSublocationCreateOpen(false)}
          onCreated={() => { setSublocationCreateOpen(false); load(); }}
        />
      )}

      <ConfirmDialog
        open={deleteOpen}
        title={t('common.delete')}
        message={t('common.deleteConfirm', { name: location?.name })}
        onConfirm={onDelete}
        onCancel={() => setDeleteOpen(false)}
        destructive
      />
    </>
  );
}
