import { useTranslation } from 'react-i18next';
import Box from '@mui/material/Box';
import Typography from '@mui/material/Typography';
import DataTable, { type Column } from '@/components/common/DataTable';
import EmptyState from '@/components/common/EmptyState';
import { useNavigate } from 'react-router-dom';
import type { PlantInRun, PlantingRunStatus } from '@/api/types';

interface PlantingRunPlantsTabProps {
  plants: PlantInRun[];
  plantColumns: Column<PlantInRun>[];
  runStatus: PlantingRunStatus | undefined;
  onCreatePlants: () => void;
}

export default function PlantingRunPlantsTab({
  plants,
  plantColumns,
  runStatus,
  onCreatePlants,
}: PlantingRunPlantsTabProps) {
  const { t } = useTranslation();
  const navigate = useNavigate();

  return (
    <Box role="tabpanel" aria-labelledby="tab-plants">
      <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 2 }}>
        <Typography variant="h6">
          {t('pages.plantingRuns.tabPlants')}
          {plants.length > 0 && (
            <Typography component="span" variant="body2" color="text.secondary" sx={{ ml: 1 }}>
              ({plants.length})
            </Typography>
          )}
        </Typography>
      </Box>
      {plants.length === 0 ? (
        <EmptyState
          message={t('pages.plantingRuns.noPlantsYet')}
          {...(runStatus === 'planned' ? {
            actionLabel: t('pages.plantingRuns.createPlants'),
            onAction: onCreatePlants,
          } : {})}
        />
      ) : (
        <DataTable
          columns={plantColumns}
          rows={plants}
          getRowKey={(r) => r.key}
          onRowClick={(r) => navigate(`/pflanzen/plant-instances/${r.key}`)}
          variant="simple"
          ariaLabel={t('pages.plantingRuns.tabPlants')}
        />
      )}
    </Box>
  );
}
