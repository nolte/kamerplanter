import { useEffect, useState, useCallback } from 'react';
import { useTranslation } from 'react-i18next';
import Dialog from '@mui/material/Dialog';
import DialogTitle from '@mui/material/DialogTitle';
import DialogContent from '@mui/material/DialogContent';
import Box from '@mui/material/Box';
import Typography from '@mui/material/Typography';
import List from '@mui/material/List';
import ListItem from '@mui/material/ListItem';
import ListItemText from '@mui/material/ListItemText';
import Chip from '@mui/material/Chip';
import Autocomplete from '@mui/material/Autocomplete';
import TextField from '@mui/material/TextField';
import Button from '@mui/material/Button';
import CircularProgress from '@mui/material/CircularProgress';
import { useNotification } from '@/hooks/useNotification';
import { useApiError } from '@/hooks/useApiError';
import * as taskApi from '@/api/endpoints/tasks';
import * as plantApi from '@/api/endpoints/plantInstances';
import type { PlantInstance, TaskTemplate } from '@/api/types';

interface Props {
  open: boolean;
  workflowKey: string;
  onClose: () => void;
  onInstantiated: () => void;
}

export default function WorkflowInstantiateDialog({
  open,
  workflowKey,
  onClose,
  onInstantiated,
}: Props) {
  const { t } = useTranslation();
  const notification = useNotification();
  const { handleError } = useApiError();

  const [plants, setPlants] = useState<PlantInstance[]>([]);
  const [templates, setTemplates] = useState<TaskTemplate[]>([]);
  const [selectedPlantKey, setSelectedPlantKey] = useState<string | null>(null);
  const [loadingPlants, setLoadingPlants] = useState(false);
  const [loadingTemplates, setLoadingTemplates] = useState(false);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    if (!open) return;

    const loadPlants = async () => {
      setLoadingPlants(true);
      try {
        const data = await plantApi.listPlantInstances(0, 200);
        setPlants(data);
      } catch (err) {
        handleError(err);
      } finally {
        setLoadingPlants(false);
      }
    };

    const loadTemplates = async () => {
      setLoadingTemplates(true);
      try {
        const data = await taskApi.listTaskTemplates(workflowKey);
        setTemplates(data);
      } catch (err) {
        handleError(err);
      } finally {
        setLoadingTemplates(false);
      }
    };

    loadPlants();
    loadTemplates();
  }, [open, workflowKey, handleError]);

  const handleInstantiate = useCallback(async () => {
    if (!selectedPlantKey) return;
    try {
      setSaving(true);
      await taskApi.instantiateWorkflow(workflowKey, {
        plant_key: selectedPlantKey,
      });
      notification.success(t('pages.tasks.workflowInstantiated'));
      onInstantiated();
    } catch (err) {
      handleError(err);
    } finally {
      setSaving(false);
    }
  }, [workflowKey, selectedPlantKey, notification, handleError, t, onInstantiated]);

  const handleClose = () => {
    setSelectedPlantKey(null);
    onClose();
  };

  return (
    <Dialog open={open} onClose={handleClose} maxWidth="sm" fullWidth>
      <DialogTitle>{t('pages.tasks.instantiateWorkflow')}</DialogTitle>
      <DialogContent>
        <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
          {t('pages.tasks.instantiateIntro')}
        </Typography>

        <Autocomplete
          options={plants}
          getOptionLabel={(p) =>
            p.plant_name
              ? `${p.instance_id} - ${p.plant_name}`
              : p.instance_id
          }
          loading={loadingPlants}
          onChange={(_, value) => setSelectedPlantKey(value?.key ?? null)}
          renderInput={(params) => (
            <TextField
              {...params}
              label={t('pages.tasks.plant')}
              required
              sx={{ mb: 2 }}
              slotProps={{
                input: {
                  ...params.InputProps,
                  endAdornment: (
                    <>
                      {loadingPlants && <CircularProgress size={16} />}
                      {params.InputProps.endAdornment}
                    </>
                  ),
                },
              }}
              data-testid="plant-select"
            />
          )}
        />

        {loadingTemplates ? (
          <Box sx={{ display: 'flex', justifyContent: 'center', py: 2 }}>
            <CircularProgress size={24} />
          </Box>
        ) : templates.length > 0 ? (
          <Box>
            <Typography variant="subtitle2" sx={{ mb: 1 }}>
              {t('pages.tasks.taskPreview')} ({templates.length})
            </Typography>
            <List dense>
              {templates
                .sort((a, b) => a.sequence_order - b.sequence_order)
                .map((tmpl) => (
                  <ListItem key={tmpl.key} disablePadding sx={{ mb: 0.5 }}>
                    <ListItemText
                      primary={
                        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                          <Chip
                            label={tmpl.sequence_order}
                            size="small"
                            variant="outlined"
                          />
                          <span>{tmpl.name}</span>
                          <Chip
                            label={t(`enums.taskCategory.${tmpl.category}`)}
                            size="small"
                            variant="outlined"
                          />
                        </Box>
                      }
                      secondary={tmpl.instruction || undefined}
                    />
                  </ListItem>
                ))}
            </List>
          </Box>
        ) : (
          <Typography variant="body2" color="text.secondary">
            {t('pages.tasks.noTemplates')}
          </Typography>
        )}

        <Box sx={{ display: 'flex', gap: 2, mt: 3 }}>
          <Button
            variant="outlined"
            onClick={handleClose}
            disabled={saving}
            data-testid="form-cancel-button"
          >
            {t('common.cancel')}
          </Button>
          <Button
            variant="contained"
            onClick={handleInstantiate}
            disabled={!selectedPlantKey || saving}
            startIcon={saving ? <CircularProgress size={16} /> : undefined}
            data-testid="instantiate-button"
          >
            {t('pages.tasks.instantiate')}
          </Button>
        </Box>
      </DialogContent>
    </Dialog>
  );
}
