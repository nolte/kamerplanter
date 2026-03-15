import { useEffect, useState, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import Box from '@mui/material/Box';
import Button from '@mui/material/Button';
import Card from '@mui/material/Card';
import CardActionArea from '@mui/material/CardActionArea';
import CardContent from '@mui/material/CardContent';
import Chip from '@mui/material/Chip';
import CircularProgress from '@mui/material/CircularProgress';
import Dialog from '@mui/material/Dialog';
import DialogTitle from '@mui/material/DialogTitle';
import DialogContent from '@mui/material/DialogContent';
import DialogActions from '@mui/material/DialogActions';
import IconButton from '@mui/material/IconButton';
import TextField from '@mui/material/TextField';
import Typography from '@mui/material/Typography';
import AddIcon from '@mui/icons-material/Add';
import AutoFixHighIcon from '@mui/icons-material/AutoFixHigh';
import ContentCopyIcon from '@mui/icons-material/ContentCopy';
import DeleteIcon from '@mui/icons-material/Delete';
import GroupWorkIcon from '@mui/icons-material/GroupWork';
import Tooltip from '@mui/material/Tooltip';
import EmptyState from '@/components/common/EmptyState';
import ConfirmDialog from '@/components/common/ConfirmDialog';
import { useNotification } from '@/hooks/useNotification';
import { useApiError } from '@/hooks/useApiError';
import * as taskApi from '@/api/endpoints/tasks';
import * as activityPlanApi from '@/api/endpoints/activityPlans';
import type { WorkflowTemplate } from '@/api/types';

interface Props {
  speciesKey: string;
}

export default function SpeciesWorkflowsSection({ speciesKey }: Props) {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const notification = useNotification();
  const { handleError } = useApiError();

  const [workflows, setWorkflows] = useState<WorkflowTemplate[]>([]);
  const [loading, setLoading] = useState(true);
  const [generating, setGenerating] = useState(false);
  const [deleteKey, setDeleteKey] = useState<string | null>(null);
  const [createOpen, setCreateOpen] = useState(false);
  const [newName, setNewName] = useState('');
  const [creating, setCreating] = useState(false);
  const [duplicateSource, setDuplicateSource] = useState<WorkflowTemplate | null>(null);
  const [duplicateName, setDuplicateName] = useState('');
  const [duplicating, setDuplicating] = useState(false);

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const list = await taskApi.listWorkflows(0, 100, speciesKey);
      setWorkflows(list);
    } catch (err) {
      handleError(err);
    } finally {
      setLoading(false);
    }
  }, [speciesKey, handleError]);

  useEffect(() => { load(); }, [load]);

  const handleGenerate = useCallback(async () => {
    setGenerating(true);
    try {
      const result = await activityPlanApi.generatePlan({
        species_key: speciesKey,
        force_regenerate: false,
      });
      notification.success(t('pages.species.workflowGenerated'));
      load();
      navigate(`/aufgaben/workflows/${result.workflow_template_key}#templates`);
    } catch (err) {
      handleError(err);
    } finally {
      setGenerating(false);
    }
  }, [speciesKey, load, navigate, notification, handleError, t]);

  const handleCreateEmpty = useCallback(async () => {
    if (!newName.trim()) return;
    setCreating(true);
    try {
      const wf = await taskApi.createWorkflow({
        name: newName.trim(),
        species_key: speciesKey,
      });
      notification.success(t('pages.tasks.workflowCreated'));
      setCreateOpen(false);
      setNewName('');
      load();
      navigate(`/aufgaben/workflows/${wf.key}#templates`);
    } catch (err) {
      handleError(err);
    } finally {
      setCreating(false);
    }
  }, [newName, speciesKey, load, navigate, notification, handleError, t]);

  const handleDuplicate = useCallback(async () => {
    if (!duplicateSource || !duplicateName.trim()) return;
    setDuplicating(true);
    try {
      await taskApi.duplicateWorkflow(duplicateSource.key, duplicateName.trim());
      notification.success(t('pages.species.workflowDuplicated'));
      setDuplicateSource(null);
      setDuplicateName('');
      load();
    } catch (err) {
      handleError(err);
    } finally {
      setDuplicating(false);
    }
  }, [duplicateSource, duplicateName, load, notification, handleError, t]);

  const handleDelete = useCallback(async () => {
    if (!deleteKey) return;
    try {
      await taskApi.deleteWorkflow(deleteKey);
      notification.success(t('pages.tasks.workflowDeleted'));
      setDeleteKey(null);
      load();
    } catch (err) {
      handleError(err);
    }
  }, [deleteKey, load, notification, handleError, t]);

  if (loading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', py: 4 }}>
        <CircularProgress size={24} />
      </Box>
    );
  }

  return (
    <Box>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
        <Typography variant="h6">{t('pages.species.workflows')}</Typography>
        <Box sx={{ display: 'flex', gap: 1 }}>
          <Button
            variant="outlined"
            startIcon={generating ? <CircularProgress size={18} /> : <AutoFixHighIcon />}
            onClick={handleGenerate}
            disabled={generating}
            size="small"
          >
            {t('pages.species.autoGenerate')}
          </Button>
          <Button
            variant="contained"
            startIcon={<AddIcon />}
            onClick={() => { setNewName(''); setCreateOpen(true); }}
            size="small"
          >
            {t('pages.species.createWorkflow')}
          </Button>
        </Box>
      </Box>

      {workflows.length === 0 ? (
        <EmptyState
          message={t('pages.species.noWorkflows')}
          actionLabel={t('pages.species.autoGenerate')}
          onAction={handleGenerate}
        />
      ) : (
        <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1.5 }}>
          {workflows.map((wf) => (
            <Card key={wf.key} variant="outlined">
              <CardActionArea onClick={() => navigate(`/aufgaben/workflows/${wf.key}#templates`)}>
                <CardContent sx={{ display: 'flex', alignItems: 'center', gap: 2, py: 1.5 }}>
                  <Box sx={{ flex: 1 }}>
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 0.5 }}>
                      <Typography variant="subtitle1" sx={{ fontWeight: 600 }}>
                        {wf.name}
                      </Typography>
                      {wf.auto_generated && (
                        <Chip label={t('pages.tasks.autoGenerated')} size="small" color="secondary" variant="outlined" />
                      )}
                    </Box>
                    <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap' }}>
                      {wf.total_duration_days > 0 && (
                        <Chip label={`${wf.total_duration_days}d`} size="small" variant="outlined" />
                      )}
                      {wf.assigned_plant_count > 0 && (
                        <Chip
                          icon={<GroupWorkIcon />}
                          label={t('pages.species.assignedPlantCount', { count: wf.assigned_plant_count })}
                          size="small"
                          color="primary"
                          variant="outlined"
                        />
                      )}
                    </Box>
                  </Box>
                  <Box sx={{ display: 'flex', gap: 0.5 }}>
                    <Tooltip title={t('pages.species.duplicateWorkflow')}>
                      <IconButton
                        size="small"
                        onClick={(e) => {
                          e.stopPropagation();
                          e.preventDefault();
                          setDuplicateSource(wf);
                          setDuplicateName(`${wf.name} (${t('common.copy')})`);
                        }}
                      >
                        <ContentCopyIcon fontSize="small" />
                      </IconButton>
                    </Tooltip>
                    <Tooltip title={t('common.delete')}>
                      <IconButton
                        size="small"
                        color="error"
                        onClick={(e) => { e.stopPropagation(); e.preventDefault(); setDeleteKey(wf.key); }}
                        disabled={wf.is_system}
                      >
                        <DeleteIcon fontSize="small" />
                      </IconButton>
                    </Tooltip>
                  </Box>
                </CardContent>
              </CardActionArea>
            </Card>
          ))}
        </Box>
      )}

      {/* Create empty workflow dialog */}
      <Dialog open={createOpen} onClose={() => setCreateOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>{t('pages.species.createWorkflow')}</DialogTitle>
        <DialogContent>
          <TextField
            autoFocus
            fullWidth
            label={t('pages.tasks.workflowName')}
            value={newName}
            onChange={(e) => setNewName(e.target.value)}
            sx={{ mt: 1 }}
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setCreateOpen(false)}>{t('common.cancel')}</Button>
          <Button
            variant="contained"
            onClick={handleCreateEmpty}
            disabled={creating || !newName.trim()}
          >
            {t('common.create')}
          </Button>
        </DialogActions>
      </Dialog>

      {/* Duplicate workflow dialog */}
      <Dialog
        open={!!duplicateSource}
        onClose={() => setDuplicateSource(null)}
        maxWidth="sm"
        fullWidth
      >
        <DialogTitle>{t('pages.species.duplicateWorkflow')}</DialogTitle>
        <DialogContent>
          <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
            {t('pages.species.duplicateWorkflowDescription', { name: duplicateSource?.name ?? '' })}
          </Typography>
          <TextField
            autoFocus
            fullWidth
            label={t('pages.tasks.workflowName')}
            value={duplicateName}
            onChange={(e) => setDuplicateName(e.target.value)}
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setDuplicateSource(null)}>{t('common.cancel')}</Button>
          <Button
            variant="contained"
            onClick={handleDuplicate}
            disabled={duplicating || !duplicateName.trim()}
            startIcon={duplicating ? <CircularProgress size={18} /> : <ContentCopyIcon />}
          >
            {t('pages.species.duplicateWorkflow')}
          </Button>
        </DialogActions>
      </Dialog>

      <ConfirmDialog
        open={!!deleteKey}
        title={t('pages.tasks.deleteWorkflow')}
        message={t('common.deleteConfirm', { name: workflows.find((w) => w.key === deleteKey)?.name ?? '' })}
        onConfirm={handleDelete}
        onCancel={() => setDeleteKey(null)}
        destructive
      />
    </Box>
  );
}
