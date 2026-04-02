import { useEffect, useState, useMemo } from 'react';
import { useNavigate, Link as RouterLink } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import Button from '@mui/material/Button';
import Box from '@mui/material/Box';
import Chip from '@mui/material/Chip';
import Typography from '@mui/material/Typography';
import AddIcon from '@mui/icons-material/Add';
import SpaIcon from '@mui/icons-material/Spa';
import MobileCard from '@/components/common/MobileCard';
import PageTitle from '@/components/layout/PageTitle';
import DataTable, { type Column } from '@/components/common/DataTable';
import { useAppDispatch, useAppSelector } from '@/store/hooks';
import { fetchWateringLogs } from '@/store/slices/wateringLogsSlice';
import { useTableUrlState } from '@/hooks/useTableState';
import type { WateringLog } from '@/api/types';
import WateringLogCreateDialog from './WateringLogCreateDialog';
import { kamiTanks } from '@/assets/brand/illustrations';

export default function WateringLogListPage() {
  const { t } = useTranslation();
  const dispatch = useAppDispatch();
  const navigate = useNavigate();
  const { logs, loading } = useAppSelector((s) => s.wateringLogs);
  const [createOpen, setCreateOpen] = useState(false);
  const tableState = useTableUrlState({
    defaultSort: { column: 'loggedAt', direction: 'desc' },
  });

  useEffect(() => {
    dispatch(fetchWateringLogs({}));
  }, [dispatch]);

  const columns: Column<WateringLog>[] = useMemo(() => [
    {
      id: 'loggedAt',
      label: t('pages.wateringLogs.loggedAt'),
      render: (r) =>
        r.logged_at ? new Date(r.logged_at).toLocaleString() : '\u2014',
      searchValue: (r) =>
        r.logged_at ? new Date(r.logged_at).toLocaleString() : '',
    },
    {
      id: 'plants',
      label: t('pages.wateringLogs.plants'),
      render: (r) => {
        const plants = r.resolved_plants ?? [];
        if (plants.length === 0) return <Typography variant="body2" color="text.secondary">{'\u2014'}</Typography>;
        return (
          <Box sx={{ display: 'flex', gap: 0.5, flexWrap: 'wrap' }}>
            {plants.slice(0, 3).map((p) => (
              <Chip
                key={p.key}
                icon={<SpaIcon />}
                label={p.name}
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
      searchValue: (r) => (r.resolved_plants ?? []).map((p) => p.name).join(' '),
    },
    {
      id: 'applicationMethod',
      label: t('pages.wateringLogs.applicationMethod'),
      render: (r) => t(`enums.applicationMethod.${r.application_method}`),
      searchValue: (r) => t(`enums.applicationMethod.${r.application_method}`),
    },
    {
      id: 'volume',
      label: t('pages.wateringLogs.volumeLiters'),
      render: (r) => (
        <Typography variant="body2" sx={{ fontFamily: 'monospace' }}>
          {r.volume_liters} L
        </Typography>
      ),
      align: 'right',
      searchValue: (r) => String(r.volume_liters),
    },
    {
      id: 'fertilizers',
      label: t('pages.wateringLogs.fertilizersUsed'),
      hideBelowBreakpoint: 'md',
      render: (r) => {
        const resolved = r.resolved_fertilizers ?? [];
        return resolved.length > 0 ? (
          <Box sx={{ display: 'flex', gap: 0.5, flexWrap: 'wrap' }}>
            {resolved.map((rf, i) => (
              <Chip
                key={i}
                label={rf.name}
                size="small"
                variant="outlined"
                color="secondary"
              />
            ))}
          </Box>
        ) : (
          <Typography variant="body2" color="text.secondary">{'\u2014'}</Typography>
        );
      },
      searchValue: (r) => (r.resolved_fertilizers ?? []).map((rf) => rf.name).join(' '),
    },
    {
      id: 'ecBefore',
      label: t('pages.wateringLogs.ecBefore'),
      hideBelowBreakpoint: 'md',
      render: (r) => (
        <Typography variant="body2" sx={{ fontFamily: 'monospace', whiteSpace: 'nowrap' }}>
          {r.ec_before != null ? r.ec_before : '\u2014'}
          {r.ec_before != null && (
            <Typography component="span" variant="caption" color="text.secondary"> mS/cm</Typography>
          )}
        </Typography>
      ),
      align: 'right',
      searchValue: (r) => (r.ec_before != null ? String(r.ec_before) : ''),
    },
    {
      id: 'ecAfter',
      label: t('pages.wateringLogs.ecAfter'),
      hideBelowBreakpoint: 'md',
      render: (r) => (
        <Typography variant="body2" sx={{ fontFamily: 'monospace', whiteSpace: 'nowrap' }}>
          {r.ec_after != null ? r.ec_after : '\u2014'}
          {r.ec_after != null && (
            <Typography component="span" variant="caption" color="text.secondary"> mS/cm</Typography>
          )}
        </Typography>
      ),
      align: 'right',
      searchValue: (r) => (r.ec_after != null ? String(r.ec_after) : ''),
    },
    {
      id: 'phBeforeAfter',
      label: `${t('pages.wateringLogs.phBefore')} / ${t('pages.wateringLogs.phAfter')}`,
      hideBelowBreakpoint: 'lg',
      render: (r) => {
        const before = r.ph_before != null ? `${r.ph_before}` : '\u2014';
        const after = r.ph_after != null ? `${r.ph_after}` : '\u2014';
        return (
          <Typography variant="body2" sx={{ fontFamily: 'monospace', whiteSpace: 'nowrap' }}>
            {before} / {after}
          </Typography>
        );
      },
      searchValue: (r) => `${r.ph_before ?? ''} ${r.ph_after ?? ''}`,
    },
    {
      id: 'waterSource',
      label: t('pages.wateringLogs.waterSource'),
      hideBelowBreakpoint: 'md',
      render: (r) =>
        r.water_source ? t(`enums.waterSource.${r.water_source}`) : (
          <Typography variant="body2" color="text.secondary">{'\u2014'}</Typography>
        ),
      searchValue: (r) =>
        r.water_source ? t(`enums.waterSource.${r.water_source}`) : '',
    },
  ], [t]);

  return (
    <Box data-testid="watering-log-list-page">
      <Box
        sx={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
        }}
      >
        <PageTitle title={t('pages.wateringLogs.title')} />
        <Button
          variant="contained"
          startIcon={<AddIcon />}
          onClick={() => setCreateOpen(true)}
          data-testid="create-watering-log-button"
        >
          {t('pages.wateringLogs.create')}
        </Button>
      </Box>
      <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
        {t('pages.wateringLogs.description')}
      </Typography>
      <DataTable
        columns={columns}
        rows={logs}
        loading={loading}
        getRowKey={(r) => r.key}
        onRowClick={(r) => navigate(`/giessprotokoll/${r.key}`)}
        emptyActionLabel={t('pages.wateringLogs.create')}
        onEmptyAction={() => setCreateOpen(true)}
        emptyIllustration={kamiTanks}
        tableState={tableState}
        ariaLabel={t('pages.wateringLogs.title')}
        mobileCardRenderer={(r) => {
          const plants = r.resolved_plants ?? [];
          const plantNames = plants.slice(0, 3).map((p) => p.name).join(', ');
          const ferts = r.resolved_fertilizers ?? [];
          return (
            <MobileCard
              title={r.logged_at ? new Date(r.logged_at).toLocaleString() : '\u2014'}
              subtitle={plantNames || undefined}
              chips={
                <>
                  <Chip
                    label={t(`enums.applicationMethod.${r.application_method}`)}
                    size="small"
                    variant="outlined"
                  />
                  {r.water_source && (
                    <Chip
                      label={t(`enums.waterSource.${r.water_source}`)}
                      size="small"
                      variant="outlined"
                    />
                  )}
                  {ferts.map((rf, i) => (
                    <Chip key={i} label={rf.name} size="small" variant="outlined" color="secondary" />
                  ))}
                </>
              }
              fields={[
                { label: t('pages.wateringLogs.volumeLiters'), value: `${r.volume_liters} L` },
                ...(r.ec_before != null || r.ec_after != null
                  ? [{ label: 'EC', value: `${r.ec_before ?? '\u2014'} / ${r.ec_after ?? '\u2014'} mS/cm` }]
                  : []),
              ]}
            />
          );
        }}
      />
      <WateringLogCreateDialog
        open={createOpen}
        onClose={() => setCreateOpen(false)}
        onCreated={() => {
          setCreateOpen(false);
          dispatch(fetchWateringLogs({}));
        }}
      />
    </Box>
  );
}
