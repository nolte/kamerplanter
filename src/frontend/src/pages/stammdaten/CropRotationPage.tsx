import { useEffect, useState } from 'react';
import { useTranslation } from 'react-i18next';
import Box from '@mui/material/Box';
import TextField from '@mui/material/TextField';
import MenuItem from '@mui/material/MenuItem';
import Button from '@mui/material/Button';
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
import * as rotationApi from '@/api/endpoints/cropRotation';
import * as familiesApi from '@/api/endpoints/botanicalFamilies';
import type { BotanicalFamily, RotationSuccessor } from '@/api/types';

export default function CropRotationPage() {
  const { t } = useTranslation();
  const notification = useNotification();
  const { handleError } = useApiError();
  const [families, setFamilies] = useState<BotanicalFamily[]>([]);
  const [selectedKey, setSelectedKey] = useState('');
  const [successors, setSuccessors] = useState<RotationSuccessor[]>([]);
  const [loading, setLoading] = useState(false);
  const [dialogOpen, setDialogOpen] = useState(false);
  const [targetKey, setTargetKey] = useState('');
  const [waitYears, setWaitYears] = useState(3);

  useEffect(() => {
    familiesApi.listBotanicalFamilies().then(setFamilies).catch(() => {});
  }, []);

  useEffect(() => {
    if (!selectedKey) return;
    setLoading(true);
    rotationApi
      .getSuccessors(selectedKey)
      .then(setSuccessors)
      .catch((err) => handleError(err))
      .finally(() => setLoading(false));
  }, [selectedKey]); // eslint-disable-line react-hooks/exhaustive-deps

  const handleAdd = async () => {
    if (!selectedKey || !targetKey) return;
    try {
      await rotationApi.setSuccessor({
        from_family_key: selectedKey,
        to_family_key: targetKey,
        wait_years: waitYears,
      });
      notification.success(t('common.create'));
      const updated = await rotationApi.getSuccessors(selectedKey);
      setSuccessors(updated);
    } catch (err) {
      handleError(err);
    }
    setDialogOpen(false);
    setTargetKey('');
  };

  return (
    <>
      <PageTitle title={t('pages.cropRotation.title')} />

      <TextField
        select
        label={t('pages.cropRotation.fromFamily')}
        value={selectedKey}
        onChange={(e) => setSelectedKey(e.target.value)}
        sx={{ minWidth: 300, mb: 3 }}
      >
        {families.map((f) => (
          <MenuItem key={f.key} value={f.key}>{f.name}</MenuItem>
        ))}
      </TextField>

      {loading && <LoadingSkeleton variant="card" />}

      {selectedKey && !loading && (
        <Box>
          <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
            <Box />
            <Button onClick={() => setDialogOpen(true)}>
              {t('pages.cropRotation.addSuccessor')}
            </Button>
          </Box>
          {successors.length === 0 ? (
            <EmptyState />
          ) : (
            <List>
              {successors.map((s) => (
                <ListItem key={s.family_key}>
                  <ListItemText primary={s.name ?? s.family_key} />
                  <Chip label={`${s.wait_years} ${t('pages.cropRotation.waitYears')}`} size="small" />
                </ListItem>
              ))}
            </List>
          )}
        </Box>
      )}

      <Dialog open={dialogOpen} onClose={() => setDialogOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>{t('pages.cropRotation.addSuccessor')}</DialogTitle>
        <DialogContent>
          <TextField
            select
            fullWidth
            label={t('pages.cropRotation.toFamily')}
            value={targetKey}
            onChange={(e) => setTargetKey(e.target.value)}
            sx={{ mt: 1, mb: 2 }}
          >
            {families.filter((f) => f.key !== selectedKey).map((f) => (
              <MenuItem key={f.key} value={f.key}>{f.name}</MenuItem>
            ))}
          </TextField>
          <TextField
            type="number"
            label={t('pages.cropRotation.waitYears')}
            value={waitYears}
            onChange={(e) => setWaitYears(Number(e.target.value))}
            fullWidth
            inputProps={{ min: 1, max: 10 }}
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setDialogOpen(false)}>{t('common.cancel')}</Button>
          <Button variant="contained" onClick={handleAdd} disabled={!targetKey}>
            {t('common.create')}
          </Button>
        </DialogActions>
      </Dialog>
    </>
  );
}
