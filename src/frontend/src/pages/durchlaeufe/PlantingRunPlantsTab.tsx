import { useTranslation } from 'react-i18next';
import Box from '@mui/material/Box';
import Button from '@mui/material/Button';
import Chip from '@mui/material/Chip';
import Typography from '@mui/material/Typography';
import PersonAddIcon from '@mui/icons-material/PersonAdd';
import MobileCard from '@/components/common/MobileCard';
import DataTable, { type Column } from '@/components/common/DataTable';
import EmptyState from '@/components/common/EmptyState';
import { useNavigate } from 'react-router-dom';
import type { PlantInRun, PlantingRunStatus } from '@/api/types';
import { getPlantDisplayName } from '@/utils/plantDisplay';

interface PlantingRunPlantsTabProps {
  plants: PlantInRun[];
  plantColumns: Column<PlantInRun>[];
  runStatus: PlantingRunStatus | undefined;
  onCreatePlants: () => void;
  onAdoptPlants?: () => void;
}

export default function PlantingRunPlantsTab({
  plants,
  plantColumns,
  runStatus,
  onCreatePlants,
  onAdoptPlants,
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
        {onAdoptPlants && (runStatus === 'planned' || runStatus === 'active') && plants.length > 0 && (
          <Button
            variant="outlined"
            size="small"
            startIcon={<PersonAddIcon />}
            onClick={onAdoptPlants}
            data-testid="adopt-plants-tab-button"
          >
            {t('pages.plantingRuns.adoptPlants')}
          </Button>
        )}
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
          mobileCardRenderer={(r) => {
            const displayName = getPlantDisplayName(r);
            return (
              <MobileCard
                title={displayName}
                titleId="plantName"
                subtitle={displayName !== r.instance_id ? r.instance_id : undefined}
                subtitleId="instanceId"
                chips={
                  r.current_phase
                    ? [
                        {
                          id: 'currentPhase',
                          content: (
                            <Chip
                              label={t(`enums.phaseName.${r.current_phase}`, { defaultValue: r.current_phase })}
                              size="small"
                              color="primary"
                            />
                          ),
                        },
                      ]
                    : []
                }
                fields={[
                  ...(r.planted_on ? [{ id: 'plantedOn', label: t('pages.plantInstances.plantedOn'), value: r.planted_on }] : []),
                  ...(r.removed_on ? [{ id: 'removedOn', label: t('pages.plantInstances.removedOn'), value: r.removed_on }] : []),
                  ...(r.detached_at ? [{ id: 'detached', label: t('pages.plantingRuns.detached'), value: t('common.yes') }] : []),
                ]}
              />
            );
          }}
        />
      )}
    </Box>
  );
}
