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
import type { ResolvedPlant, WateringLog } from '@/api/types';
import { formatDateTime, formatNumberWithUnit } from '@/utils/formatting';
import WateringLogCreateDialog from './WateringLogCreateDialog';
import { kamiTanks } from '@/assets/brand/illustrations';

/** Plants shown before the overflow chip takes over, in *both* layouts. */
const MAX_VISIBLE_PLANT_CHIPS = 3;

interface PlantLinkChipsProps {
  plants: ResolvedPlant[];
  /**
   * Test hook for the whole group. The desktop column needs none (its `<td>`
   * already carries `cell-plants`); the mobile card passes `card-field-plants`
   * so the same column id keeps resolving in the card layout.
   */
  testId?: string;
}

/**
 * The plants a watering log was recorded for — one **link** per plant.
 *
 * Shared by the desktop `plants` column and the mobile card so the navigation
 * to the plant exists in both layouts. Rendering it as plain text below the
 * table's breakpoint left phone users with no way from the log to the plant at
 * all, because the surrounding row click leads to the *watering log's* detail
 * page, not to the plant (TC-004-092).
 *
 * `onClick` stops propagation in both layouts: desktop row and mobile card are
 * both click targets of their own, so without it a tap would fire the row
 * navigation and the link navigation at once.
 */
function PlantLinkChips({ plants, testId }: PlantLinkChipsProps) {
  if (plants.length === 0) {
    return (
      <Typography variant="body2" color="text.secondary" data-testid={testId}>{'—'}</Typography>
    );
  }
  const overflow = plants.length - MAX_VISIBLE_PLANT_CHIPS;
  return (
    <Box sx={{ display: 'flex', gap: 0.5, flexWrap: 'wrap' }} data-testid={testId}>
      {plants.slice(0, MAX_VISIBLE_PLANT_CHIPS).map((p) => (
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
          data-testid={`plant-link-${p.key}`}
        />
      ))}
      {overflow > 0 && (
        <Chip label={`+${overflow}`} size="small" variant="outlined" />
      )}
    </Box>
  );
}

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
      render: (r) => formatDateTime(r.logged_at),
      searchValue: (r) => formatDateTime(r.logged_at),
    },
    {
      id: 'plants',
      label: t('pages.wateringLogs.plants'),
      render: (r) => <PlantLinkChips plants={r.resolved_plants ?? []} />,
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
          {formatNumberWithUnit(r.volume_liters, 'L')}
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
          <Typography variant="body2" color="text.secondary">{'—'}</Typography>
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
          {formatNumberWithUnit(r.ec_before, 'mS/cm')}
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
          {formatNumberWithUnit(r.ec_after, 'mS/cm')}
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
        const before = r.ph_before != null ? `${r.ph_before}` : '—';
        const after = r.ph_after != null ? `${r.ph_after}` : '—';
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
          <Typography variant="body2" color="text.secondary">{'—'}</Typography>
        ),
      searchValue: (r) =>
        r.water_source ? t(`enums.waterSource.${r.water_source}`) : '',
    },
  ], [t]);

  /** Hide optional columns when ALL rows have empty/null values. */
  const optionalColumnChecks: Record<string, (r: WateringLog) => boolean> = useMemo(() => ({
    fertilizers: (r) => (r.resolved_fertilizers ?? []).length > 0,
    ecBefore: (r) => r.ec_before != null,
    ecAfter: (r) => r.ec_after != null,
    phBeforeAfter: (r) => r.ph_before != null || r.ph_after != null,
    waterSource: (r) => r.water_source != null,
  }), []);

  const visibleColumns = useMemo(() => {
    if (logs.length === 0) return columns;
    return columns.filter((col) => {
      const check = optionalColumnChecks[col.id as string];
      if (!check) return true; // always show non-optional columns
      return logs.some(check);
    });
  }, [columns, logs, optionalColumnChecks]);

  return (
    <Box data-testid="watering-log-list-page">
      <PageTitle
        title={t('pages.wateringLogs.title')}
        action={
          <Button
            variant="contained"
            startIcon={<AddIcon />}
            onClick={() => setCreateOpen(true)}
            data-testid="create-watering-log-button"
          >
            {t('pages.wateringLogs.create')}
          </Button>
        }
      />
      <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
        {t('pages.wateringLogs.description')}
      </Typography>
      <DataTable
        columns={visibleColumns}
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
          const ferts = r.resolved_fertilizers ?? [];
          return (
            <MobileCard
              title={formatDateTime(r.logged_at)}
              titleId="loggedAt"
              // Keyed chip list (not a plain node): every chip mirrors the
              // column id that addresses the same value on the desktop table,
              // so a reader asks for `applicationMethod` instead of counting
              // DOM positions across a conditional water-source chip. The
              // fertilizer chips share one carrier because the column holds a
              // list — the same shape as its desktop `<td>`.
              chips={[
                {
                  // The plants live in the chip row, not in the subtitle: the
                  // subtitle is a `noWrap` caption `Typography`, which clips
                  // its overflow — links placed there would be cut off and
                  // untappable exactly when there is more than one plant. The
                  // chip row wraps, and it is the same affordance the desktop
                  // column offers.
                  id: 'plants',
                  content: (
                    // The outer carrier deliberately sets **no** `data-testid`:
                    // `MobileCard` only clones `card-chip-plants` onto a chip
                    // whose element carries none. The group hook the readers
                    // resolve first (`card-field-plants`, kept from when the
                    // plants were the subtitle) therefore sits one level in.
                    <Box sx={{ display: 'inline-flex' }}>
                      <PlantLinkChips plants={plants} testId="card-field-plants" />
                    </Box>
                  ),
                },
                {
                  id: 'applicationMethod',
                  content: (
                    <Chip
                      label={t(`enums.applicationMethod.${r.application_method}`)}
                      size="small"
                      variant="outlined"
                    />
                  ),
                },
                ...(r.water_source
                  ? [{
                    id: 'waterSource',
                    content: (
                      <Chip
                        label={t(`enums.waterSource.${r.water_source}`)}
                        size="small"
                        variant="outlined"
                      />
                    ),
                  }]
                  : []),
                ...(ferts.length > 0
                  ? [{
                    id: 'fertilizers',
                    content: (
                      <Box sx={{ display: 'inline-flex', flexWrap: 'wrap', gap: 0.5 }}>
                        {ferts.map((rf, i) => (
                          <Chip key={i} label={rf.name} size="small" variant="outlined" color="secondary" />
                        ))}
                      </Box>
                    ),
                  }]
                  : []),
              ]}
              fields={[
                { id: 'volume', label: t('pages.wateringLogs.volumeLiters'), value: formatNumberWithUnit(r.volume_liters, 'L') },
                ...(r.ec_before != null || r.ec_after != null
                  ? [{ label: 'EC', value: `${r.ec_before != null ? formatNumberWithUnit(r.ec_before, 'mS/cm') : '—'} / ${r.ec_after != null ? formatNumberWithUnit(r.ec_after, 'mS/cm') : '—'}` }]
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
