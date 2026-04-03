import { useEffect, useMemo, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import Box from '@mui/material/Box';
import Button from '@mui/material/Button';
import Card from '@mui/material/Card';
import CardActionArea from '@mui/material/CardActionArea';
import CardActions from '@mui/material/CardActions';
import CardContent from '@mui/material/CardContent';
import Chip from '@mui/material/Chip';
import CircularProgress from '@mui/material/CircularProgress';
import Dialog from '@mui/material/Dialog';
import DialogActions from '@mui/material/DialogActions';
import DialogContent from '@mui/material/DialogContent';
import DialogTitle from '@mui/material/DialogTitle';
import IconButton from '@mui/material/IconButton';
import InputAdornment from '@mui/material/InputAdornment';
import Skeleton from '@mui/material/Skeleton';
import TextField from '@mui/material/TextField';
import Tooltip from '@mui/material/Tooltip';
import Typography from '@mui/material/Typography';
import useMediaQuery from '@mui/material/useMediaQuery';
import { useTheme } from '@mui/material/styles';
import AddIcon from '@mui/icons-material/Add';
import ContentCopyIcon from '@mui/icons-material/ContentCopy';
import DeleteIcon from '@mui/icons-material/Delete';
import LocalFloristIcon from '@mui/icons-material/LocalFlorist';
import AssignmentTurnedInIcon from '@mui/icons-material/AssignmentTurnedIn';
import SearchIcon from '@mui/icons-material/Search';
import SettingsIcon from '@mui/icons-material/Settings';
import SmartToyIcon from '@mui/icons-material/SmartToy';
import PageTitle from '@/components/layout/PageTitle';
import ConfirmDialog from '@/components/common/ConfirmDialog';
import { useAppDispatch, useAppSelector } from '@/store/hooks';
import { fetchWorkflows } from '@/store/slices/tasksSlice';
import { useNotification } from '@/hooks/useNotification';
import { useApiError } from '@/hooks/useApiError';
import * as taskApi from '@/api/endpoints/tasks';
import type { WorkflowTemplate } from '@/api/types';
import WorkflowInstantiateDialog from './WorkflowInstantiateDialog';
import WorkflowCreateDialog from './WorkflowCreateDialog';
import { kamiTasks } from '@/assets/brand/illustrations';

function WorkflowCard({
  workflow,
  onInstantiate,
  onDuplicate,
  onDelete,
}: {
  workflow: WorkflowTemplate;
  onInstantiate: (key: string) => void;
  onDuplicate: (key: string) => void;
  onDelete: (key: string) => void;
}) {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const theme = useTheme();

  return (
    <Card
      data-testid={`workflow-card-${workflow.key}`}
      sx={{
        display: 'flex',
        flexDirection: 'column',
        height: '100%',
        transition: 'box-shadow 0.2s ease-in-out, border-color 0.2s ease-in-out',
        border: 1,
        borderColor: 'divider',
        '&:hover': {
          boxShadow: theme.shadows[4],
          borderColor: 'primary.main',
        },
      }}
    >
      <CardActionArea
        onClick={() => navigate(`/aufgaben/workflows/${workflow.key}`)}
        sx={{ flexGrow: 1, display: 'flex', flexDirection: 'column', alignItems: 'stretch' }}
      >
        <CardContent sx={{ flexGrow: 1, pb: 1 }}>
          {/* Name */}
          <Tooltip title={workflow.name} disableHoverListener={workflow.name.length <= 40} enterDelay={500}>
            <Typography variant="subtitle1" component="h3" gutterBottom noWrap fontWeight={600}>
              {workflow.name}
            </Typography>
          </Tooltip>

          {/* Species info */}
          <Box sx={{ mb: 1.5, minHeight: 28 }}>
            {workflow.species_name ? (
              <Chip
                icon={<LocalFloristIcon />}
                label={workflow.species_name}
                size="small"
                color="success"
                variant="outlined"
              />
            ) : workflow.species_compatible.length > 0 ? (
              <Box sx={{ display: 'flex', gap: 0.5, flexWrap: 'wrap' }}>
                {workflow.species_compatible.slice(0, 3).map((s) => (
                  <Chip key={s} label={s} size="small" variant="outlined" />
                ))}
                {workflow.species_compatible.length > 3 && (
                  <Chip
                    label={`+${workflow.species_compatible.length - 3}`}
                    size="small"
                    variant="outlined"
                    color="default"
                  />
                )}
              </Box>
            ) : (
              <Typography variant="caption" color="text.secondary">
                {t('pages.tasks.allSpecies')}
              </Typography>
            )}
          </Box>

          {/* Category + Difficulty + Entity Type chips */}
          <Box sx={{ display: 'flex', gap: 0.5, flexWrap: 'wrap', mb: 1 }}>
            {workflow.category && (
              <Chip
                label={t(`enums.taskCategory.${workflow.category}`, { defaultValue: workflow.category })}
                size="small"
                color="default"
                variant="filled"
              />
            )}
            {workflow.difficulty_level && (
              <Chip
                label={t(`enums.difficultyLevel.${workflow.difficulty_level}`, { defaultValue: workflow.difficulty_level })}
                size="small"
                color="default"
                variant="outlined"
              />
            )}
            {workflow.target_entity_types
              .filter((et) => et !== 'plant_instance')
              .map((et) => (
                <Chip
                  key={et}
                  label={t(`pages.tasks.entityTypes.${et}`, { defaultValue: et })}
                  size="small"
                  color="info"
                  variant="outlined"
                />
              ))}
          </Box>

          {/* Badges row */}
          <Box sx={{ display: 'flex', gap: 0.5, flexWrap: 'wrap', mb: 1 }}>
            {workflow.is_system && (
              <Chip
                icon={<SettingsIcon />}
                label={t('pages.tasks.systemWorkflow')}
                size="small"
                color="info"
                variant="outlined"
              />
            )}
            {workflow.auto_generated && (
              <Chip
                icon={<SmartToyIcon />}
                label={t('pages.tasks.autoGenerated')}
                size="small"
                color="secondary"
                variant="outlined"
              />
            )}
          </Box>

          {/* Tags */}
          {workflow.tags.length > 0 && (
            <Box sx={{ display: 'flex', gap: 0.5, flexWrap: 'wrap', mb: 1 }}>
              {workflow.tags.map((tag) => (
                <Chip
                  key={tag}
                  label={tag}
                  size="small"
                  sx={{ fontSize: '0.7rem', height: 20 }}
                />
              ))}
            </Box>
          )}

          {/* Bottom info */}
          <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mt: 'auto' }}>
            {workflow.assigned_entity_count > 0 && (
              <Chip
                icon={<LocalFloristIcon />}
                label={`${workflow.assigned_entity_count} ${t('pages.tasks.assignedEntities')}`}
                size="small"
                color="primary"
                variant="outlined"
              />
            )}
            {workflow.total_duration_days > 0 && (
              <Typography variant="caption" color="text.secondary">
                {t('pages.tasks.totalDurationDays', { count: workflow.total_duration_days })}
              </Typography>
            )}
          </Box>
        </CardContent>
      </CardActionArea>

      <CardActions sx={{ justifyContent: 'flex-end', pt: 0, px: 2, pb: 1 }}>
        <Tooltip title={t('pages.tasks.applyWorkflow')}>
          <IconButton
            size="small"
            onClick={() => onInstantiate(workflow.key)}
            aria-label={t('pages.tasks.applyWorkflow')}
          >
            <AssignmentTurnedInIcon fontSize="small" />
          </IconButton>
        </Tooltip>
        <Tooltip title={t('pages.tasks.duplicateWorkflow')}>
          <IconButton
            size="small"
            onClick={() => onDuplicate(workflow.key)}
            aria-label={t('pages.tasks.duplicateWorkflow')}
          >
            <ContentCopyIcon fontSize="small" />
          </IconButton>
        </Tooltip>
        <Tooltip
          title={
            workflow.is_system
              ? t('pages.tasks.systemTemplateDeleteDisabled')
              : t('common.delete')
          }
        >
          <span>
            <IconButton
              size="small"
              color="error"
              disabled={workflow.is_system}
              onClick={() => onDelete(workflow.key)}
              aria-label={t('common.delete')}
            >
              <DeleteIcon fontSize="small" />
            </IconButton>
          </span>
        </Tooltip>
      </CardActions>
    </Card>
  );
}

function LoadingSkeletonCards() {
  return (
    <Box
      sx={{
        display: 'grid',
        gridTemplateColumns: {
          xs: '1fr',
          sm: 'repeat(2, 1fr)',
          md: 'repeat(3, 1fr)',
        },
        gap: 2,
      }}
    >
      {Array.from({ length: 6 }).map((_, i) => (
        <Card key={i} sx={{ p: 2 }}>
          <Skeleton variant="text" width="70%" height={28} />
          <Skeleton variant="rounded" width="50%" height={24} sx={{ mt: 1 }} />
          <Box sx={{ display: 'flex', gap: 1, mt: 1.5 }}>
            <Skeleton variant="rounded" width={80} height={24} />
            <Skeleton variant="rounded" width={80} height={24} />
          </Box>
          <Box sx={{ display: 'flex', justifyContent: 'flex-end', mt: 2 }}>
            <Skeleton variant="circular" width={32} height={32} />
            <Skeleton variant="circular" width={32} height={32} sx={{ ml: 1 }} />
          </Box>
        </Card>
      ))}
    </Box>
  );
}

export default function WorkflowTemplateListPage() {
  const theme = useTheme();
  const fullScreen = useMediaQuery(theme.breakpoints.down('sm'));
  const { t } = useTranslation();
  const dispatch = useAppDispatch();
  const navigate = useNavigate();
  const notification = useNotification();
  const { handleError } = useApiError();
  const { workflows, loading } = useAppSelector((s) => s.tasks);
  const [instantiateKey, setInstantiateKey] = useState<string | null>(null);
  const [createOpen, setCreateOpen] = useState(false);
  const [deleteKey, setDeleteKey] = useState<string | null>(null);
  const [duplicateKey, setDuplicateKey] = useState<string | null>(null);
  const [duplicateName, setDuplicateName] = useState('');
  const [duplicating, setDuplicating] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');


  useEffect(() => {
    dispatch(fetchWorkflows({}));
  }, [dispatch]);

  const filteredWorkflows = useMemo(() => {
    if (!searchQuery.trim()) return workflows;
    const query = searchQuery.toLowerCase();
    return workflows.filter(
      (w) =>
        w.name.toLowerCase().includes(query) ||
        w.species_name.toLowerCase().includes(query) ||
        w.species_compatible.some((s) => s.toLowerCase().includes(query)) ||
        w.tags.some((tag) => tag.toLowerCase().includes(query)),
    );
  }, [workflows, searchQuery]);

  const handleDelete = async () => {
    if (!deleteKey) return;
    try {
      await taskApi.deleteWorkflow(deleteKey);
      notification.success(t('pages.tasks.workflowDeleted'));
      setDeleteKey(null);
      dispatch(fetchWorkflows({}));
    } catch (err) {
      handleError(err);
    }
  };

  const handleOpenDuplicate = (key: string) => {
    const wf = workflows.find((w) => w.key === key);
    setDuplicateKey(key);
    setDuplicateName(wf ? `${wf.name} (${t('common.copy')})` : '');
  };

  const handleDuplicate = async () => {
    if (!duplicateKey || !duplicateName.trim()) return;
    setDuplicating(true);
    try {
      await taskApi.duplicateWorkflow(duplicateKey, duplicateName.trim());
      notification.success(t('pages.tasks.workflowDuplicated'));
      setDuplicateKey(null);
      dispatch(fetchWorkflows({}));
    } catch (err) {
      handleError(err);
    } finally {
      setDuplicating(false);
    }
  };


  return (
    <Box data-testid="workflow-template-list-page">
      {/* Header */}
      <Box
        sx={{
          display: 'flex',
          flexDirection: { xs: 'column', sm: 'row' },
          justifyContent: 'space-between',
          alignItems: { xs: 'stretch', sm: 'center' },
          gap: 1,
        }}
      >
        <PageTitle title={t('pages.tasks.workflowsTitle')} />
        <Box sx={{ display: 'flex', gap: 1, flexShrink: 0 }}>
          <Button
            variant="contained"
            startIcon={<AddIcon />}
            onClick={() => setCreateOpen(true)}
            data-testid="create-workflow-button"
          >
            {t('pages.tasks.createWorkflow')}
          </Button>
        </Box>
      </Box>

      <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
        {t('pages.tasks.workflowsIntro')}
      </Typography>

      {/* Search field */}
      <TextField
        size="small"
        placeholder={t('pages.tasks.searchWorkflows')}
        value={searchQuery}
        onChange={(e) => setSearchQuery(e.target.value)}
        slotProps={{
          input: {
            startAdornment: (
              <InputAdornment position="start">
                <SearchIcon color="action" />
              </InputAdornment>
            ),
          },
        }}
        sx={{ mb: 2, maxWidth: 400, width: '100%' }}
        data-testid="workflow-search"
        aria-label={t('pages.tasks.searchWorkflows')}
      />

      {/* Content */}
      {loading ? (
        <LoadingSkeletonCards />
      ) : filteredWorkflows.length === 0 ? (
        <Box
          sx={{
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            py: 8,
            px: 2,
          }}
        >
          <Box
            component="img"
            src={kamiTasks}
            alt=""
            sx={{ width: 200, height: 200, mb: 3, opacity: 0.7 }}
          />
          <Typography variant="h6" color="text.secondary" align="center">
            {searchQuery
              ? t('common.noSearchResults')
              : t('pages.tasks.noWorkflows')}
          </Typography>
        </Box>
      ) : (
        <Box
          sx={{
            display: 'grid',
            gridTemplateColumns: {
              xs: '1fr',
              sm: 'repeat(2, 1fr)',
              md: 'repeat(3, 1fr)',
            },
            gap: 2,
          }}
        >
          {filteredWorkflows.map((w) => (
            <WorkflowCard
              key={w.key}
              workflow={w}
              onInstantiate={setInstantiateKey}
              onDuplicate={handleOpenDuplicate}
              onDelete={setDeleteKey}
            />
          ))}
        </Box>
      )}

      {/* Dialogs */}
      {instantiateKey && (
        <WorkflowInstantiateDialog
          open={!!instantiateKey}
          workflowKey={instantiateKey}
          targetEntityTypes={workflows.find((w) => w.key === instantiateKey)?.target_entity_types ?? ['plant_instance']}
          onClose={() => setInstantiateKey(null)}
          onInstantiated={() => {
            setInstantiateKey(null);
            navigate('/aufgaben/queue');
          }}
        />
      )}
      <WorkflowCreateDialog
        open={createOpen}
        onClose={() => setCreateOpen(false)}
        onCreated={() => {
          setCreateOpen(false);
          dispatch(fetchWorkflows({}));
        }}
      />
      <ConfirmDialog
        open={!!deleteKey}
        title={t('pages.tasks.deleteWorkflow')}
        message={t('common.deleteConfirm', { name: workflows.find((w) => w.key === deleteKey)?.name ?? '' })}
        onConfirm={handleDelete}
        onCancel={() => setDeleteKey(null)}
        destructive
      />

      {/* Duplicate Workflow Dialog */}
      <Dialog
        fullScreen={fullScreen}
        open={!!duplicateKey}
        onClose={() => setDuplicateKey(null)}
        maxWidth="sm"
        fullWidth
      >
        <DialogTitle>{t('pages.tasks.duplicateWorkflow')}</DialogTitle>
        <DialogContent>
          <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
            {t('pages.tasks.duplicateWorkflowDescription', {
              name: workflows.find((w) => w.key === duplicateKey)?.name ?? '',
            })}
          </Typography>
          <TextField
            autoFocus
            fullWidth
            label={t('common.name')}
            value={duplicateName}
            onChange={(e) => setDuplicateName(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === 'Enter' && duplicateName.trim()) {
                handleDuplicate();
              }
            }}
            data-testid="duplicate-workflow-name"
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setDuplicateKey(null)}>
            {t('common.cancel')}
          </Button>
          <Button
            variant="contained"
            disabled={!duplicateName.trim() || duplicating}
            onClick={handleDuplicate}
            startIcon={duplicating ? <CircularProgress size={20} /> : <ContentCopyIcon />}
          >
            {t('pages.tasks.duplicateWorkflow')}
          </Button>
        </DialogActions>
      </Dialog>

    </Box>
  );
}
