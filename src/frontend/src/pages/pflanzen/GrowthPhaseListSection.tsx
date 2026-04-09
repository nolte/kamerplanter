import { useEffect, useState } from 'react';
import { useTranslation } from 'react-i18next';
import { Link as RouterLink } from 'react-router-dom';
import Alert from '@mui/material/Alert';
import AlertTitle from '@mui/material/AlertTitle';
import Box from '@mui/material/Box';
import Link from '@mui/material/Link';
import Typography from '@mui/material/Typography';
import Button from '@mui/material/Button';
import IconButton from '@mui/material/IconButton';
import AddIcon from '@mui/icons-material/Add';
import DeleteIcon from '@mui/icons-material/Delete';
import Chip from '@mui/material/Chip';
import DataTable, { type Column } from '@/components/common/DataTable';
import MobileCard from '@/components/common/MobileCard';
import ConfirmDialog from '@/components/common/ConfirmDialog';
import { useTableLocalState } from '@/hooks/useTableState';
import GrowthPhaseDialog from './GrowthPhaseDialog';
import ProfilesSection from './ProfilesSection';
import { useNotification } from '@/hooks/useNotification';
import { useApiError } from '@/hooks/useApiError';
import * as phasesApi from '@/api/endpoints/phases';
import * as phaseSequenceApi from '@/api/endpoints/phaseSequences';
import type { GrowthPhase, PhaseSequenceEntry } from '@/api/types';

interface Props {
  lifecycleKey: string;
  phaseSequenceKey?: string | null;
  phaseSequenceName?: string | null;
}

/** Unified row type for both legacy GrowthPhase and new PhaseSequenceEntry. */
interface PhaseRow {
  key: string;
  name: string;
  displayName: string;
  sequenceOrder: number;
  durationDays: number;
  wateringIntervalDays: number | null;
  stressTolerance: string;
  isTerminal: boolean;
  allowsHarvest: boolean;
  isOverridden: boolean;
  /** Original GrowthPhase if from legacy source (for edit/delete/profiles). */
  growthPhase: GrowthPhase | null;
}

function fromGrowthPhase(gp: GrowthPhase): PhaseRow {
  return {
    key: gp.key,
    name: gp.name,
    displayName: gp.display_name || gp.name,
    sequenceOrder: gp.sequence_order,
    durationDays: gp.typical_duration_days,
    wateringIntervalDays: gp.watering_interval_days,
    stressTolerance: gp.stress_tolerance,
    isTerminal: gp.is_terminal,
    allowsHarvest: gp.allows_harvest,
    isOverridden: false,
    growthPhase: gp,
  };
}

function fromSequenceEntry(entry: PhaseSequenceEntry, lang: string): PhaseRow {
  const def = entry.phase_definition;
  const displayName = def
    ? ((lang === 'de' ? def.display_name_de : def.display_name) || def.name)
    : entry.phase_definition_key;
  return {
    key: entry.key,
    name: def?.name ?? entry.phase_definition_key,
    displayName,
    sequenceOrder: entry.sequence_order,
    durationDays: entry.effective_duration_days,
    wateringIntervalDays: def?.watering_interval_days ?? null,
    stressTolerance: def?.stress_tolerance ?? 'none',
    isTerminal: entry.is_terminal,
    allowsHarvest: entry.allows_harvest,
    isOverridden: entry.override_duration_days != null,
    growthPhase: null,
  };
}

export default function GrowthPhaseListSection({ lifecycleKey, phaseSequenceKey, phaseSequenceName }: Props) {
  const { t, i18n } = useTranslation();
  const lang = i18n.language;
  const notification = useNotification();
  const { handleError } = useApiError();
  const [rows, setRows] = useState<PhaseRow[]>([]);
  const [loading, setLoading] = useState(false);
  const [dialogOpen, setDialogOpen] = useState(false);
  const [editPhase, setEditPhase] = useState<GrowthPhase | null>(null);
  const [deleteTarget, setDeleteTarget] = useState<PhaseRow | null>(null);
  const [selectedPhase, setSelectedPhase] = useState<PhaseRow | null>(null);
  const tableState = useTableLocalState({ defaultSort: { column: 'order', direction: 'asc' } });

  const isManaged = !!phaseSequenceKey;

  const load = async () => {
    setLoading(true);
    try {
      if (phaseSequenceKey) {
        // New system: load from phase sequence
        const seq = await phaseSequenceApi.getPhaseSequence(phaseSequenceKey);
        const sorted = [...seq.entries].sort((a, b) => a.sequence_order - b.sequence_order);
        setRows(sorted.map((e) => fromSequenceEntry(e, lang)));
      } else {
        // Legacy: load from growth phases
        const items = await phasesApi.listGrowthPhases(lifecycleKey);
        setRows(items.sort((a, b) => a.sequence_order - b.sequence_order).map(fromGrowthPhase));
      }
    } catch (err) {
      handleError(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { load(); }, [lifecycleKey, phaseSequenceKey]); // eslint-disable-line react-hooks/exhaustive-deps

  const onDelete = async () => {
    if (!deleteTarget?.growthPhase) return;
    try {
      await phasesApi.deleteGrowthPhase(deleteTarget.growthPhase.key);
      notification.success(t('common.delete'));
      load();
    } catch (err) {
      handleError(err);
    }
    setDeleteTarget(null);
  };

  const columns: Column<PhaseRow>[] = [
    { id: 'order', label: '#', width: 50, render: (r) => r.sequenceOrder, align: 'right' as const },
    {
      id: 'name',
      label: t('pages.growthPhases.name'),
      render: (r) => (
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          {r.displayName}
          {r.isOverridden && (
            <Chip label={t('pages.phaseSequences.overrideIndicator')} size="small" variant="outlined" color="info" />
          )}
        </Box>
      ),
    },
    { id: 'duration', label: t('pages.growthPhases.duration'), render: (r) => `${r.durationDays}d`, align: 'right' as const, searchValue: (r: PhaseRow) => String(r.durationDays) },
    {
      id: 'watering',
      label: t('pages.growthPhases.wateringInterval'),
      render: (r) => r.wateringIntervalDays != null ? `${r.wateringIntervalDays}d` : '\u2014',
      align: 'right' as const,
      searchValue: (r: PhaseRow) => r.wateringIntervalDays != null ? String(r.wateringIntervalDays) : '',
    },
    {
      id: 'stress',
      label: t('pages.growthPhases.stressTolerance'),
      render: (r) => t(`enums.stressTolerance.${r.stressTolerance}`),
      searchValue: (r: PhaseRow) => t(`enums.stressTolerance.${r.stressTolerance}`),
    },
    {
      id: 'flags',
      label: '',
      render: (r) => (
        <Box sx={{ display: 'flex', gap: 0.5 }}>
          {r.isTerminal && <Chip label={t('pages.growthPhases.isTerminal')} size="small" color="warning" />}
          {r.allowsHarvest && <Chip label={t('pages.growthPhases.allowsHarvest')} size="small" color="success" />}
        </Box>
      ),
      searchValue: (r: PhaseRow) => [
        r.isTerminal ? t('pages.growthPhases.isTerminal') : '',
        r.allowsHarvest ? t('pages.growthPhases.allowsHarvest') : '',
      ].filter(Boolean).join(' '),
    },
    // Actions only for legacy phases (not managed by sequence)
    ...(!isManaged ? [{
      id: 'actions',
      label: t('common.actions'),
      width: 120,
      sortable: false,
      searchable: false,
      render: (r: PhaseRow) => (
        <Box>
          <Button size="small" onClick={(e: React.MouseEvent) => { e.stopPropagation(); setSelectedPhase(r); }}>
            {t('entities.profile')}
          </Button>
          <IconButton size="small" aria-label={t('common.delete')} onClick={(e: React.MouseEvent) => { e.stopPropagation(); setDeleteTarget(r); }}>
            <DeleteIcon fontSize="small" />
          </IconButton>
        </Box>
      ),
    } as Column<PhaseRow>] : []),
  ];

  return (
    <Box sx={{ mt: 3 }}>
      {isManaged && (
        <Alert severity="info" sx={{ mb: 2 }}>
          <AlertTitle>
            <Link component={RouterLink} to={`/phasen/ablaeufe/${phaseSequenceKey}`} underline="hover" color="inherit">
              {phaseSequenceName || t('pages.phaseSequences.phaseSequence')}
            </Link>
          </AlertTitle>
          {t('pages.phases.managedBySequence')}
        </Alert>
      )}
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
        <Typography variant="h6">{t('pages.growthPhases.title')}</Typography>
        {!isManaged && (
          <Button startIcon={<AddIcon />} onClick={() => { setEditPhase(null); setDialogOpen(true); }}>
            {t('pages.growthPhases.create')}
          </Button>
        )}
      </Box>

      <DataTable
        columns={columns}
        rows={rows}
        loading={loading}
        onRowClick={isManaged ? undefined : (r) => { if (r.growthPhase) { setEditPhase(r.growthPhase); setDialogOpen(true); } }}
        getRowKey={(r) => r.key}
        tableState={tableState}
        ariaLabel={t('pages.growthPhases.title')}
        mobileCardRenderer={(r) => (
          <MobileCard
            title={r.displayName}
            subtitle={`#${r.sequenceOrder} \u2014 ${r.durationDays}d`}
            chips={
              <>
                {r.isTerminal && <Chip label={t('pages.growthPhases.isTerminal')} size="small" color="warning" />}
                {r.allowsHarvest && <Chip label={t('pages.growthPhases.allowsHarvest')} size="small" color="success" />}
                {r.isOverridden && <Chip label={t('pages.phaseSequences.overrideIndicator')} size="small" variant="outlined" color="info" />}
              </>
            }
            fields={[
              { label: t('pages.growthPhases.stressTolerance'), value: t(`enums.stressTolerance.${r.stressTolerance}`) },
              ...(r.wateringIntervalDays != null ? [{ label: t('pages.growthPhases.wateringInterval'), value: `${r.wateringIntervalDays}d` }] : []),
            ]}
          />
        )}
      />

      {/* Legend */}
      {rows.length > 0 && (
        <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 2, mt: 1.5, px: 1 }}>
          {rows.some((r) => r.isTerminal) && (
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
              <Chip label={t('pages.growthPhases.isTerminal')} size="small" color="warning" />
              <Typography variant="caption" color="text.secondary">
                {t('pages.growthPhases.isTerminalHelper')}
              </Typography>
            </Box>
          )}
          {rows.some((r) => r.allowsHarvest) && (
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
              <Chip label={t('pages.growthPhases.allowsHarvest')} size="small" color="success" />
              <Typography variant="caption" color="text.secondary">
                {t('pages.growthPhases.allowsHarvestHelper')}
              </Typography>
            </Box>
          )}
          {rows.some((r) => r.isOverridden) && (
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
              <Chip label={t('pages.phaseSequences.overrideIndicator')} size="small" variant="outlined" color="info" />
              <Typography variant="caption" color="text.secondary">
                {t('pages.growthPhases.overriddenHelper')}
              </Typography>
            </Box>
          )}
        </Box>
      )}

      {!isManaged && (
        <>
          <GrowthPhaseDialog
            lifecycleKey={lifecycleKey}
            phase={editPhase}
            open={dialogOpen}
            onClose={() => setDialogOpen(false)}
            onSaved={() => { setDialogOpen(false); load(); }}
          />

          <ConfirmDialog
            open={!!deleteTarget}
            title={t('common.delete')}
            message={t('common.deleteConfirm', { name: deleteTarget?.name })}
            onConfirm={onDelete}
            onCancel={() => setDeleteTarget(null)}
            destructive
          />
        </>
      )}

      {selectedPhase?.growthPhase && (
        <ProfilesSection
          phaseKey={selectedPhase.growthPhase.key}
          phaseName={selectedPhase.displayName}
        />
      )}
    </Box>
  );
}
