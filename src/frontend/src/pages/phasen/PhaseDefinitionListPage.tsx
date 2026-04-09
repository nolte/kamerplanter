import { useEffect, useMemo, useState, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import Box from '@mui/material/Box';
import Button from '@mui/material/Button';
import Chip from '@mui/material/Chip';
import IconButton from '@mui/material/IconButton';
import InputAdornment from '@mui/material/InputAdornment';
import Skeleton from '@mui/material/Skeleton';
import Table from '@mui/material/Table';
import TableBody from '@mui/material/TableBody';
import TableCell from '@mui/material/TableCell';
import TableContainer from '@mui/material/TableContainer';
import TableHead from '@mui/material/TableHead';
import TableRow from '@mui/material/TableRow';
import TextField from '@mui/material/TextField';
import Tooltip from '@mui/material/Tooltip';
import Typography from '@mui/material/Typography';
import Paper from '@mui/material/Paper';
import AddIcon from '@mui/icons-material/Add';
import DeleteIcon from '@mui/icons-material/Delete';
import EditIcon from '@mui/icons-material/Edit';
import SearchIcon from '@mui/icons-material/Search';
import SettingsIcon from '@mui/icons-material/Settings';
import PageTitle from '@/components/layout/PageTitle';
import ConfirmDialog from '@/components/common/ConfirmDialog';
import ErrorDisplay from '@/components/common/ErrorDisplay';
import { useNotification } from '@/hooks/useNotification';
import { useApiError } from '@/hooks/useApiError';
import * as phaseSequenceApi from '@/api/endpoints/phaseSequences';
import type { PhaseDefinition } from '@/api/types';
import PhaseDefinitionDialog from './PhaseDefinitionDialog';

function LoadingSkeletonTable() {
  return (
    <TableContainer component={Paper} variant="outlined">
      <Table>
        <TableHead>
          <TableRow>
            {Array.from({ length: 5 }).map((_, i) => (
              <TableCell key={i}>
                <Skeleton variant="text" width={80} />
              </TableCell>
            ))}
          </TableRow>
        </TableHead>
        <TableBody>
          {Array.from({ length: 5 }).map((_, i) => (
            <TableRow key={i}>
              {Array.from({ length: 5 }).map((_, j) => (
                <TableCell key={j}>
                  <Skeleton variant="text" width={j === 0 ? 120 : 60} />
                </TableCell>
              ))}
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </TableContainer>
  );
}

export default function PhaseDefinitionListPage() {
  const navigate = useNavigate();
  const { t, i18n } = useTranslation();
  const lang = i18n.language;
  const notification = useNotification();
  const { handleError } = useApiError();

  const [definitions, setDefinitions] = useState<PhaseDefinition[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [searchQuery, setSearchQuery] = useState('');
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

  const filteredDefinitions = useMemo(() => {
    if (!searchQuery.trim()) return definitions;
    const query = searchQuery.toLowerCase();
    return definitions.filter(
      (d) =>
        d.name.toLowerCase().includes(query) ||
        d.display_name.toLowerCase().includes(query) ||
        d.display_name_de.toLowerCase().includes(query) ||
        d.tags.some((tag) => tag.toLowerCase().includes(query)),
    );
  }, [definitions, searchQuery]);

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

      <TextField
        size="small"
        placeholder={t('pages.phaseSequences.searchDefinitions')}
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
        data-testid="definition-search"
        aria-label={t('pages.phaseSequences.searchDefinitions')}
      />

      {error && <ErrorDisplay error={error} onRetry={loadDefinitions} />}

      {loading ? (
        <LoadingSkeletonTable />
      ) : filteredDefinitions.length === 0 ? (
        <Box
          sx={{
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            py: 8,
            px: 2,
          }}
        >
          <Typography variant="h6" color="text.secondary" align="center">
            {searchQuery
              ? t('common.noSearchResults')
              : t('pages.phaseSequences.noDefinitions')}
          </Typography>
        </Box>
      ) : (
        <TableContainer component={Paper} variant="outlined">
          <Table>
            <TableHead>
              <TableRow>
                <TableCell>{t('common.name')}</TableCell>
                <TableCell>{t('pages.phaseSequences.typicalDuration')}</TableCell>
                <TableCell>{t('pages.phaseSequences.stressTolerance')}</TableCell>
                <TableCell>{t('pages.phaseSequences.usageCount')}</TableCell>
                <TableCell align="right">{t('common.actions')}</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {filteredDefinitions.map((def) => (
                <TableRow
                  key={def.key}
                  hover
                  onClick={() => navigate(`/phasen/definitionen/${def.key}`)}
                  sx={{ cursor: 'pointer' }}
                  data-testid={`definition-row-${def.key}`}
                >
                  <TableCell>
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                      <Box>
                        <Typography variant="body2" sx={{ fontWeight: 500 }}>
                          {(lang === 'de' ? def.display_name_de : def.display_name) || def.name}
                        </Typography>
                        <Typography variant="caption" color="text.secondary">
                          {def.name}
                        </Typography>
                      </Box>
                      {def.is_system && (
                        <Chip
                          icon={<SettingsIcon />}
                          label={t('pages.phaseSequences.system')}
                          size="small"
                          color="info"
                          variant="outlined"
                        />
                      )}
                    </Box>
                  </TableCell>
                  <TableCell>
                    {t('pages.phaseSequences.durationDays', {
                      count: def.typical_duration_days,
                    })}
                  </TableCell>
                  <TableCell>
                    <Chip
                      label={t(`enums.stressLevel.${def.stress_tolerance}`)}
                      size="small"
                      variant="outlined"
                    />
                  </TableCell>
                  <TableCell>{def.usage_count}</TableCell>
                  <TableCell align="right">
                    <Tooltip title={t('common.edit')}>
                      <IconButton
                        size="small"
                        onClick={() => handleOpenEdit(def)}
                        aria-label={t('common.edit')}
                        disabled={def.is_system}
                      >
                        <EditIcon fontSize="small" />
                      </IconButton>
                    </Tooltip>
                    <Tooltip
                      title={
                        def.usage_count > 0
                          ? t('pages.phaseSequences.definitionInUse')
                          : def.is_system
                            ? t('pages.phaseSequences.system')
                            : t('common.delete')
                      }
                    >
                      <span>
                        <IconButton
                          size="small"
                          color="error"
                          disabled={def.usage_count > 0 || def.is_system}
                          onClick={() => setDeleteKey(def.key)}
                          aria-label={t('common.delete')}
                        >
                          <DeleteIcon fontSize="small" />
                        </IconButton>
                      </span>
                    </Tooltip>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </TableContainer>
      )}

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
