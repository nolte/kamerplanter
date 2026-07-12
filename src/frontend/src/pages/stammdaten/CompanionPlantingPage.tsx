import { useEffect, useMemo, useState } from 'react';
import { useTranslation } from 'react-i18next';
import Box from '@mui/material/Box';
import Typography from '@mui/material/Typography';
import TextField from '@mui/material/TextField';
import MenuItem from '@mui/material/MenuItem';
import Autocomplete from '@mui/material/Autocomplete';
import { visuallyHidden } from '@mui/utils';
import Button from '@mui/material/Button';
import Card from '@mui/material/Card';
import CardContent from '@mui/material/CardContent';
import CardHeader from '@mui/material/CardHeader';
import List from '@mui/material/List';
import ListItem from '@mui/material/ListItem';
import ListItemText from '@mui/material/ListItemText';
import Chip from '@mui/material/Chip';
import Dialog from '@mui/material/Dialog';
import useMediaQuery from '@mui/material/useMediaQuery';
import { useTheme } from '@mui/material/styles';
import DialogTitle from '@mui/material/DialogTitle';
import DialogContent from '@mui/material/DialogContent';
import DialogContentText from '@mui/material/DialogContentText';
import DialogActions from '@mui/material/DialogActions';
import CheckCircleIcon from '@mui/icons-material/CheckCircle';
import CancelIcon from '@mui/icons-material/Cancel';
import AddIcon from '@mui/icons-material/Add';
import PageTitle from '@/components/layout/PageTitle';
import LoadingSkeleton from '@/components/common/LoadingSkeleton';
import EmptyState from '@/components/common/EmptyState';
import { useNotification } from '@/hooks/useNotification';
import { useApiError } from '@/hooks/useApiError';
import * as companionApi from '@/api/endpoints/companionPlanting';
import * as speciesApi from '@/api/endpoints/species';
import type {
  Species,
  CompatibleSpecies,
  IncompatibleSpecies,
  CompanionCountsMap,
} from '@/api/types';
import { kamiMasterdata } from '@/assets/brand/illustrations';

export default function CompanionPlantingPage() {
  const theme = useTheme();
  const fullScreen = useMediaQuery(theme.breakpoints.down('sm'));
  const { t } = useTranslation();
  const notification = useNotification();
  const { handleError } = useApiError();
  const [speciesList, setSpeciesList] = useState<Species[]>([]);
  const [companionCounts, setCompanionCounts] = useState<CompanionCountsMap>({});
  const [selectedKey, setSelectedKey] = useState('');
  const [compatible, setCompatible] = useState<CompatibleSpecies[]>([]);
  const [incompatible, setIncompatible] = useState<IncompatibleSpecies[]>([]);
  const [loading, setLoading] = useState(false);
  const [dialogType, setDialogType] = useState<'compatible' | 'incompatible' | null>(null);
  const [targetKey, setTargetKey] = useState('');
  const [score, setScore] = useState(1);
  const [reason, setReason] = useState('');

  useEffect(() => {
    speciesApi.listSpecies(0, 200).then((r) => setSpeciesList(r.items)).catch(() => {});
    // Whole-catalogue companion counts in one aggregate request (no N+1) so the
    // dropdown can badge every option before the user selects anything.
    companionApi.getCompanionCounts().then(setCompanionCounts).catch(() => {});
  }, []);

  // Stable lookup of the resolved count summary per species — memoised so the
  // Autocomplete option renderer and the selected value derive from the same
  // reference (custom-object convention, FRONTEND.md).
  const selectedSpecies = useMemo(
    () => speciesList.find((s) => s.key === selectedKey) ?? null,
    [speciesList, selectedKey],
  );

  const loadRelations = async (key: string) => {
    setLoading(true);
    try {
      const [comp, incomp] = await Promise.all([
        companionApi.getCompatibleSpecies(key),
        companionApi.getIncompatibleSpecies(key),
      ]);
      setCompatible(comp);
      setIncompatible(incomp);
    } catch (err) {
      handleError(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (selectedKey) loadRelations(selectedKey);
  }, [selectedKey]); // eslint-disable-line react-hooks/exhaustive-deps

  const handleAdd = async () => {
    if (!selectedKey || !targetKey) return;
    try {
      if (dialogType === 'compatible') {
        await companionApi.setCompatible({ from_species_key: selectedKey, to_species_key: targetKey, score });
      } else {
        await companionApi.setIncompatible({ from_species_key: selectedKey, to_species_key: targetKey, reason });
      }
      notification.success(t('common.create'));
      loadRelations(selectedKey);
    } catch (err) {
      handleError(err);
    }
    setDialogType(null);
    setTargetKey('');
  };

  return (
    <>
      <PageTitle title={t('pages.companionPlanting.title')} />

      <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
        {t('pages.companionPlanting.intro')}
      </Typography>

      <Autocomplete
        fullWidth
        options={speciesList}
        value={selectedSpecies}
        onChange={(_e, option) => setSelectedKey(option?.key ?? '')}
        getOptionLabel={(option) => option.scientific_name}
        isOptionEqualToValue={(option, value) => option.key === value.key}
        noOptionsText={t('pages.companionPlanting.noSpeciesFound')}
        sx={{ maxWidth: 480, mb: 1 }}
        renderOption={({ key: optionKey, ...optionProps }, option) => {
          const counts = companionCounts[option.key] ?? { compatible: 0, incompatible: 0 };
          const hasRelations = counts.compatible > 0 || counts.incompatible > 0;
          return (
            <Box
              component="li"
              key={optionKey}
              {...optionProps}
              sx={{
                display: 'flex',
                alignItems: 'center',
                gap: 1,
                justifyContent: 'space-between',
                minHeight: 48,
              }}
              data-testid={`species-option-${option.key}`}
              data-has-relations={hasRelations}
            >
              {/* De-emphasis uses a plain secondary text colour, never `text.disabled` —
                  these 0/0 options remain fully selectable and keyboard-reachable, so
                  they must not visually read as disabled (UI-NFR-002). The count chips
                  stay at full opacity: an explicit "0" is useful information on its own
                  and must stay legible. */}
              <Typography
                variant="body2"
                noWrap
                color={hasRelations ? 'text.primary' : 'text.secondary'}
                sx={{ flex: 1, minWidth: 0 }}
              >
                {option.scientific_name}
              </Typography>
              {/* Visual badge cluster: icon + number (not colour alone). Hidden
                  from the a11y tree — the readable summary below carries the
                  same information as text for screen readers. */}
              <Box sx={{ display: 'flex', gap: 0.5, alignItems: 'center' }} aria-hidden>
                <Chip
                  icon={<CheckCircleIcon />}
                  label={counts.compatible}
                  size="small"
                  color="success"
                  variant="outlined"
                  data-testid={`species-option-compatible-${option.key}`}
                />
                <Chip
                  icon={<CancelIcon />}
                  label={counts.incompatible}
                  size="small"
                  color="error"
                  variant="outlined"
                  data-testid={`species-option-incompatible-${option.key}`}
                />
              </Box>
              <Box component="span" sx={visuallyHidden}>
                {t('pages.companionPlanting.optionCountSummary', {
                  compatible: counts.compatible,
                  incompatible: counts.incompatible,
                })}
              </Box>
            </Box>
          );
        }}
        renderInput={(params) => (
          <TextField
            {...params}
            label={t('pages.companionPlanting.selectSpecies')}
            helperText={t('pages.companionPlanting.selectSpeciesHelper')}
            data-testid="species-select"
          />
        )}
      />

      {/* Persistent legend (not hover-dependent, so it works on touch too) mapping
          the icon + colour badges rendered in the dropdown to their meaning for
          non-expert users (UI-NFR-008/011 descriptive-text obligation). */}
      <Box sx={{ display: 'flex', gap: 2, flexWrap: 'wrap', alignItems: 'center', mb: 3 }}>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
          <CheckCircleIcon fontSize="small" color="success" />
          <Typography variant="caption" color="text.secondary">
            {t('pages.companionPlanting.optionCountLegendCompatible')}
          </Typography>
        </Box>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
          <CancelIcon fontSize="small" color="error" />
          <Typography variant="caption" color="text.secondary">
            {t('pages.companionPlanting.optionCountLegendIncompatible')}
          </Typography>
        </Box>
      </Box>

      {loading && <LoadingSkeleton variant="card" />}

      {!selectedKey && !loading && (
        <EmptyState
          illustration={kamiMasterdata}
          message={t('pages.companionPlanting.selectSpeciesHint')}
        />
      )}

      {selectedKey && !loading && (
        <Box sx={{ display: 'flex', gap: 3, flexWrap: 'wrap' }}>
          <Card sx={{ flex: 1, minWidth: 300 }} variant="outlined">
            <CardHeader
              title={
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                  <CheckCircleIcon fontSize="small" color="success" />
                  <Typography variant="subtitle1">
                    {t('pages.companionPlanting.compatible')}
                  </Typography>
                  {compatible.length > 0 && (
                    <Chip label={compatible.length} size="small" color="success" variant="outlined" />
                  )}
                </Box>
              }
              action={
                <Button
                  size="small"
                  startIcon={<AddIcon />}
                  onClick={() => setDialogType('compatible')}
                  data-testid="add-compatible-button"
                >
                  {t('pages.companionPlanting.addCompatible')}
                </Button>
              }
              sx={{ pb: 0 }}
            />
            <CardContent>
              {compatible.length === 0 ? (
                <EmptyState
                  illustration={kamiMasterdata}
                  message={t('pages.companionPlanting.noCompatible')}
                />
              ) : (
                <List dense disablePadding>
                  {compatible.map((c) => (
                    <ListItem key={c.species_key} divider>
                      <ListItemText
                        primary={c.scientific_name ?? c.species_key} slotProps={{ primary: { variant: 'body2' } }} />
                      <Chip
                        label={`${t('pages.companionPlanting.score')}: ${c.score}`}
                        size="small"
                        color="success"
                        variant="outlined"
                      />
                    </ListItem>
                  ))}
                </List>
              )}
            </CardContent>
          </Card>

          <Card sx={{ flex: 1, minWidth: 300 }} variant="outlined">
            <CardHeader
              title={
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                  <CancelIcon fontSize="small" color="error" />
                  <Typography variant="subtitle1">
                    {t('pages.companionPlanting.incompatible')}
                  </Typography>
                  {incompatible.length > 0 && (
                    <Chip label={incompatible.length} size="small" color="error" variant="outlined" />
                  )}
                </Box>
              }
              action={
                <Button
                  size="small"
                  startIcon={<AddIcon />}
                  onClick={() => setDialogType('incompatible')}
                  data-testid="add-incompatible-button"
                >
                  {t('pages.companionPlanting.addIncompatible')}
                </Button>
              }
              sx={{ pb: 0 }}
            />
            <CardContent>
              {incompatible.length === 0 ? (
                <EmptyState
                  illustration={kamiMasterdata}
                  message={t('pages.companionPlanting.noIncompatible')}
                />
              ) : (
                <List dense disablePadding>
                  {incompatible.map((c) => (
                    <ListItem key={c.species_key} divider>
                      <ListItemText
                        primary={c.scientific_name ?? c.species_key}
                        secondary={c.reason || undefined} slotProps={{ primary: { variant: 'body2' }, secondary: { variant: 'caption' } }} />
                    </ListItem>
                  ))}
                </List>
              )}
            </CardContent>
          </Card>
        </Box>
      )}

      <Dialog fullScreen={fullScreen} open={!!dialogType} onClose={() => setDialogType(null)} maxWidth="sm" fullWidth>
        <DialogTitle>
          {dialogType === 'compatible'
            ? t('pages.companionPlanting.addCompatible')
            : t('pages.companionPlanting.addIncompatible')}
        </DialogTitle>
        <DialogContent>
          <DialogContentText sx={{ mb: 2 }}>
            {dialogType === 'compatible'
              ? t('pages.companionPlanting.addCompatibleHint')
              : t('pages.companionPlanting.addIncompatibleHint')}
          </DialogContentText>
          <TextField
            select
            fullWidth
            label={t('pages.companionPlanting.selectSpecies')}
            value={targetKey}
            onChange={(e) => setTargetKey(e.target.value)}
            helperText={t('pages.companionPlanting.targetSpeciesHelper')}
            sx={{ mt: 1, mb: 2 }}
            data-testid="target-species-select"
          >
            {speciesList.filter((s) => s.key !== selectedKey).map((s) => (
              <MenuItem key={s.key} value={s.key}>{s.scientific_name}</MenuItem>
            ))}
          </TextField>
          {dialogType === 'compatible' && (
            <TextField
              type="number"
              label={t('pages.companionPlanting.score')}
              value={score}
              onChange={(e) => setScore(Number(e.target.value))}
              fullWidth
              helperText={t('pages.companionPlanting.scoreHelper')}
              slotProps={{ htmlInput: { min: 0, max: 1, step: 0.1 } }}
              data-testid="score-input"
            />
          )}
          {dialogType === 'incompatible' && (
            <TextField
              label={t('pages.companionPlanting.reason')}
              value={reason}
              onChange={(e) => setReason(e.target.value)}
              fullWidth
              helperText={t('pages.companionPlanting.reasonHelper')}
              multiline
              rows={2}
              data-testid="reason-input"
            />
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setDialogType(null)}>{t('common.cancel')}</Button>
          <Button variant="contained" onClick={handleAdd} disabled={!targetKey}>
            {t('common.create')}
          </Button>
        </DialogActions>
      </Dialog>
    </>
  );
}
