import { useEffect, useState } from 'react';
import { useTranslation } from 'react-i18next';
import Box from '@mui/material/Box';
import Typography from '@mui/material/Typography';
import TextField from '@mui/material/TextField';
import MenuItem from '@mui/material/MenuItem';
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
import type { Species, CompatibleSpecies, IncompatibleSpecies } from '@/api/types';
import { kamiMasterdata } from '@/assets/brand/illustrations';

export default function CompanionPlantingPage() {
  const theme = useTheme();
  const fullScreen = useMediaQuery(theme.breakpoints.down('sm'));
  const { t } = useTranslation();
  const notification = useNotification();
  const { handleError } = useApiError();
  const [speciesList, setSpeciesList] = useState<Species[]>([]);
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
  }, []);

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

      <TextField
        select
        label={t('pages.companionPlanting.selectSpecies')}
        value={selectedKey}
        onChange={(e) => setSelectedKey(e.target.value)}
        helperText={t('pages.companionPlanting.selectSpeciesHelper')}
        sx={{ minWidth: 300, mb: 3 }}
        data-testid="species-select"
      >
        {speciesList.map((s) => (
          <MenuItem key={s.key} value={s.key}>{s.scientific_name}</MenuItem>
        ))}
      </TextField>

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
                        primary={c.scientific_name ?? c.species_key}
                        primaryTypographyProps={{ variant: 'body2' }}
                      />
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
                        secondary={c.reason || undefined}
                        primaryTypographyProps={{ variant: 'body2' }}
                        secondaryTypographyProps={{ variant: 'caption' }}
                      />
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
              inputProps={{ min: 0, max: 1, step: 0.1 }}
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
