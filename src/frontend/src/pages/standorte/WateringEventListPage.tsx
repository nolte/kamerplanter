import { useEffect, useState, useCallback, useMemo } from 'react';
import { useTranslation } from 'react-i18next';
import { Link as RouterLink } from 'react-router-dom';
import Button from '@mui/material/Button';
import Box from '@mui/material/Box';
import Chip from '@mui/material/Chip';
import Dialog from '@mui/material/Dialog';
import useMediaQuery from '@mui/material/useMediaQuery';
import { useTheme } from '@mui/material/styles';
import DialogTitle from '@mui/material/DialogTitle';
import DialogContent from '@mui/material/DialogContent';
import DialogActions from '@mui/material/DialogActions';
import Typography from '@mui/material/Typography';
import Divider from '@mui/material/Divider';
import Link from '@mui/material/Link';
import Table from '@mui/material/Table';
import TableBody from '@mui/material/TableBody';
import TableCell from '@mui/material/TableCell';
import TableHead from '@mui/material/TableHead';
import TableRow from '@mui/material/TableRow';
import AddIcon from '@mui/icons-material/Add';
import SpaIcon from '@mui/icons-material/Spa';
import MobileCard from '@/components/common/MobileCard';
import PageTitle from '@/components/layout/PageTitle';
import DataTable, { type Column } from '@/components/common/DataTable';
import { useAppDispatch, useAppSelector } from '@/store/hooks';
import { fetchWateringEvents } from '@/store/slices/wateringEventsSlice';
import { useTableUrlState } from '@/hooks/useTableState';
import type { WateringEvent, PlantInstance } from '@/api/types';
import * as plantApi from '@/api/endpoints/plantInstances';
import WateringEventCreateDialog from './WateringEventCreateDialog';
import { kamiTanks } from '@/assets/brand/illustrations';

// ── Plant resolution cache ─────────────────────────────────────────

/** Resolves plants from plant_keys on WateringEvents. */
function usePlantResolver(events: WateringEvent[]) {
  const [keyPlantMap, setKeyPlantMap] = useState<Map<string, PlantInstance>>(new Map());

  const hasEvents = events.length > 0;

  useEffect(() => {
    if (!hasEvents) return;
    let cancelled = false;

    async function resolve() {
      const plants = await plantApi.listPlantInstances(0, 500);
      if (cancelled) return;
      const byKey = new Map<string, PlantInstance>();
      for (const p of plants) {
        byKey.set(p.key, p);
      }
      setKeyPlantMap(byKey);
    }

    resolve().catch(() => {});
    return () => { cancelled = true; };
  }, [hasEvents]);

  const getPlantsForEvent = useCallback(
    (event: WateringEvent): PlantInstance[] => {
      const result: PlantInstance[] = [];
      for (const pk of event.plant_keys) {
        const p = keyPlantMap.get(pk);
        if (p) result.push(p);
      }
      return result;
    },
    [keyPlantMap],
  );

  return { getPlantsForEvent };
}

// ── Detail Dialog ──────────────────────────────────────────────────

function InfoRow({ label, value }: { label: string; value: React.ReactNode }) {
  if (value == null) return null;
  return (
    <Box sx={{ display: 'flex', justifyContent: 'space-between', py: 0.5 }}>
      <Typography variant="body2" color="text.secondary">{label}</Typography>
      <Typography variant="body2">{value}</Typography>
    </Box>
  );
}

interface DetailDialogProps {
  event: WateringEvent | null;
  open: boolean;
  onClose: () => void;
  getPlantsForEvent: (event: WateringEvent) => PlantInstance[];
}

function WateringEventDetailDialog({ event, open, onClose, getPlantsForEvent }: DetailDialogProps) {
  const theme = useTheme();
  const fullScreen = useMediaQuery(theme.breakpoints.down('sm'));
  const { t } = useTranslation();

  if (!event) return null;

  const plants = getPlantsForEvent(event);

  return (
    <Dialog fullScreen={fullScreen} open={open} onClose={onClose} maxWidth="sm" fullWidth>
      <DialogTitle>{t('pages.wateringEvents.detail')}</DialogTitle>
      <DialogContent dividers>
        {/* Plants linked via slots */}
        {plants.length > 0 && (
          <Box sx={{ mb: 2 }}>
            <Typography variant="subtitle2" color="text.secondary" sx={{ mb: 0.5 }}>
              {t('pages.wateringEvents.plants')}
            </Typography>
            <Box sx={{ display: 'flex', gap: 0.5, flexWrap: 'wrap' }}>
              {plants.map((p) => (
                <Chip
                  key={p.key}
                  icon={<SpaIcon />}
                  label={p.plant_name || p.instance_id}
                  size="small"
                  component={RouterLink}
                  to={`/pflanzen/plant-instances/${p.key}`}
                  clickable
                  color="success"
                  variant="outlined"
                />
              ))}
            </Box>
          </Box>
        )}
        {plants.length === 0 && (
          <Typography variant="body2" color="text.secondary" sx={{ mb: 2, fontStyle: 'italic' }}>
            {t('pages.wateringEvents.noPlantsInSlot')}
          </Typography>
        )}

        <Divider sx={{ mb: 1.5 }} />

        {/* Basic info */}
        <InfoRow
          label={t('pages.wateringEvents.wateredAt')}
          value={event.watered_at ? new Date(event.watered_at).toLocaleString() : '—'}
        />
        <InfoRow
          label={t('pages.wateringEvents.applicationMethod')}
          value={t(`enums.applicationMethod.${event.application_method}`)}
        />
        <InfoRow
          label={t('pages.wateringEvents.volumeLiters')}
          value={`${event.volume_liters} L`}
        />
        <InfoRow
          label={t('pages.wateringEvents.waterSource')}
          value={event.water_source ? t(`enums.waterSource.${event.water_source}`) : null}
        />
        {event.is_supplemental && (
          <InfoRow
            label={t('pages.wateringEvents.isSupplemental')}
            value={<Chip label={t('common.yes')} size="small" color="info" />}
          />
        )}
        <InfoRow
          label={t('pages.wateringEvents.performedBy')}
          value={event.performed_by}
        />
        {event.channel_id && (
          <InfoRow label={t('pages.wateringEvents.channelId')} value={event.channel_id} />
        )}

        {/* EC / pH section */}
        {(event.target_ec != null || event.target_ph != null || event.measured_ec != null || event.measured_ph != null) && (
          <>
            <Divider sx={{ my: 1.5 }} />
            <Typography variant="subtitle2" color="text.secondary" sx={{ mb: 0.5 }}>
              {t('pages.wateringEvents.sectionTarget')} / {t('pages.wateringEvents.sectionMeasured')}
            </Typography>
            <Box sx={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 0.5 }}>
              <InfoRow label={t('pages.wateringEvents.targetEc')} value={event.target_ec != null ? `${event.target_ec} mS/cm` : null} />
              <InfoRow label={t('pages.wateringEvents.measuredEc')} value={event.measured_ec != null ? `${event.measured_ec} mS/cm` : null} />
              <InfoRow label={t('pages.wateringEvents.targetPh')} value={event.target_ph} />
              <InfoRow label={t('pages.wateringEvents.measuredPh')} value={event.measured_ph} />
            </Box>
          </>
        )}

        {/* Runoff */}
        {(event.runoff_ec != null || event.runoff_ph != null) && (
          <>
            <Divider sx={{ my: 1.5 }} />
            <Typography variant="subtitle2" color="text.secondary" sx={{ mb: 0.5 }}>
              {t('pages.wateringEvents.sectionRunoff')}
            </Typography>
            <InfoRow label={t('pages.wateringEvents.runoffEc')} value={event.runoff_ec != null ? `${event.runoff_ec} mS/cm` : null} />
            <InfoRow label={t('pages.wateringEvents.runoffPh')} value={event.runoff_ph} />
          </>
        )}

        {/* Fertilizers used */}
        {event.fertilizers_used.length > 0 && (
          <>
            <Divider sx={{ my: 1.5 }} />
            <Typography variant="subtitle2" color="text.secondary" sx={{ mb: 0.5 }}>
              {t('pages.wateringEvents.fertilizersUsed')}
            </Typography>
            <Table size="small">
              <TableHead>
                <TableRow>
                  <TableCell>{t('pages.wateringEvents.productName')}</TableCell>
                  <TableCell align="right">{t('pages.wateringEvents.mlPerLiter')}</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {event.fertilizers_used.map((f, i) => (
                  <TableRow key={i}>
                    <TableCell>{f.product_name}</TableCell>
                    <TableCell align="right">{f.ml_per_liter}</TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </>
        )}

        {/* Plant keys */}
        <Divider sx={{ my: 1.5 }} />
        <Typography variant="subtitle2" color="text.secondary" sx={{ mb: 0.5 }}>
          {t('pages.wateringEvents.plantKeys')}
        </Typography>
        <Box sx={{ display: 'flex', gap: 0.5, flexWrap: 'wrap' }}>
          {event.plant_keys.map((pk) => (
            <Chip key={pk} label={pk} size="small" variant="outlined" />
          ))}
        </Box>

        {/* Notes */}
        {event.notes && (
          <>
            <Divider sx={{ my: 1.5 }} />
            <Typography variant="subtitle2" color="text.secondary" sx={{ mb: 0.5 }}>
              {t('pages.wateringEvents.notes')}
            </Typography>
            <Typography variant="body2" sx={{ whiteSpace: 'pre-wrap' }}>
              {event.notes}
            </Typography>
          </>
        )}

        {/* Nutrient plan link */}
        {event.nutrient_plan_key && (
          <>
            <Divider sx={{ my: 1.5 }} />
            <InfoRow
              label={t('pages.wateringEvents.nutrientPlan')}
              value={
                <Link component={RouterLink} to={`/duengung/plans/${event.nutrient_plan_key}`} underline="hover">
                  {event.nutrient_plan_key}
                </Link>
              }
            />
          </>
        )}

        {event.created_at && (
          <>
            <Divider sx={{ my: 1.5 }} />
            <InfoRow
              label={t('pages.wateringEvents.createdAt')}
              value={new Date(event.created_at).toLocaleString()}
            />
          </>
        )}
      </DialogContent>
      <DialogActions>
        <Button onClick={onClose}>{t('common.close')}</Button>
      </DialogActions>
    </Dialog>
  );
}

// ── Main Page ──────────────────────────────────────────────────────

export default function WateringEventListPage() {
  const { t } = useTranslation();
  const dispatch = useAppDispatch();
  const { events, loading } = useAppSelector((s) => s.wateringEvents);
  const [createOpen, setCreateOpen] = useState(false);
  const [selectedEvent, setSelectedEvent] = useState<WateringEvent | null>(null);
  const tableState = useTableUrlState({
    defaultSort: { column: 'wateredAt', direction: 'desc' },
  });

  useEffect(() => {
    dispatch(fetchWateringEvents({}));
  }, [dispatch]);

  const { getPlantsForEvent } = usePlantResolver(events);

  const columns: Column<WateringEvent>[] = useMemo(() => [
    {
      id: 'wateredAt',
      label: t('pages.wateringEvents.wateredAt'),
      render: (r) =>
        r.watered_at ? new Date(r.watered_at).toLocaleString() : '—',
      searchValue: (r) =>
        r.watered_at ? new Date(r.watered_at).toLocaleString() : '',
    },
    {
      id: 'plants',
      label: t('pages.wateringEvents.plants'),
      render: (r) => {
        const plants = getPlantsForEvent(r);
        if (plants.length === 0) return <Typography variant="body2" color="text.secondary">—</Typography>;
        return (
          <Box sx={{ display: 'flex', gap: 0.5, flexWrap: 'wrap' }}>
            {plants.slice(0, 3).map((p) => (
              <Chip
                key={p.key}
                icon={<SpaIcon />}
                label={p.plant_name || p.instance_id}
                size="small"
                color="success"
                variant="outlined"
                onClick={(e) => e.stopPropagation()}
                component={RouterLink}
                to={`/pflanzen/plant-instances/${p.key}`}
              />
            ))}
            {plants.length > 3 && (
              <Chip label={`+${plants.length - 3}`} size="small" variant="outlined" />
            )}
          </Box>
        );
      },
      searchValue: (r) => getPlantsForEvent(r).map((p) => p.plant_name || p.instance_id).join(' '),
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
      searchValue: (r) => String(r.volume_liters),
    },
    {
      id: 'ecPh',
      label: 'EC / pH',
      render: (r) => {
        const parts: string[] = [];
        if (r.measured_ec != null) parts.push(`EC ${r.measured_ec}`);
        else if (r.target_ec != null) parts.push(`EC ${r.target_ec}*`);
        if (r.measured_ph != null) parts.push(`pH ${r.measured_ph}`);
        else if (r.target_ph != null) parts.push(`pH ${r.target_ph}*`);
        return parts.length > 0 ? parts.join(' | ') : '—';
      },
    },
    {
      id: 'waterSource',
      label: t('pages.wateringEvents.waterSource'),
      render: (r) =>
        r.water_source ? t(`enums.waterSource.${r.water_source}`) : '—',
      searchValue: (r) =>
        r.water_source ? t(`enums.waterSource.${r.water_source}`) : '',
    },
    {
      id: 'fertilizers',
      label: t('pages.wateringEvents.fertilizersUsed'),
      render: (r) =>
        r.fertilizers_used.length > 0
          ? r.fertilizers_used.map((f) => f.product_name).join(', ')
          : '—',
      searchValue: (r) => r.fertilizers_used.map((f) => f.product_name).join(' '),
    },
  ], [t, getPlantsForEvent]);

  return (
    <Box data-testid="watering-event-list-page">
      <PageTitle
        title={t('pages.wateringEvents.title')}
        action={
          <Button
            variant="contained"
            startIcon={<AddIcon />}
            onClick={() => setCreateOpen(true)}
            data-testid="create-button"
          >
            {t('pages.wateringEvents.create')}
          </Button>
        }
      />
      <DataTable
        columns={columns}
        rows={events}
        loading={loading}
        getRowKey={(r) => r.key}
        onRowClick={(r) => setSelectedEvent(r)}
        emptyActionLabel={t('pages.wateringEvents.create')}
        onEmptyAction={() => setCreateOpen(true)}
        emptyIllustration={kamiTanks}
        tableState={tableState}
        ariaLabel={t('pages.wateringEvents.title')}
        mobileCardRenderer={(r) => {
          const plants = getPlantsForEvent(r);
          const ecPhParts: string[] = [];
          if (r.measured_ec != null) ecPhParts.push(`EC ${r.measured_ec}`);
          else if (r.target_ec != null) ecPhParts.push(`EC ${r.target_ec}*`);
          if (r.measured_ph != null) ecPhParts.push(`pH ${r.measured_ph}`);
          else if (r.target_ph != null) ecPhParts.push(`pH ${r.target_ph}*`);
          return (
            <MobileCard
              title={r.watered_at ? new Date(r.watered_at).toLocaleString() : '\u2014'}
              subtitle={plants.length > 0 ? plants.map((p) => p.plant_name || p.instance_id).join(', ') : undefined}
              chips={<Chip label={t(`enums.applicationMethod.${r.application_method}`)} size="small" />}
              fields={[
                { label: t('pages.wateringEvents.volumeLiters'), value: `${r.volume_liters} L` },
                ...(ecPhParts.length > 0 ? [{ label: 'EC / pH', value: ecPhParts.join(' | ') }] : []),
                ...(r.water_source ? [{ label: t('pages.wateringEvents.waterSource'), value: t(`enums.waterSource.${r.water_source}`) }] : []),
              ]}
            />
          );
        }}
      />
      <WateringEventCreateDialog
        open={createOpen}
        onClose={() => setCreateOpen(false)}
        onCreated={() => {
          setCreateOpen(false);
          dispatch(fetchWateringEvents({}));
        }}
      />
      <WateringEventDetailDialog
        event={selectedEvent}
        open={selectedEvent != null}
        onClose={() => setSelectedEvent(null)}
        getPlantsForEvent={getPlantsForEvent}
      />
    </Box>
  );
}
