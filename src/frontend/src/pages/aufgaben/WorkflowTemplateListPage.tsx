import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import Box from '@mui/material/Box';
import Chip from '@mui/material/Chip';
import Typography from '@mui/material/Typography';
import PageTitle from '@/components/layout/PageTitle';
import DataTable, { type Column } from '@/components/common/DataTable';
import { useAppDispatch, useAppSelector } from '@/store/hooks';
import { fetchWorkflows } from '@/store/slices/tasksSlice';
import { useTableUrlState } from '@/hooks/useTableState';
import type { WorkflowTemplate } from '@/api/types';
import WorkflowInstantiateDialog from './WorkflowInstantiateDialog';

export default function WorkflowTemplateListPage() {
  const { t } = useTranslation();
  const dispatch = useAppDispatch();
  const navigate = useNavigate();
  const { workflows, loading } = useAppSelector((s) => s.tasks);
  const [instantiateKey, setInstantiateKey] = useState<string | null>(null);
  const tableState = useTableUrlState({ defaultSort: { column: 'name', direction: 'asc' } });

  useEffect(() => {
    dispatch(fetchWorkflows({}));
  }, [dispatch]);

  const columns: Column<WorkflowTemplate>[] = [
    {
      id: 'name',
      label: t('pages.tasks.workflowName'),
      render: (r) => (
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          <span>{r.name}</span>
          {r.is_system && (
            <Chip
              label={t('pages.tasks.systemWorkflow')}
              size="small"
              color="info"
              variant="outlined"
            />
          )}
        </Box>
      ),
      searchValue: (r) => r.name,
    },
    {
      id: 'category',
      label: t('pages.tasks.category'),
      render: (r) => t(`enums.taskCategory.${r.category}`),
      searchValue: (r) => t(`enums.taskCategory.${r.category}`),
    },
    {
      id: 'difficultyLevel',
      label: t('pages.tasks.difficultyLevel'),
      render: (r) => t(`enums.difficultyLevel.${r.difficulty_level}`),
      searchValue: (r) => t(`enums.difficultyLevel.${r.difficulty_level}`),
    },
    {
      id: 'version',
      label: t('pages.tasks.version'),
      render: (r) => r.version,
    },
    {
      id: 'speciesCount',
      label: t('pages.tasks.speciesCompatible'),
      render: (r) => r.species_compatible.length,
      align: 'right',
      searchValue: (r) => String(r.species_compatible.length),
    },
  ];

  return (
    <Box data-testid="workflow-template-list-page">
      <Box
        sx={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
        }}
      >
        <PageTitle title={t('pages.tasks.workflowsTitle')} />
      </Box>
      <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
        {t('pages.tasks.workflowsIntro')}
      </Typography>
      <DataTable
        columns={columns}
        rows={workflows}
        loading={loading}
        onRowClick={(r) => setInstantiateKey(r.key)}
        getRowKey={(r) => r.key}
        emptyMessage={t('pages.tasks.noWorkflows')}
        tableState={tableState}
        ariaLabel={t('pages.tasks.workflowsTitle')}
      />
      {instantiateKey && (
        <WorkflowInstantiateDialog
          open={!!instantiateKey}
          workflowKey={instantiateKey}
          onClose={() => setInstantiateKey(null)}
          onInstantiated={() => {
            setInstantiateKey(null);
            navigate('/aufgaben');
          }}
        />
      )}
    </Box>
  );
}
