import { useEffect, useState, useCallback } from 'react';
import { useParams, useNavigate, Link as RouterLink } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import Box from '@mui/material/Box';
import Button from '@mui/material/Button';
import Card from '@mui/material/Card';
import CardContent from '@mui/material/CardContent';
import Chip from '@mui/material/Chip';
import Divider from '@mui/material/Divider';
import Grid from '@mui/material/Grid';
import Tooltip from '@mui/material/Tooltip';
import Typography from '@mui/material/Typography';
import ArrowBackIcon from '@mui/icons-material/ArrowBack';
import DeleteIcon from '@mui/icons-material/Delete';
import EditIcon from '@mui/icons-material/Edit';
import InfoOutlinedIcon from '@mui/icons-material/InfoOutlined';
import LoopIcon from '@mui/icons-material/Loop';
import PageTitle from '@/components/layout/PageTitle';
import LoadingSkeleton from '@/components/common/LoadingSkeleton';
import ErrorDisplay from '@/components/common/ErrorDisplay';
import ConfirmDialog from '@/components/common/ConfirmDialog';
import DataTable, { type Column } from '@/components/common/DataTable';
import MobileCard from '@/components/common/MobileCard';
import OriginChip from '@/components/common/OriginChip';
import { useNotification } from '@/hooks/useNotification';
import { useApiError } from '@/hooks/useApiError';
import { useAppDispatch } from '@/store/hooks';
import { setBreadcrumbs } from '@/store/slices/uiSlice';
import * as phaseSequenceApi from '@/api/endpoints/phaseSequences';
import * as plantInstanceApi from '@/api/endpoints/plantInstances';
import type {
  PhaseDefinition,
  PhaseDefinitionSpecies,
  PhaseSequence,
  PlantInstanceInPhase,
  PlantInstancesInPhase,
} from '@/api/types';
import PhaseDefinitionDialog from './PhaseDefinitionDialog';

/** Elapsed whole days since a phase-start timestamp (FIX-01 R2). Null when unknown. */
function daysInPhase(startedAt: string | null): number | null {
  if (!startedAt) return null;
  const start = new Date(startedAt);
  if (Number.isNaN(start.getTime())) return null;
  return Math.max(0, Math.floor((Date.now() - start.getTime()) / 86_400_000));
}

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
  const [plantsInPhase, setPlantsInPhase] = useState<PlantInstancesInPhase>({
    total: 0,
    items: [],
  });
  const [speciesInPhase, setSpeciesInPhase] = useState<PhaseDefinitionSpecies[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [editOpen, setEditOpen] = useState(false);
  const [deleteOpen, setDeleteOpen] = useState(false);
  const [deleting, setDeleting] = useState(false);

  const [reloadCounter, setReloadCounter] = useState(0);
  const reload = useCallback(() => setReloadCounter((c) => c + 1), []);

  useEffect(() => {
    if (!key) return;
    let cancelled = false;
    void (async () => {
      try {
        const [defData, seqData, plantsData, speciesData] = await Promise.all([
          phaseSequenceApi.getPhaseDefinition(key),
          phaseSequenceApi.listSequencesForDefinition(key).catch(() => [] as PhaseSequence[]),
          // Tenant-scoped (FIX-01 List 1): tolerate absence of a tenant context (e.g.
          // light mode) by degrading to an empty list rather than failing the page.
          plantInstanceApi
            .listPlantInstancesInPhaseDefinition(key)
            .catch(() => ({ total: 0, items: [] }) as PlantInstancesInPhase),
          phaseSequenceApi
            .listSpeciesForDefinition(key)
            .catch(() => [] as PhaseDefinitionSpecies[]),
        ]);
        if (cancelled) return;
        setDefinition(defData);
        setSequences(seqData);
        setPlantsInPhase(plantsData);
        setSpeciesInPhase(speciesData);
        setError(null);
      } catch (err) {
        if (cancelled) return;
        setError(t('errors.notFound'));
        handleError(err);
      } finally {
        if (!cancelled) setLoading(false);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [key, t, handleError, reloadCounter]);

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
    setDeleting(true);
    try {
      await phaseSequenceApi.deletePhaseDefinition(key);
      notification.success(t('pages.phaseSequences.definitionDeleted'));
      navigate('/phasen/definitionen');
    } catch (err) {
      handleError(err);
    } finally {
      setDeleting(false);
    }
  };

  const handleEditSaved = () => {
    setEditOpen(false);
    reload();
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
          onRetry={reload}
        />
      </Box>
    );
  }

  const displayName = (lang === 'de' ? definition.display_name_de : definition.display_name) || definition.name;
  const illustrationUrl = definition.illustration ? getIllustrationUrl(definition.illustration) : null;

  // Column definitions (FIX-01 R10: all lists use the shared DataTable, UI-NFR-010 R-037).
  const sequenceColumns: Column<PhaseSequence>[] = [
    {
      id: 'name',
      label: t('common.name'),
      render: (seq) => (
        <Typography
          component={RouterLink}
          to={`/phasen/ablaeufe/${seq.key}`}
          data-testid={`sequence-row-${seq.key}`}
          sx={{
            color: 'primary.main',
            textDecoration: 'none',
            '&:hover': { textDecoration: 'underline' },
          }}
        >
          {(lang === 'de' ? seq.display_name_de : seq.display_name) || seq.name}
        </Typography>
      ),
      searchValue: (seq) => (lang === 'de' ? seq.display_name_de : seq.display_name) || seq.name,
    },
    {
      id: 'cycleType',
      label: t('pages.phaseSequences.cycleType'),
      render: (seq) => (
        <Chip label={t(`enums.cycleType.${seq.cycle_type}`)} size="small" variant="outlined" />
      ),
      searchValue: (seq) => t(`enums.cycleType.${seq.cycle_type}`),
    },
    {
      id: 'isRepeating',
      label: t('pages.phaseSequences.isRepeating'),
      align: 'right',
      sortable: false,
      searchable: false,
      render: (seq) =>
        seq.is_repeating ? (
          <Tooltip title={t('pages.phaseSequences.isRepeating')}>
            <LoopIcon fontSize="small" color="secondary" aria-label={t('pages.phaseSequences.isRepeating')} />
          </Tooltip>
        ) : (
          '—'
        ),
    },
  ];

  const plantColumns: Column<PlantInstanceInPhase>[] = [
    {
      id: 'plantLabel',
      label: t('pages.phaseSequences.plantLabel'),
      render: (plant) => (
        <Typography
          component={RouterLink}
          to={`/pflanzen/plant-instances/${plant.key}`}
          data-testid={`plant-in-phase-row-${plant.key}`}
          sx={{
            color: 'primary.main',
            textDecoration: 'none',
            '&:hover': { textDecoration: 'underline' },
          }}
        >
          {plant.plant_name || plant.instance_id}
        </Typography>
      ),
      searchValue: (plant) => plant.plant_name || plant.instance_id,
    },
    {
      id: 'species',
      label: t('pages.phaseSequences.species'),
      render: (plant) => plant.species_scientific_name || '—',
      searchValue: (plant) => plant.species_scientific_name ?? '',
    },
    {
      id: 'locationSlot',
      label: t('pages.phaseSequences.locationSlot'),
      render: (plant) => [plant.location_name, plant.slot_label].filter(Boolean).join(' · ') || '—',
      searchValue: (plant) => [plant.location_name, plant.slot_label].filter(Boolean).join(' '),
      hideBelowBreakpoint: 'md',
    },
    {
      id: 'phaseSince',
      label: t('pages.phaseSequences.phaseSince'),
      render: (plant) =>
        plant.current_phase_started_at
          ? new Date(plant.current_phase_started_at).toLocaleDateString(lang)
          : '—',
      searchValue: (plant) =>
        plant.current_phase_started_at ? new Date(plant.current_phase_started_at).toLocaleDateString(lang) : '',
    },
    {
      id: 'daysInPhase',
      label: t('pages.phaseSequences.daysInPhase'),
      align: 'right',
      render: (plant) => {
        const days = daysInPhase(plant.current_phase_started_at);
        return days != null ? t('pages.phaseSequences.daysInPhaseValue', { count: days }) : '—';
      },
      sortFn: (a, b) => (daysInPhase(a.current_phase_started_at) ?? -1) - (daysInPhase(b.current_phase_started_at) ?? -1),
    },
  ];

  const speciesColumns: Column<PhaseDefinitionSpecies>[] = [
    {
      id: 'scientificName',
      label: t('pages.phaseSequences.scientificName'),
      render: (species) => (
        <Typography
          component={RouterLink}
          to={`/stammdaten/species/${species.key}`}
          data-testid={`species-in-phase-row-${species.key}`}
          sx={{
            fontStyle: 'italic',
            color: 'primary.main',
            textDecoration: 'none',
            '&:hover': { textDecoration: 'underline' },
          }}
        >
          {species.scientific_name || species.key}
        </Typography>
      ),
      searchValue: (species) => species.scientific_name || species.key,
    },
    {
      id: 'commonName',
      label: t('pages.phaseSequences.commonName'),
      render: (species) => (species.common_names.length > 0 ? species.common_names.join(', ') : '—'),
      searchValue: (species) => species.common_names.join(' '),
    },
    {
      id: 'typicalDuration',
      label: t('pages.phaseSequences.typicalDuration'),
      align: 'right',
      render: (species) => t('pages.phaseSequences.totalDurationDays', { count: species.typical_duration_days }),
      sortFn: (a, b) => a.typical_duration_days - b.typical_duration_days,
    },
  ];

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

      {/* UI-NFR-017 Pattern C: title-row + meta-row (chips), actions aligned with the title row. */}
      <PageTitle
        title={displayName}
        meta={
          <>
            <OriginChip isSystem={definition.is_system} />
            {definition.tags.map((tag) => (
              <Chip key={tag} label={tag} size="small" variant="outlined" />
            ))}
          </>
        }
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

      {/* Page-level intro: explains the dual operational/reference purpose (FIX-01 R10). */}
      <Typography variant="body2" color="text.secondary" sx={{ mb: 3, maxWidth: 760 }}>
        {t('pages.phaseSequences.detailIntro')}
      </Typography>

      {/* Properties Card — core reference data for the phase */}
      <Card variant="outlined" sx={{ mb: 3 }} data-testid="phase-definition-properties-card">
        <CardContent>
          {definition.illustration && (
            <Box sx={{ display: 'flex', justifyContent: 'center', mb: 2 }}>
              <Box
                component="img"
                src={illustrationUrl ?? ''}
                alt={displayName}
                sx={{ maxHeight: 120, maxWidth: '100%', objectFit: 'contain' }}
                onError={(e: React.SyntheticEvent<HTMLImageElement>) => {
                  (e.target as HTMLImageElement).style.display = 'none';
                }}
              />
            </Box>
          )}
          <Typography variant="h6" component="h2" sx={{ mb: 0.5 }}>
            {t('pages.phaseSequences.definitionDetails')}
          </Typography>
          <Typography variant="body2" color="text.secondary" sx={{ mb: 2, maxWidth: 760 }}>
            {t('pages.phaseSequences.propertiesIntro')}
          </Typography>

          <Grid container spacing={2}>
            <Grid size={{ xs: 6, sm: 4, md: 3 }}>
              <Typography variant="caption" color="text.secondary">
                {t('common.name')}
              </Typography>
              <Typography variant="body2" sx={{ fontWeight: 500 }}>
                {definition.name}
              </Typography>
            </Grid>
            <Grid size={{ xs: 6, sm: 4, md: 3 }}>
              <Typography variant="caption" color="text.secondary">
                {t('pages.phaseSequences.displayName')} (EN)
              </Typography>
              <Typography variant="body2" sx={{ fontWeight: 500 }}>
                {definition.display_name || '—'}
              </Typography>
            </Grid>
            <Grid size={{ xs: 6, sm: 4, md: 3 }}>
              <Typography variant="caption" color="text.secondary">
                {t('pages.phaseSequences.displayNameDe')}
              </Typography>
              <Typography variant="body2" sx={{ fontWeight: 500 }}>
                {definition.display_name_de || '—'}
              </Typography>
            </Grid>
            <Grid size={{ xs: 6, sm: 4, md: 3 }}>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
                <Typography variant="caption" color="text.secondary">
                  {t('pages.phaseSequences.typicalDuration')}
                </Typography>
                <Tooltip title={t('pages.phaseSequences.typicalDurationTooltip')} arrow>
                  <InfoOutlinedIcon
                    sx={{ fontSize: 14, color: 'text.secondary', cursor: 'help' }}
                    tabIndex={0}
                    aria-label={t('pages.phaseSequences.typicalDurationTooltip')}
                  />
                </Tooltip>
              </Box>
              <Typography variant="body2" sx={{ fontWeight: 500 }}>
                {t('pages.phaseSequences.totalDurationDays', { count: definition.typical_duration_days })}
              </Typography>
            </Grid>
            <Grid size={{ xs: 6, sm: 4, md: 3 }}>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
                <Typography variant="caption" color="text.secondary">
                  {t('pages.phaseSequences.stressTolerance')}
                </Typography>
                <Tooltip title={t('pages.phaseSequences.stressToleranceTooltip')} arrow>
                  <InfoOutlinedIcon
                    sx={{ fontSize: 14, color: 'text.secondary', cursor: 'help' }}
                    tabIndex={0}
                    aria-label={t('pages.phaseSequences.stressToleranceTooltip')}
                  />
                </Tooltip>
              </Box>
              <Chip
                label={t(`enums.stressTolerance.${definition.stress_tolerance}`)}
                size="small"
                variant="outlined"
                sx={{ mt: 0.25 }}
              />
            </Grid>
            <Grid size={{ xs: 6, sm: 4, md: 3 }}>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
                <Typography variant="caption" color="text.secondary">
                  {t('pages.phaseSequences.wateringInterval')}
                </Typography>
                <Tooltip title={t('pages.phaseSequences.wateringIntervalTooltip')} arrow>
                  <InfoOutlinedIcon
                    sx={{ fontSize: 14, color: 'text.secondary', cursor: 'help' }}
                    tabIndex={0}
                    aria-label={t('pages.phaseSequences.wateringIntervalTooltip')}
                  />
                </Tooltip>
              </Box>
              <Typography variant="body2" sx={{ fontWeight: 500 }}>
                {definition.watering_interval_days != null
                  ? t('pages.phaseSequences.wateringIntervalDays', { count: definition.watering_interval_days })
                  : '—'}
              </Typography>
            </Grid>
          </Grid>

          <Box sx={{ mt: 2, maxWidth: 760 }}>
            <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mb: 0.5 }}>
              {t('pages.phaseSequences.descriptionLabel')}
            </Typography>
            <Typography variant="body2">
              {(lang === 'de' ? definition.description_de : definition.description) || '—'}
            </Typography>
          </Box>
        </CardContent>
      </Card>

      {/* List 1 — tenant's active plant instances currently in this phase (FIX-01 R1–R4).
          Operational content: placed directly after the reference properties, so the
          most actionable information ("which of my plants need attention now") is the
          first thing beyond the phase's static definition. */}
      <Card variant="outlined" sx={{ mb: 3, borderColor: 'primary.main' }} data-testid="phase-definition-plants-card">
        <CardContent>
          <Box sx={{ display: 'flex', alignItems: 'center', flexWrap: 'wrap', gap: 1, mb: 0.5 }}>
            <Typography variant="h6" component="h2">
              {t('pages.phaseSequences.plantsInPhase')}
            </Typography>
            <Chip
              label={plantsInPhase.total}
              size="small"
              color="primary"
              data-testid="plants-in-phase-count"
              aria-label={t('pages.phaseSequences.plantsInPhaseCount', { count: plantsInPhase.total })}
            />
          </Box>
          <Typography variant="body2" color="text.secondary" sx={{ mb: 2, maxWidth: 760 }}>
            {t('pages.phaseSequences.plantsInPhaseIntro')}
          </Typography>

          <DataTable
            columns={plantColumns}
            rows={plantsInPhase.items}
            getRowKey={(plant) => plant.key}
            onRowClick={(plant) => navigate(`/pflanzen/plant-instances/${plant.key}`)}
            variant="simple"
            ariaLabel={t('pages.phaseSequences.plantsInPhase')}
            emptyMessage={t('pages.phaseSequences.noPlantsInPhase')}
            emptyDescription={t('pages.phaseSequences.noPlantsInPhaseDesc')}
            mobileCardRenderer={(plant) => {
              const days = daysInPhase(plant.current_phase_started_at);
              const locationSlot = [plant.location_name, plant.slot_label].filter(Boolean).join(' · ');
              return (
                <MobileCard
                  title={plant.plant_name || plant.instance_id}
                  titleId="plantLabel"
                  subtitle={plant.species_scientific_name || undefined}
                  subtitleId="species"
                  fields={[
                    ...(locationSlot ? [{ id: 'locationSlot', label: t('pages.phaseSequences.locationSlot'), value: locationSlot }] : []),
                    {
                      id: 'phaseSince',
                      label: t('pages.phaseSequences.phaseSince'),
                      value: plant.current_phase_started_at
                        ? new Date(plant.current_phase_started_at).toLocaleDateString(lang)
                        : '—',
                    },
                    {
                      id: 'daysInPhase',
                      label: t('pages.phaseSequences.daysInPhase'),
                      value: days != null ? t('pages.phaseSequences.daysInPhaseValue', { count: days }) : '—',
                    },
                  ]}
                />
              );
            }}
          />
        </CardContent>
      </Card>

      {/* Reference section — composition data: where this definition is used, and which
          species traverse it. Grouped visually and laid out side-by-side on md+ to use
          the available desktop width instead of stacking two narrow tables (UI-NFR-001
          R-023). Stacks to a single column on mobile. */}
      <Divider sx={{ mb: 2 }} />
      <Typography variant="subtitle1" color="text.secondary" sx={{ mb: 2 }}>
        {t('pages.phaseSequences.referenceSectionTitle')}
      </Typography>

      <Grid container spacing={2}>
        {/* Sequences using this definition */}
        <Grid size={{ xs: 12, md: 6 }}>
          <Card variant="outlined" sx={{ height: '100%' }} data-testid="phase-definition-sequences-card">
            <CardContent>
              <Typography variant="h6" component="h2" sx={{ mb: 0.5 }}>
                {t('pages.phaseSequences.usedInSequences')}
              </Typography>
              <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                {t('pages.phaseSequences.usedInSequencesIntro')}
              </Typography>

              <DataTable
                columns={sequenceColumns}
                rows={sequences}
                getRowKey={(seq) => seq.key}
                onRowClick={(seq) => navigate(`/phasen/ablaeufe/${seq.key}`)}
                variant="simple"
                ariaLabel={t('pages.phaseSequences.usedInSequences')}
                emptyMessage={t('pages.phaseSequences.noSequencesUsingDefinition')}
                emptyDescription={t('pages.phaseSequences.noSequencesUsingDefinitionDesc')}
                mobileCardRenderer={(seq) => (
                  <MobileCard
                    title={(lang === 'de' ? seq.display_name_de : seq.display_name) || seq.name}
                    titleId="name"
                    chips={[
                      {
                        id: 'cycleType',
                        content: <Chip label={t(`enums.cycleType.${seq.cycle_type}`)} size="small" variant="outlined" />,
                      },
                    ]}
                    trailing={
                      seq.is_repeating ? (
                        <Tooltip title={t('pages.phaseSequences.isRepeating')}>
                          <LoopIcon fontSize="small" color="secondary" aria-label={t('pages.phaseSequences.isRepeating')} />
                        </Tooltip>
                      ) : undefined
                    }
                  />
                )}
              />
            </CardContent>
          </Card>
        </Grid>

        {/* Species (global catalog) that traverse this phase */}
        <Grid size={{ xs: 12, md: 6 }}>
          <Card variant="outlined" sx={{ height: '100%' }} data-testid="phase-definition-species-card">
            <CardContent>
              <Typography variant="h6" component="h2" sx={{ mb: 0.5 }}>
                {t('pages.phaseSequences.speciesInPhase')}
              </Typography>
              <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                {t('pages.phaseSequences.speciesInPhaseIntro')}
              </Typography>

              <DataTable
                columns={speciesColumns}
                rows={speciesInPhase}
                getRowKey={(species) => species.key}
                onRowClick={(species) => navigate(`/stammdaten/species/${species.key}`)}
                variant="simple"
                ariaLabel={t('pages.phaseSequences.speciesInPhase')}
                emptyMessage={t('pages.phaseSequences.noSpeciesInPhase')}
                emptyDescription={t('pages.phaseSequences.noSpeciesInPhaseDesc')}
                mobileCardRenderer={(species) => (
                  <MobileCard
                    title={<Box sx={{ fontStyle: 'italic' }}>{species.scientific_name || species.key}</Box>}
                    titleId="scientificName"
                    subtitle={species.common_names.length > 0 ? species.common_names.join(', ') : undefined}
                    subtitleId="commonName"
                    fields={[
                      {
                        id: 'typicalDuration',
                        label: t('pages.phaseSequences.typicalDuration'),
                        value: t('pages.phaseSequences.totalDurationDays', { count: species.typical_duration_days }),
                      },
                    ]}
                  />
                )}
              />
            </CardContent>
          </Card>
        </Grid>
      </Grid>

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
        loading={deleting}
      />
    </Box>
  );
}
