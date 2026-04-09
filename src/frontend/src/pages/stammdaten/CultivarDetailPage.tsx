import { useEffect, useState, useCallback } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
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
import TableHead from '@mui/material/TableHead';
import TableRow from '@mui/material/TableRow';
import TextField from '@mui/material/TextField';
import Typography from '@mui/material/Typography';
import DeleteIcon from '@mui/icons-material/Delete';
import OpacityIcon from '@mui/icons-material/Opacity';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import PageTitle from '@/components/layout/PageTitle';
import LoadingSkeleton from '@/components/common/LoadingSkeleton';
import ErrorDisplay from '@/components/common/ErrorDisplay';
import ConfirmDialog from '@/components/common/ConfirmDialog';
import FormTextField from '@/components/form/FormTextField';
import FormNumberField from '@/components/form/FormNumberField';
import FormChipInput from '@/components/form/FormChipInput';
import FormActions from '@/components/form/FormActions';
import FormRow from '@/components/form/FormRow';
import UnsavedChangesGuard from '@/components/form/UnsavedChangesGuard';
import { useNotification } from '@/hooks/useNotification';
import { useApiError } from '@/hooks/useApiError';
import { useAppDispatch } from '@/store/hooks';
import { setBreadcrumbs } from '@/store/slices/uiSlice';
import * as api from '@/api/endpoints/species';
import * as phasesApi from '@/api/endpoints/phases';
import type { Cultivar, CultivarCreate, GrowthPhase, PlantTrait, Species } from '@/api/types';

const schema = z.object({
  name: z.string().min(1),
  breeder: z.string().nullable(),
  breeding_year: z.number().nullable(),
  traits: z.array(z.string()),
  patent_status: z.string(),
  days_to_maturity: z.number().min(1).max(365).nullable(),
  disease_resistances: z.array(z.string()),
});

type FormData = z.infer<typeof schema>;

/** Spacing between form panels (UI-NFR-008 R-039: 32px) */
const PANEL_GAP = 4;

export default function CultivarDetailPage() {
  const { speciesKey, cultivarKey } = useParams<{
    speciesKey: string;
    cultivarKey: string;
  }>();
  const { t } = useTranslation();
  const navigate = useNavigate();
  const dispatch = useAppDispatch();
  const notification = useNotification();
  const { handleError } = useApiError();
  const [cultivar, setCultivar] = useState<Cultivar | null>(null);
  const [species, setSpecies] = useState<Species | null>(null);
  const [growthPhases, setGrowthPhases] = useState<GrowthPhase[]>([]);
  const [phaseOverrides, setPhaseOverrides] = useState<Record<string, number | ''>>({});
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);
  const [savingOverrides, setSavingOverrides] = useState(false);
  const [deleteOpen, setDeleteOpen] = useState(false);

  const {
    control,
    handleSubmit,
    reset,
    formState: { isDirty },
  } = useForm<FormData>({
    resolver: zodResolver(schema),
    defaultValues: {
      name: '',
      breeder: null,
      breeding_year: null,
      traits: [],
      patent_status: '',
      days_to_maturity: null,
      disease_resistances: [],
    },
  });

  const load = async () => {
    if (!speciesKey || !cultivarKey) return;
    setLoading(true);
    try {
      const [c, s] = await Promise.all([
        api.getCultivar(speciesKey, cultivarKey),
        api.getSpecies(speciesKey),
      ]);
      setCultivar(c);
      setSpecies(s);
      reset({
        name: c.name,
        breeder: c.breeder,
        breeding_year: c.breeding_year,
        traits: c.traits,
        patent_status: c.patent_status,
        days_to_maturity: c.days_to_maturity,
        disease_resistances: c.disease_resistances,
      });

      // Load growth phases for phase watering overrides section
      try {
        const lc = await phasesApi.getLifecycleConfig(speciesKey);
        if (lc?.key) {
          const phases = await phasesApi.listGrowthPhases(lc.key);
          setGrowthPhases(phases);
        }
      } catch {
        // Lifecycle may not exist yet — that's fine
      }

      // Initialize override state from cultivar data
      const overrides: Record<string, number | ''> = {};
      if (c.phase_watering_overrides) {
        for (const [k, v] of Object.entries(c.phase_watering_overrides)) {
          overrides[k] = v;
        }
      }
      setPhaseOverrides(overrides);
    } catch (err) {
      setError(String(err));
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    load();
  }, [speciesKey, cultivarKey]); // eslint-disable-line react-hooks/exhaustive-deps

  // Dynamic breadcrumbs: Dashboard > Arten > {Species} > {Cultivar}
  useEffect(() => {
    if (!cultivar || !species) return;
    dispatch(
      setBreadcrumbs([
        { label: 'nav.dashboard', path: '/dashboard' },
        { label: 'nav.species', path: '/stammdaten/species' },
        {
          label: species.scientific_name,
          path: `/stammdaten/species/${speciesKey}`,
        },
        { label: cultivar.name },
      ]),
    );
  }, [cultivar, species, speciesKey, dispatch]);

  // Clear breadcrumbs on unmount
  useEffect(
    () => () => {
      dispatch(setBreadcrumbs([]));
    },
    [dispatch],
  );

  const onSubmit = async (data: FormData) => {
    if (!speciesKey || !cultivarKey) return;
    try {
      setSaving(true);
      await api.updateCultivar(speciesKey, cultivarKey, {
        ...data,
        traits: data.traits as PlantTrait[],
      } as Omit<CultivarCreate, 'species_key'>);
      notification.success(t('common.save'));
      load();
    } catch (err) {
      handleError(err);
    } finally {
      setSaving(false);
    }
  };

  const handleOverrideChange = useCallback((phaseName: string, value: string) => {
    setPhaseOverrides((prev) => ({
      ...prev,
      [phaseName]: value === '' ? '' : Number(value),
    }));
  }, []);

  const savePhaseOverrides = async () => {
    if (!speciesKey || !cultivarKey) return;
    try {
      setSavingOverrides(true);
      const overridesPayload: Record<string, number> = {};
      for (const [k, v] of Object.entries(phaseOverrides)) {
        if (v !== '' && typeof v === 'number' && v > 0) {
          overridesPayload[k] = v;
        }
      }
      await api.updateCultivar(speciesKey, cultivarKey, {
        phase_watering_overrides: Object.keys(overridesPayload).length > 0 ? overridesPayload : null,
      } as Omit<CultivarCreate, 'species_key'>);
      notification.success(t('common.saved'));
    } catch (err) {
      handleError(err);
    } finally {
      setSavingOverrides(false);
    }
  };

  const onDelete = async () => {
    if (!speciesKey || !cultivarKey) return;
    try {
      await api.deleteCultivar(speciesKey, cultivarKey);
      notification.success(t('common.delete'));
      navigate(`/stammdaten/species/${speciesKey}`);
    } catch (err) {
      handleError(err);
    }
    setDeleteOpen(false);
  };

  if (loading) return <LoadingSkeleton variant="form" />;
  if (error) return <ErrorDisplay error={error} onRetry={() => navigate(-1)} />;

  return (
    <Box data-testid="cultivar-detail-page">
      <UnsavedChangesGuard dirty={isDirty} />

      <PageTitle
        title={cultivar?.name ?? t('entities.cultivar')}
        action={
          <Button
            color="error"
            startIcon={<DeleteIcon />}
            onClick={() => setDeleteOpen(true)}
          >
            {t('common.delete')}
          </Button>
        }
      />

      {/* Species context chip */}
      {species && (
        <Chip
          label={species.scientific_name}
          size="small"
          variant="outlined"
          onClick={() => navigate(`/stammdaten/species/${speciesKey}`)}
          sx={{ mb: 2, cursor: 'pointer' }}
        />
      )}

      <Box
        component="form"
        onSubmit={handleSubmit(onSubmit)}
        sx={{ maxWidth: 900, display: 'flex', flexDirection: 'column', gap: PANEL_GAP }}
      >
        <Typography variant="body2" color="text.secondary">
          {t('pages.cultivars.editIntro')}
        </Typography>

        {/* ── Panel 1: Grunddaten ── */}
        {/* UI-NFR-008 R-037/R-038: Card panel with h6 heading, required fields first */}
        <Card variant="outlined">
          <CardContent component="fieldset" sx={{ border: 'none', p: 0, m: 0, '&:last-child': { pb: 2 }, px: 2, pt: 2 }}>
            <Typography component="legend" variant="h6" sx={{ pt: 1.5, mb: 0.5 }}>
              {t('pages.cultivars.sectionIdentification')}
            </Typography>
            <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
              {t('pages.cultivars.sectionIdentificationDesc')}
            </Typography>
            <FormTextField
              name="name"
              control={control}
              label={t('pages.cultivars.name')}
              helperText={t('pages.cultivars.nameHelper')}
              required
              autoFocus
            />
            <FormRow>
              <FormTextField
                name="breeder"
                control={control}
                label={t('pages.cultivars.breeder')}
                helperText={t('pages.cultivars.breederHelper')}
              />
              <FormNumberField
                name="breeding_year"
                control={control}
                label={t('pages.cultivars.breedingYear')}
                helperText={t('pages.cultivars.breedingYearHelper')}
              />
            </FormRow>
          </CardContent>
        </Card>

        {/* ── Panel 2: Eigenschaften ── */}
        <Card variant="outlined">
          <CardContent component="fieldset" sx={{ border: 'none', p: 0, m: 0, '&:last-child': { pb: 2 }, px: 2, pt: 2 }}>
            <Typography component="legend" variant="h6" sx={{ pt: 1.5, mb: 0.5 }}>
              {t('pages.cultivars.sectionCharacteristics')}
            </Typography>
            <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
              {t('pages.cultivars.sectionCharacteristicsDesc')}
            </Typography>
            <FormNumberField
              name="days_to_maturity"
              control={control}
              label={t('pages.cultivars.daysToMaturity')}
              helperText={t('pages.cultivars.daysToMaturityHelper')}
              min={1}
              max={365}
            />
            <FormChipInput
              name="traits"
              control={control}
              label={t('pages.cultivars.traits')}
              helperText={t('pages.cultivars.traitsHelper')}
            />
            <FormChipInput
              name="disease_resistances"
              control={control}
              label={t('pages.cultivars.diseaseResistances')}
              helperText={t('pages.cultivars.diseaseResistancesHelper')}
            />
            <FormTextField
              name="patent_status"
              control={control}
              label={t('pages.cultivars.patentStatus')}
              helperText={t('pages.cultivars.patentStatusHelper')}
            />
          </CardContent>
        </Card>

        {/* UI-NFR-008 R-025: Required field legend */}
        <Typography variant="caption" color="text.secondary">
          * {t('common.required')}
        </Typography>

        <FormActions
          onCancel={() => navigate(`/stammdaten/species/${speciesKey}`)}
          loading={saving}
        />
      </Box>

      {/* Phase watering overrides */}
      {growthPhases.length > 0 && (
        <Paper sx={{ mt: 4, p: 2 }}>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 2 }}>
            <OpacityIcon color="primary" />
            <Typography variant="h6">
              {t('pages.cultivars.phaseWateringOverrides')}
            </Typography>
          </Box>
          <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
            {t('pages.cultivars.phaseWateringOverridesHelper')}
          </Typography>
          <Table size="small">
            <TableHead>
              <TableRow>
                <TableCell>{t('pages.growthPhases.name')}</TableCell>
                <TableCell sx={{ width: 160 }}>{t('pages.growthPhases.duration')}</TableCell>
                <TableCell sx={{ width: 160 }}>{t('pages.growthPhases.wateringIntervalDefault')}</TableCell>
                <TableCell sx={{ width: 160 }}>{t('pages.cultivars.overrideInterval')}</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {growthPhases.map((gp) => (
                <TableRow key={gp.key}>
                  <TableCell>{gp.display_name || gp.name}</TableCell>
                  <TableCell>{gp.typical_duration_days} {t('common.days')}</TableCell>
                  <TableCell>
                    {gp.watering_interval_days
                      ? `${gp.watering_interval_days} ${t('common.days')}`
                      : '\u2014'}
                  </TableCell>
                  <TableCell>
                    <TextField
                      type="number"
                      size="small"
                      value={phaseOverrides[gp.name] ?? ''}
                      onChange={(e) => handleOverrideChange(gp.name, e.target.value)}
                      placeholder={String(gp.watering_interval_days ?? '')}
                      slotProps={{ htmlInput: { min: 1, max: 90, step: 1 } }}
                      sx={{ width: 120 }}
                      data-testid={`phase-override-${gp.name}`}
                    />
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
          <Box sx={{ mt: 2, display: 'flex', justifyContent: 'flex-end' }}>
            <Button
              variant="contained"
              size="small"
              onClick={savePhaseOverrides}
              disabled={savingOverrides}
            >
              {t('common.save')}
            </Button>
          </Box>
        </Paper>
      )}

      <ConfirmDialog
        open={deleteOpen}
        title={t('common.delete')}
        message={t('common.deleteConfirm', { name: cultivar?.name })}
        onConfirm={onDelete}
        onCancel={() => setDeleteOpen(false)}
        destructive
      />
    </Box>
  );
}
