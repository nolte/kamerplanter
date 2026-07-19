import { useEffect, useState } from 'react';
import { useTranslation } from 'react-i18next';
import { Link as RouterLink } from 'react-router-dom';
import Box from '@mui/material/Box';
import Button from '@mui/material/Button';
import Card from '@mui/material/Card';
import CardContent from '@mui/material/CardContent';
import CardHeader from '@mui/material/CardHeader';
import Chip from '@mui/material/Chip';
import Dialog from '@mui/material/Dialog';
import DialogActions from '@mui/material/DialogActions';
import DialogContent from '@mui/material/DialogContent';
import DialogContentText from '@mui/material/DialogContentText';
import DialogTitle from '@mui/material/DialogTitle';
import Link from '@mui/material/Link';
import List from '@mui/material/List';
import ListItem from '@mui/material/ListItem';
import ListItemText from '@mui/material/ListItemText';
import MenuItem from '@mui/material/MenuItem';
import TextField from '@mui/material/TextField';
import Typography from '@mui/material/Typography';
import AddIcon from '@mui/icons-material/Add';
import CancelIcon from '@mui/icons-material/Cancel';
import CheckCircleIcon from '@mui/icons-material/CheckCircle';
import LoadingSkeleton from '@/components/common/LoadingSkeleton';
import EmptyState from '@/components/common/EmptyState';
import { useNotification } from '@/hooks/useNotification';
import { useApiError } from '@/hooks/useApiError';
import * as api from '@/api/endpoints/species';
import * as companionApi from '@/api/endpoints/companionPlanting';
import type { CompatibleSpecies, IncompatibleSpecies, Species } from '@/api/types';
import { getPrimaryCommonName } from '@/utils/plantDisplay';
import { kamiMasterdata } from '@/assets/brand/illustrations';

interface SpeciesCompanionTabProps {
  speciesKey: string;
  speciesName: string;
  fullScreen: boolean;
}

/**
 * Companion-planting (Mischkultur) tab — expert-only (U-4). Self-contained:
 * loads the compatible/incompatible relations when it mounts (i.e. when the tab
 * becomes active), matching the former tab-activation effect.
 */
export default function SpeciesCompanionTab({
  speciesKey,
  speciesName,
  fullScreen,
}: SpeciesCompanionTabProps) {
  const { t } = useTranslation();
  const notification = useNotification();
  const { handleError } = useApiError();

  const [companionSpeciesList, setCompanionSpeciesList] = useState<Species[]>([]);
  const [compatible, setCompatible] = useState<CompatibleSpecies[]>([]);
  const [incompatible, setIncompatible] = useState<IncompatibleSpecies[]>([]);
  const [companionLoading, setCompanionLoading] = useState(false);
  const [companionDialogType, setCompanionDialogType] = useState<
    'compatible' | 'incompatible' | null
  >(null);
  const [companionTargetKey, setCompanionTargetKey] = useState('');
  const [companionScore, setCompanionScore] = useState(1);
  const [companionReason, setCompanionReason] = useState('');

  useEffect(() => {
    if (speciesKey) {
      setCompanionLoading(true);
      api
        .listSpecies(0, 200)
        .then((r) => setCompanionSpeciesList(r.items))
        .catch(() => {});
      Promise.all([
        companionApi.getCompatibleSpecies(speciesKey),
        companionApi.getIncompatibleSpecies(speciesKey),
      ])
        .then(([comp, incomp]) => {
          setCompatible(comp);
          setIncompatible(incomp);
        })
        .catch((err) => handleError(err))
        .finally(() => setCompanionLoading(false));
    }
  }, [speciesKey, handleError]);

  const reloadCompanionRelations = async () => {
    try {
      const [comp, incomp] = await Promise.all([
        companionApi.getCompatibleSpecies(speciesKey),
        companionApi.getIncompatibleSpecies(speciesKey),
      ]);
      setCompatible(comp);
      setIncompatible(incomp);
    } catch (err) {
      handleError(err);
    }
  };

  const handleAddCompanion = async () => {
    if (!companionTargetKey) return;
    try {
      if (companionDialogType === 'compatible') {
        await companionApi.setCompatible({
          from_species_key: speciesKey,
          to_species_key: companionTargetKey,
          score: companionScore,
        });
      } else {
        await companionApi.setIncompatible({
          from_species_key: speciesKey,
          to_species_key: companionTargetKey,
          reason: companionReason,
        });
      }
      notification.success(t('common.create'));
      reloadCompanionRelations();
    } catch (err) {
      handleError(err);
    }
    setCompanionDialogType(null);
    setCompanionTargetKey('');
  };

  return (
    <>
      <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
        {t('pages.species.companionPlantingIntro', { name: speciesName })}
      </Typography>

      {companionLoading && <LoadingSkeleton variant="card" />}

      {!companionLoading && (
        <Box sx={{ display: 'flex', gap: 3, flexWrap: 'wrap' }}>
          {/* Compatible species */}
          <Card sx={{ flex: 1, minWidth: 300 }} variant="outlined">
            <CardHeader
              title={
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                  <CheckCircleIcon fontSize="small" color="success" />
                  <Typography variant="subtitle1">
                    {t('pages.companionPlanting.compatible')}
                  </Typography>
                  {compatible.length > 0 && (
                    <Chip
                      label={compatible.length}
                      size="small"
                      color="success"
                      variant="outlined"
                    />
                  )}
                </Box>
              }
              action={
                <Button
                  size="small"
                  startIcon={<AddIcon />}
                  onClick={() => setCompanionDialogType('compatible')}
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
                  {compatible.map((c) => {
                    const commonName =
                      getPrimaryCommonName(c.common_names, c.scientific_name) ?? c.species_key;
                    const showScientific =
                      !!c.scientific_name && c.scientific_name !== commonName;
                    return (
                      <ListItem key={c.species_key} divider>
                        <ListItemText
                          primary={
                            <Link
                              component={RouterLink}
                              to={`/stammdaten/species/${c.species_key}`}
                              variant="body2"
                              underline="hover"
                            >
                              {commonName}
                            </Link>
                          }
                          secondary={showScientific ? c.scientific_name : undefined}
                          slotProps={{
                            secondary: { variant: 'caption', sx: { fontStyle: 'italic' } },
                          }}
                        />
                        <Chip
                          label={`${t('pages.companionPlanting.score')}: ${c.score}`}
                          size="small"
                          color="success"
                          variant="outlined"
                        />
                      </ListItem>
                    );
                  })}
                </List>
              )}
            </CardContent>
          </Card>

          {/* Incompatible species */}
          <Card sx={{ flex: 1, minWidth: 300 }} variant="outlined">
            <CardHeader
              title={
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                  <CancelIcon fontSize="small" color="error" />
                  <Typography variant="subtitle1">
                    {t('pages.companionPlanting.incompatible')}
                  </Typography>
                  {incompatible.length > 0 && (
                    <Chip
                      label={incompatible.length}
                      size="small"
                      color="error"
                      variant="outlined"
                    />
                  )}
                </Box>
              }
              action={
                <Button
                  size="small"
                  startIcon={<AddIcon />}
                  onClick={() => setCompanionDialogType('incompatible')}
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
                  {incompatible.map((c) => {
                    const commonName =
                      getPrimaryCommonName(c.common_names, c.scientific_name) ?? c.species_key;
                    const showScientific =
                      !!c.scientific_name && c.scientific_name !== commonName;
                    return (
                      <ListItem key={c.species_key} divider>
                        <ListItemText
                          primary={
                            <Link
                              component={RouterLink}
                              to={`/stammdaten/species/${c.species_key}`}
                              variant="body2"
                              underline="hover"
                            >
                              {commonName}
                            </Link>
                          }
                          secondary={
                            showScientific || c.reason ? (
                              <>
                                {showScientific && (
                                  <Typography
                                    component="span"
                                    variant="caption"
                                    color="text.secondary"
                                    sx={{ display: 'block', fontStyle: 'italic' }}
                                  >
                                    {c.scientific_name}
                                  </Typography>
                                )}
                                {c.reason && (
                                  <Typography
                                    component="span"
                                    variant="caption"
                                    color="text.secondary"
                                    sx={{ display: 'block' }}
                                  >
                                    {c.reason}
                                  </Typography>
                                )}
                              </>
                            ) : undefined
                          }
                          slotProps={{ secondary: { component: 'div' } }}
                        />
                      </ListItem>
                    );
                  })}
                </List>
              )}
            </CardContent>
          </Card>
        </Box>
      )}

      {/* Companion planting dialog */}
      <Dialog
        fullScreen={fullScreen}
        open={!!companionDialogType}
        onClose={() => setCompanionDialogType(null)}
        maxWidth="sm"
        fullWidth
      >
        <DialogTitle>
          {companionDialogType === 'compatible'
            ? t('pages.companionPlanting.addCompatible')
            : t('pages.companionPlanting.addIncompatible')}
        </DialogTitle>
        <DialogContent>
          <DialogContentText sx={{ mb: 2 }}>
            {companionDialogType === 'compatible'
              ? t('pages.companionPlanting.addCompatibleHint')
              : t('pages.companionPlanting.addIncompatibleHint')}
          </DialogContentText>
          <TextField
            select
            fullWidth
            label={t('pages.companionPlanting.selectSpecies')}
            value={companionTargetKey}
            onChange={(e) => setCompanionTargetKey(e.target.value)}
            helperText={t('pages.companionPlanting.targetSpeciesHelper')}
            sx={{ mt: 1, mb: 2 }}
            data-testid="target-species-select"
          >
            {companionSpeciesList
              .filter((s) => s.key !== speciesKey)
              .map((s) => (
                <MenuItem key={s.key} value={s.key}>
                  {s.scientific_name}
                </MenuItem>
              ))}
          </TextField>
          {companionDialogType === 'compatible' && (
            <TextField
              type="number"
              label={t('pages.companionPlanting.score')}
              value={companionScore}
              onChange={(e) => setCompanionScore(Number(e.target.value))}
              fullWidth
              helperText={t('pages.companionPlanting.scoreHelper')}
              slotProps={{ htmlInput: { min: 0, max: 1, step: 0.1 } }}
              data-testid="score-input"
            />
          )}
          {companionDialogType === 'incompatible' && (
            <TextField
              label={t('pages.companionPlanting.reason')}
              value={companionReason}
              onChange={(e) => setCompanionReason(e.target.value)}
              fullWidth
              helperText={t('pages.companionPlanting.reasonHelper')}
              multiline
              rows={2}
              data-testid="reason-input"
            />
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setCompanionDialogType(null)}>{t('common.cancel')}</Button>
          <Button variant="contained" onClick={handleAddCompanion} disabled={!companionTargetKey}>
            {t('common.create')}
          </Button>
        </DialogActions>
      </Dialog>
    </>
  );
}
