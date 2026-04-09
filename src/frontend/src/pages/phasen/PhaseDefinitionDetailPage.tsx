import { useEffect, useState, useCallback } from 'react';
import { useParams, useNavigate, Link as RouterLink } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import Box from '@mui/material/Box';
import Button from '@mui/material/Button';
import Card from '@mui/material/Card';
import CardContent from '@mui/material/CardContent';
import Chip from '@mui/material/Chip';
import Paper from '@mui/material/Paper';
import Table from '@mui/material/Table';
import TableBody from '@mui/material/TableBody';
import TableCell from '@mui/material/TableCell';
import TableContainer from '@mui/material/TableContainer';
import TableHead from '@mui/material/TableHead';
import TableRow from '@mui/material/TableRow';
import Tooltip from '@mui/material/Tooltip';
import Typography from '@mui/material/Typography';
import ArrowBackIcon from '@mui/icons-material/ArrowBack';
import DeleteIcon from '@mui/icons-material/Delete';
import EditIcon from '@mui/icons-material/Edit';
import LoopIcon from '@mui/icons-material/Loop';
import PageTitle from '@/components/layout/PageTitle';
import LoadingSkeleton from '@/components/common/LoadingSkeleton';
import ErrorDisplay from '@/components/common/ErrorDisplay';
import ConfirmDialog from '@/components/common/ConfirmDialog';
import { useNotification } from '@/hooks/useNotification';
import { useApiError } from '@/hooks/useApiError';
import { useAppDispatch } from '@/store/hooks';
import { setBreadcrumbs } from '@/store/slices/uiSlice';
import * as phaseSequenceApi from '@/api/endpoints/phaseSequences';
import type { PhaseDefinition, PhaseSequence } from '@/api/types';
import PhaseDefinitionDialog from './PhaseDefinitionDialog';

const phaseIllustrations = import.meta.glob<{ default: string }>(
  '../../assets/brand/illustrations/phases/*.svg',
  { eager: true },
);

function getIllustrationUrl(path: string): string | null {
  const filename = path.split('/').pop();
  for (const [key, mod] of Object.entries(phaseIllustrations)) {
    if (key.endsWith(`/${filename}`)) return mod.default;
  }
  return null;
}

export default function PhaseDefinitionDetailPage() {
  const { key } = useParams<{ key: string }>();
  const navigate = useNavigate();
  const dispatch = useAppDispatch();
  const { t, i18n } = useTranslation();
  const lang = i18n.language;
  const notification = useNotification();
  const { handleError } = useApiError();

  const [definition, setDefinition] = useState<PhaseDefinition | null>(null);
  const [sequences, setSequences] = useState<PhaseSequence[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [editOpen, setEditOpen] = useState(false);
  const [deleteOpen, setDeleteOpen] = useState(false);

  const loadData = useCallback(async () => {
    if (!key) return;
    try {
      setLoading(true);
      setError(null);
      const [defData, seqData] = await Promise.all([
        phaseSequenceApi.getPhaseDefinition(key),
        phaseSequenceApi.listSequencesForDefinition(key).catch(() => []),
      ]);
      setDefinition(defData);
      setSequences(seqData);
    } catch (err) {
      setError(t('errors.notFound'));
      handleError(err);
    } finally {
      setLoading(false);
    }
  }, [key, t, handleError]);

  useEffect(() => {
    loadData();
  }, [loadData]);

  // Breadcrumbs
  useEffect(() => {
    if (!definition) return;
    dispatch(
      setBreadcrumbs([
        { label: 'nav.dashboard', path: '/dashboard' },
        {
          label: 'pages.phaseSequences.phaseDefinitions',
          path: '/phasen/definitionen',
        },
        { label: (lang === 'de' ? definition.display_name_de : definition.display_name) || definition.name },
      ]),
    );
  }, [definition, dispatch, lang]);

  // Clear breadcrumbs on unmount
  useEffect(() => () => {
    dispatch(setBreadcrumbs([]));
  }, [dispatch]);

  const handleDelete = async () => {
    if (!key) return;
    try {
      await phaseSequenceApi.deletePhaseDefinition(key);
      notification.success(t('pages.phaseSequences.definitionDeleted'));
      navigate('/phasen/definitionen');
    } catch (err) {
      handleError(err);
    }
  };

  const handleEditSaved = () => {
    setEditOpen(false);
    loadData();
  };

  const canDelete =
    definition != null &&
    !definition.is_system &&
    definition.usage_count === 0;

  if (loading) {
    return <LoadingSkeleton variant="form" />;
  }

  if (error || !definition) {
    return (
      <Box>
        <Button
          startIcon={<ArrowBackIcon />}
          onClick={() => navigate('/phasen/definitionen')}
          sx={{ mb: 2 }}
          data-testid="back-button"
        >
          {t('common.back')}
        </Button>
        <ErrorDisplay
          error={error ?? t('errors.notFound')}
          onRetry={loadData}
        />
      </Box>
    );
  }

  return (
    <Box data-testid="phase-definition-detail-page">
      <Button
        startIcon={<ArrowBackIcon />}
        onClick={() => navigate('/phasen/definitionen')}
        sx={{ mb: 2 }}
        data-testid="back-button"
      >
        {t('common.back')}
      </Button>

      <PageTitle
        title={(lang === 'de' ? definition.display_name_de : definition.display_name) || definition.name}
        action={
          <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap' }}>
            <Button
              variant="outlined"
              startIcon={<EditIcon />}
              onClick={() => setEditOpen(true)}
              disabled={definition.is_system}
              data-testid="edit-definition-button"
            >
              {t('pages.phaseSequences.editDefinition')}
            </Button>
            <Tooltip
              title={
                definition.is_system
                  ? t('pages.phaseSequences.system')
                  : definition.usage_count > 0
                    ? t('pages.phaseSequences.definitionInUse')
                    : t('common.delete')
              }
            >
              <span>
                <Button
                  variant="outlined"
                  color="error"
                  startIcon={<DeleteIcon />}
                  onClick={() => setDeleteOpen(true)}
                  disabled={!canDelete}
                  data-testid="delete-definition-button"
                >
                  {t('common.delete')}
                </Button>
              </span>
            </Tooltip>
          </Box>
        }
      />

      {/* Metadata chips */}
      <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1, mb: 3 }}>
        {definition.is_system && (
          <Chip
            label={t('pages.phaseSequences.system')}
            color="info"
            variant="outlined"
          />
        )}
        {definition.tags.map((tag) => (
          <Chip key={tag} label={tag} size="small" variant="outlined" />
        ))}
      </Box>

      {/* Properties Card */}
      <Card variant="outlined" sx={{ mb: 3 }}>
        <CardContent>
          {definition.illustration && (
            <Box sx={{ display: 'flex', justifyContent: 'center', mb: 2 }}>
              <Box
                component="img"
                src={getIllustrationUrl(definition.illustration) ?? ''}
                alt={(lang === 'de' ? definition.display_name_de : definition.display_name) || definition.name}
                sx={{ maxHeight: 120, maxWidth: '100%', objectFit: 'contain' }}
                onError={(e: React.SyntheticEvent<HTMLImageElement>) => {
                  (e.target as HTMLImageElement).style.display = 'none';
                }}
              />
            </Box>
          )}
          <Typography variant="h6" component="h2" sx={{ mb: 2 }}>
            {t('pages.phaseSequences.definitionDetails')}
          </Typography>
          <TableContainer>
            <Table size="small" aria-label={t('pages.phaseSequences.definitionDetails')}>
              <TableBody>
                <TableRow>
                  <TableCell
                    component="th"
                    scope="row"
                    sx={{ fontWeight: 'bold', width: '30%', borderBottom: 'none' }}
                  >
                    {t('common.name')}
                  </TableCell>
                  <TableCell sx={{ borderBottom: 'none' }}>
                    {definition.name}
                  </TableCell>
                </TableRow>
                <TableRow>
                  <TableCell
                    component="th"
                    scope="row"
                    sx={{ fontWeight: 'bold', borderBottom: 'none' }}
                  >
                    {t('pages.phaseSequences.displayName')} (EN)
                  </TableCell>
                  <TableCell sx={{ borderBottom: 'none' }}>
                    {definition.display_name || '\u2014'}
                  </TableCell>
                </TableRow>
                <TableRow>
                  <TableCell
                    component="th"
                    scope="row"
                    sx={{ fontWeight: 'bold', borderBottom: 'none' }}
                  >
                    {t('pages.phaseSequences.displayNameDe')}
                  </TableCell>
                  <TableCell sx={{ borderBottom: 'none' }}>
                    {definition.display_name_de || '\u2014'}
                  </TableCell>
                </TableRow>
                <TableRow>
                  <TableCell
                    component="th"
                    scope="row"
                    sx={{ fontWeight: 'bold', borderBottom: 'none' }}
                  >
                    {t('pages.phaseSequences.descriptionLabel')}
                  </TableCell>
                  <TableCell sx={{ borderBottom: 'none' }}>
                    {(lang === 'de' ? definition.description_de : definition.description) || '—'}
                  </TableCell>
                </TableRow>
                <TableRow>
                  <TableCell
                    component="th"
                    scope="row"
                    sx={{ fontWeight: 'bold', borderBottom: 'none' }}
                  >
                    {t('pages.phaseSequences.typicalDuration')}
                  </TableCell>
                  <TableCell sx={{ borderBottom: 'none' }}>
                    {t('pages.phaseSequences.totalDurationDays', {
                      count: definition.typical_duration_days,
                    })}
                  </TableCell>
                </TableRow>
                <TableRow>
                  <TableCell
                    component="th"
                    scope="row"
                    sx={{ fontWeight: 'bold', borderBottom: 'none' }}
                  >
                    {t('pages.phaseSequences.stressTolerance')}
                  </TableCell>
                  <TableCell sx={{ borderBottom: 'none' }}>
                    <Chip
                      label={t(
                        `enums.stressTolerance.${definition.stress_tolerance}`,
                      )}
                      size="small"
                      variant="outlined"
                    />
                  </TableCell>
                </TableRow>
                <TableRow>
                  <TableCell
                    component="th"
                    scope="row"
                    sx={{ fontWeight: 'bold', borderBottom: 'none' }}
                  >
                    {t('pages.phaseSequences.wateringInterval')}
                  </TableCell>
                  <TableCell sx={{ borderBottom: 'none' }}>
                    {definition.watering_interval_days != null
                      ? t('pages.phaseSequences.wateringIntervalDays', {
                          count: definition.watering_interval_days,
                        })
                      : '\u2014'}
                  </TableCell>
                </TableRow>
                <TableRow>
                  <TableCell
                    component="th"
                    scope="row"
                    sx={{ fontWeight: 'bold', borderBottom: 'none' }}
                  >
                    {t('pages.phaseSequences.tags')}
                  </TableCell>
                  <TableCell sx={{ borderBottom: 'none' }}>
                    {definition.tags.length > 0 ? (
                      <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5 }}>
                        {definition.tags.map((tag) => (
                          <Chip key={tag} label={tag} size="small" />
                        ))}
                      </Box>
                    ) : (
                      '\u2014'
                    )}
                  </TableCell>
                </TableRow>
              </TableBody>
            </Table>
          </TableContainer>
        </CardContent>
      </Card>

      {/* Sequences using this definition */}
      <Card variant="outlined">
        <CardContent>
          <Typography variant="h6" component="h2" sx={{ mb: 2 }}>
            {t('pages.phaseSequences.usedInSequences')}
          </Typography>

          {sequences.length === 0 ? (
            <Paper variant="outlined" sx={{ p: 4, textAlign: 'center' }}>
              <Typography color="text.secondary">
                {t('pages.phaseSequences.noSequencesUsingDefinition')}
              </Typography>
            </Paper>
          ) : (
            <TableContainer>
              <Table size="small" aria-label={t('pages.phaseSequences.usedInSequences')}>
                <TableHead>
                  <TableRow>
                    <TableCell>{t('common.name')}</TableCell>
                    <TableCell>{t('pages.phaseSequences.cycleType')}</TableCell>
                    <TableCell>{t('pages.phaseSequences.isRepeating')}</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {sequences.map((seq) => (
                    <TableRow
                      key={seq.key}
                      hover
                      data-testid={`sequence-row-${seq.key}`}
                    >
                      <TableCell>
                        <Typography
                          component={RouterLink}
                          to={`/phasen/ablaeufe/${seq.key}`}
                          sx={{
                            color: 'primary.main',
                            textDecoration: 'none',
                            '&:hover': { textDecoration: 'underline' },
                          }}
                        >
                          {(lang === 'de' ? seq.display_name_de : seq.display_name) || seq.name}
                        </Typography>
                      </TableCell>
                      <TableCell>
                        <Chip
                          label={t(`enums.cycleType.${seq.cycle_type}`)}
                          size="small"
                          variant="outlined"
                        />
                      </TableCell>
                      <TableCell>
                        {seq.is_repeating ? (
                          <Tooltip title={t('pages.phaseSequences.isRepeating')}>
                            <LoopIcon fontSize="small" color="secondary" aria-label={t('pages.phaseSequences.isRepeating')} />
                          </Tooltip>
                        ) : (
                          '\u2014'
                        )}
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </TableContainer>
          )}
        </CardContent>
      </Card>

      {/* Edit dialog */}
      <PhaseDefinitionDialog
        open={editOpen}
        onClose={() => setEditOpen(false)}
        definition={definition}
        onSaved={handleEditSaved}
      />

      {/* Delete confirm dialog */}
      <ConfirmDialog
        open={deleteOpen}
        title={t('pages.phaseSequences.deleteDefinition')}
        message={t('pages.phaseSequences.deleteDefinitionConfirm', {
          name: definition.name,
        })}
        onConfirm={handleDelete}
        onCancel={() => setDeleteOpen(false)}
        destructive
      />
    </Box>
  );
}
