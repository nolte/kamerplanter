import { useEffect, useState } from 'react';
import { useTranslation } from 'react-i18next';
import Box from '@mui/material/Box';
import Typography from '@mui/material/Typography';
import TextField from '@mui/material/TextField';
import MenuItem from '@mui/material/MenuItem';
import Button from '@mui/material/Button';
import Card from '@mui/material/Card';
import CardContent from '@mui/material/CardContent';
import List from '@mui/material/List';
import ListItem from '@mui/material/ListItem';
import ListItemText from '@mui/material/ListItemText';
import Chip from '@mui/material/Chip';
import Dialog from '@mui/material/Dialog';
import DialogTitle from '@mui/material/DialogTitle';
import DialogContent from '@mui/material/DialogContent';
import DialogActions from '@mui/material/DialogActions';
import PageTitle from '@/components/layout/PageTitle';
import LoadingSkeleton from '@/components/common/LoadingSkeleton';
import EmptyState from '@/components/common/EmptyState';
import { useNotification } from '@/hooks/useNotification';
import { useApiError } from '@/hooks/useApiError';
import * as companionApi from '@/api/endpoints/companionPlanting';
import * as speciesApi from '@/api/endpoints/species';
import type { Species, CompatibleSpecies, IncompatibleSpecies } from '@/api/types';

export default function CompanionPlantingPage() {
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

      <TextField
        select
        label={t('pages.companionPlanting.selectSpecies')}
        value={selectedKey}
        onChange={(e) => setSelectedKey(e.target.value)}
        sx={{ minWidth: 300, mb: 3 }}
      >
        {speciesList.map((s) => (
          <MenuItem key={s.key} value={s.key}>{s.scientific_name}</MenuItem>
        ))}
      </TextField>

      {loading && <LoadingSkeleton variant="card" />}

      {selectedKey && !loading && (
        <Box sx={{ display: 'flex', gap: 3, flexWrap: 'wrap' }}>
          <Card sx={{ flex: 1, minWidth: 300 }}>
            <CardContent>
              <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 2 }}>
                <Typography variant="h6">{t('pages.companionPlanting.compatible')}</Typography>
                <Button size="small" onClick={() => setDialogType('compatible')}>
                  {t('pages.companionPlanting.addCompatible')}
                </Button>
              </Box>
              {compatible.length === 0 ? (
                <EmptyState />
              ) : (
                <List dense>
                  {compatible.map((c) => (
                    <ListItem key={c.species_key}>
                      <ListItemText primary={c.scientific_name ?? c.species_key} />
                      <Chip label={`${c.score}`} size="small" color="success" />
                    </ListItem>
                  ))}
                </List>
              )}
            </CardContent>
          </Card>

          <Card sx={{ flex: 1, minWidth: 300 }}>
            <CardContent>
              <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 2 }}>
                <Typography variant="h6">{t('pages.companionPlanting.incompatible')}</Typography>
                <Button size="small" onClick={() => setDialogType('incompatible')}>
                  {t('pages.companionPlanting.addIncompatible')}
                </Button>
              </Box>
              {incompatible.length === 0 ? (
                <EmptyState />
              ) : (
                <List dense>
                  {incompatible.map((c) => (
                    <ListItem key={c.species_key}>
                      <ListItemText primary={c.scientific_name ?? c.species_key} secondary={c.reason} />
                    </ListItem>
                  ))}
                </List>
              )}
            </CardContent>
          </Card>
        </Box>
      )}

      <Dialog open={!!dialogType} onClose={() => setDialogType(null)} maxWidth="sm" fullWidth>
        <DialogTitle>
          {dialogType === 'compatible'
            ? t('pages.companionPlanting.addCompatible')
            : t('pages.companionPlanting.addIncompatible')}
        </DialogTitle>
        <DialogContent>
          <TextField
            select
            fullWidth
            label={t('pages.companionPlanting.selectSpecies')}
            value={targetKey}
            onChange={(e) => setTargetKey(e.target.value)}
            sx={{ mt: 1, mb: 2 }}
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
              inputProps={{ min: 0, max: 1, step: 0.1 }}
            />
          )}
          {dialogType === 'incompatible' && (
            <TextField
              label={t('pages.companionPlanting.reason')}
              value={reason}
              onChange={(e) => setReason(e.target.value)}
              fullWidth
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
