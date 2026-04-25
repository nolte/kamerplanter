import { useEffect, useState, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import Box from '@mui/material/Box';
import Button from '@mui/material/Button';
import Chip from '@mui/material/Chip';
import IconButton from '@mui/material/IconButton';
import Tooltip from '@mui/material/Tooltip';
import Typography from '@mui/material/Typography';
import AddIcon from '@mui/icons-material/Add';
import DeleteIcon from '@mui/icons-material/Delete';
import EditIcon from '@mui/icons-material/Edit';
import PageTitle from '@/components/layout/PageTitle';
import ConfirmDialog from '@/components/common/ConfirmDialog';
import OriginChip from '@/components/common/OriginChip';
import ErrorDisplay from '@/components/common/ErrorDisplay';
import MobileCard from '@/components/common/MobileCard';
import DataTable, { type Column } from '@/components/common/DataTable';
import { useTableUrlState } from '@/hooks/useTableState';
import { useNotification } from '@/hooks/useNotification';
import { useApiError } from '@/hooks/useApiError';
import * as phaseSequenceApi from '@/api/endpoints/phaseSequences';
import type { PhaseDefinition } from '@/api/types';
import { kamiPhaseGermination } from '@/assets/brand/illustrations';
import PhaseDefinitionDialog from './PhaseDefinitionDialog';

export default function PhaseDefinitionListPage() {
  const navigate = useNavigate();
  const { t, i18n } = useTranslation();
  const lang = i18n.language;
  const notification = useNotification();
  const { handleError } = useApiError();
  const tableState = useTableUrlState({
    defaultSort: { column: 'name', direction: 'asc' },
    pageSizeStorageKey: 'phaseDefinitions.pageSize',
  });

  const [definitions, setDefinitions] = useState<PhaseDefinition[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [dialogOpen, setDialogOpen] = useState(false);
  const [editDefinition, setEditDefinition] = useState<PhaseDefinition | undefined>(
    undefined,
  );
  const [deleteKey, setDeleteKey] = useState<string | null>(null);

  const loadDefinitions = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await phaseSequenceApi.listPhaseDefinitions(0, 200);
      setDefinitions(data);
    } catch (err) {
      setError(t('errors.server'));
      handleError(err);
    } finally {
      setLoading(false);
    }
  }, [t, handleError]);

  useEffect(() => {
    loadDefinitions();
  }, [loadDefinitions]);

  const handleDelete = async () => {
    if (!deleteKey) return;
    try {
      await phaseSequenceApi.deletePhaseDefinition(deleteKey);
      notification.success(t('pages.phaseSequences.definitionDeleted'));
      setDeleteKey(null);
      loadDefinitions();
    } catch (err) {
      handleError(err);
    }
  };

  const handleOpenCreate = () => {
    setEditDefinition(undefined);
    setDialogOpen(true);
  };

  const handleOpenEdit = (def: PhaseDefinition) => {
    setEditDefinition(def);
    setDialogOpen(true);
  };

  const handleDialogSaved = () => {
    setDialogOpen(false);
    setEditDefinition(undefined);
    loadDefinitions();
  };

  const deleteTarget = definitions.find((d) => d.key === deleteKey);

  const getDisplayName = (def: PhaseDefinition): string =>
    (lang === 'de' ? def.display_name_de : def.display_name) || def.name;

  const columns: Column<PhaseDefinition>[] = [
    {
      id: 'name',
      label: t('common.name'),
      render: (def) => (
        <Box>
          <Typography variant="body2" sx={{ fontWeight: 500 }}>
            {getDisplayName(def)}
          </Typography>
          <Typography variant="caption" color="text.secondary">
            {def.name}
          </Typography>
        </Box>
      ),
      searchValue: (def) => `${getDisplayName(def)} ${def.name} ${def.tags.join(' ')}`,
      sortFn: (a, b) => getDisplayName(a).localeCompare(getDisplayName(b)),
    },
    {
      id: 'stressTolerance',
      label: t('pages.phaseSequences.stressTolerance'),
      render: (def) => (
        <Chip
          label={t(`enums.stressLevel.${def.stress_tolerance}`)}
          size="small"
          variant="outlined"
        />
      ),
      searchValue: (def) => t(`enums.stressLevel.${def.stress_tolerance}`),
      sortFn: (a, b) => a.stress_tolerance.localeCompare(b.stress_tolerance),
    },
    {
      id: 'typicalDuration',
      label: t('pages.phaseSequences.typicalDuration'),
      render: (def) =>
        t('pages.phaseSequences.durationDays', { count: def.typical_duration_days }),
      searchValue: (def) => String(def.typical_duration_days),
      sortFn: (a, b) => a.typical_duration_days - b.typical_duration_days,
      align: 'right',
      hideBelowBreakpoint: 'md',
    },
    {
      id: 'usageCount',
      label: t('pages.phaseSequences.usageCount'),
      render: (def) => def.usage_count,
      searchValue: (def) => String(def.usage_count),
      sortFn: (a, b) => a.usage_count - b.usage_count,
      align: 'right',
      hideBelowBreakpoint: 'md',
    },
    {
      // UI-NFR-018 R-002/R-019: Origin column
      id: 'origin',
      label: t('common.origin.filterLabel'),
      render: (def) => <OriginChip isSystem={def.is_system} />,
      sortable: false,
      searchable: false,
      hideBelowBreakpoint: 'md',
    },
    {
      id: 'actions',
      label: t('common.actions'),
      align: 'right',
      sortable: false,
      searchable: false,
      render: (def) => (
        <Box onClick={(e) => e.stopPropagation()}>
          {/* UI-NFR-018 R-011/R-013: hide edit/delete actions for system data */}
          {!def.is_system && (
            <Tooltip title={t('common.edit')}>
              <IconButton
                size="small"
                onClick={() => handleOpenEdit(def)}
                aria-label={t('common.edit')}
              >
                <EditIcon fontSize="small" />
              </IconButton>
            </Tooltip>
          )}
          {!def.is_system && (
            <Tooltip
              title={
                def.usage_count > 0
                  ? t('pages.phaseSequences.definitionInUse')
                  : t('common.delete')
              }
            >
              <span>
                <IconButton
                  size="small"
                  color="error"
                  disabled={def.usage_count > 0}
                  onClick={() => setDeleteKey(def.key)}
                  aria-label={t('common.delete')}
                >
                  <DeleteIcon fontSize="small" />
                </IconButton>
              </span>
            </Tooltip>
          )}
        </Box>
      ),
    },
  ];

  return (
    <Box data-testid="phase-definition-list-page">
      <PageTitle
        title={t('pages.phaseSequences.definitionsTitle')}
        action={
          <Button
            variant="contained"
            startIcon={<AddIcon />}
            onClick={handleOpenCreate}
            data-testid="create-definition-button"
          >
            {t('pages.phaseSequences.createDefinition')}
          </Button>
        }
      />

      <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
        {t('pages.phaseSequences.definitionsIntro')}
      </Typography>

      {error && <ErrorDisplay error={error} onRetry={loadDefinitions} />}

      <DataTable
        columns={columns}
        rows={definitions}
        loading={loading}
        getRowKey={(def) => def.key}
        onRowClick={(def) => navigate(`/phasen/definitionen/${def.key}`)}
        tableState={tableState}
        ariaLabel={t('pages.phaseSequences.definitionsTitle')}
        emptyMessage={t('pages.phaseSequences.noDefinitions')}
        emptyActionLabel={t('pages.phaseSequences.createDefinition')}
        onEmptyAction={handleOpenCreate}
        emptyIllustration={kamiPhaseGermination}
        mobileCardRenderer={(def) => (
          <MobileCard
            title={getDisplayName(def)}
            subtitle={def.name}
            trailing={<OriginChip isSystem={def.is_system} />}
            chips={
              <Chip
                label={t(`enums.stressLevel.${def.stress_tolerance}`)}
                size="small"
                variant="outlined"
              />
            }
            fields={[
              {
                label: t('pages.phaseSequences.typicalDuration'),
                value: t('pages.phaseSequences.durationDays', {
                  count: def.typical_duration_days,
                }),
              },
              {
                label: t('pages.phaseSequences.usageCount'),
                value: def.usage_count,
              },
            ]}
          />
        )}
      />

      <PhaseDefinitionDialog
        open={dialogOpen}
        onClose={() => {
          setDialogOpen(false);
          setEditDefinition(undefined);
        }}
        definition={editDefinition}
        onSaved={handleDialogSaved}
      />

      <ConfirmDialog
        open={!!deleteKey}
        title={t('pages.phaseSequences.deleteDefinition')}
        message={t('pages.phaseSequences.deleteDefinitionConfirm', {
          name: deleteTarget?.name ?? '',
        })}
        onConfirm={handleDelete}
        onCancel={() => setDeleteKey(null)}
        destructive
      />
    </Box>
  );
}
