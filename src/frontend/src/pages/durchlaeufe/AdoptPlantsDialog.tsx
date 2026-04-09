import { useState, useEffect, useMemo } from 'react';
import { useTranslation } from 'react-i18next';
import Dialog from '@mui/material/Dialog';
import DialogTitle from '@mui/material/DialogTitle';
import DialogContent from '@mui/material/DialogContent';
import DialogActions from '@mui/material/DialogActions';
import Button from '@mui/material/Button';
import Typography from '@mui/material/Typography';
import Checkbox from '@mui/material/Checkbox';
import List from '@mui/material/List';
import ListItem from '@mui/material/ListItem';
import ListItemButton from '@mui/material/ListItemButton';
import ListItemIcon from '@mui/material/ListItemIcon';
import ListItemText from '@mui/material/ListItemText';
import Chip from '@mui/material/Chip';
import TextField from '@mui/material/TextField';
import InputAdornment from '@mui/material/InputAdornment';
import CircularProgress from '@mui/material/CircularProgress';
import Alert from '@mui/material/Alert';
import Box from '@mui/material/Box';
import useMediaQuery from '@mui/material/useMediaQuery';
import { useTheme } from '@mui/material/styles';
import SearchIcon from '@mui/icons-material/Search';
import LoadingSkeleton from '@/components/common/LoadingSkeleton';
import EmptyState from '@/components/common/EmptyState';
import * as plantApi from '@/api/endpoints/plantInstances';
import type { PlantInstance } from '@/api/types';

interface AdoptPlantsDialogProps {
  open: boolean;
  onClose: () => void;
  onAdopted: (adoptedCount: number) => void;
  runKey: string;
  adoptFn: (runKey: string, plantKeys: string[]) => Promise<{ adopted_count: number; skipped: Array<{ key: string; reason: string }> }>;
}

export default function AdoptPlantsDialog({
  open,
  onClose,
  onAdopted,
  runKey,
  adoptFn,
}: AdoptPlantsDialogProps) {
  const theme = useTheme();
  const fullScreen = useMediaQuery(theme.breakpoints.down('sm'));
  const { t } = useTranslation();
  const [plants, setPlants] = useState<PlantInstance[]>([]);
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [selected, setSelected] = useState<Set<string>>(new Set());
  const [search, setSearch] = useState('');

  useEffect(() => {
    if (!open) return;
    setSelected(new Set());
    setSearch('');
    setError(null);
    setLoading(true);
    plantApi
      .listPlantInstances(0, 200)
      .then((allPlants) => {
        // Filter to plants that are not removed (no removed_on date)
        const available = allPlants.filter((p) => !p.removed_on);
        setPlants(available);
      })
      .catch(() => {
        setPlants([]);
        setError(t('common.loadingError'));
      })
      .finally(() => setLoading(false));
  }, [open, t]);

  const filteredPlants = useMemo(() => {
    if (!search.trim()) return plants;
    const lower = search.toLowerCase();
    return plants.filter(
      (p) =>
        p.instance_id.toLowerCase().includes(lower) ||
        (p.plant_name ?? '').toLowerCase().includes(lower) ||
        p.current_phase.toLowerCase().includes(lower),
    );
  }, [plants, search]);

  const handleToggle = (key: string) => {
    setSelected((prev) => {
      const next = new Set(prev);
      if (next.has(key)) {
        next.delete(key);
      } else {
        next.add(key);
      }
      return next;
    });
  };

  const handleSelectAll = () => {
    if (selected.size === filteredPlants.length) {
      setSelected(new Set());
    } else {
      setSelected(new Set(filteredPlants.map((p) => p.key)));
    }
  };

  const handleAdopt = async () => {
    if (selected.size === 0) return;
    setSaving(true);
    setError(null);
    try {
      const result = await adoptFn(runKey, Array.from(selected));
      if (result.skipped.length > 0) {
        setError(
          t('pages.plantingRuns.adoptSkipped', { count: result.skipped.length }),
        );
      }
      onAdopted(result.adopted_count);
    } catch {
      setError(t('pages.plantingRuns.adoptError'));
    } finally {
      setSaving(false);
    }
  };

  return (
    <Dialog
      fullScreen={fullScreen}
      open={open}
      onClose={onClose}
      maxWidth="sm"
      fullWidth
      data-testid="adopt-plants-dialog"
    >
      <DialogTitle>{t('pages.plantingRuns.adoptPlants')}</DialogTitle>
      <DialogContent>
        <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
          {t('pages.plantingRuns.adoptPlantsDesc')}
        </Typography>

        {error && (
          <Alert severity="error" sx={{ mb: 2 }} data-testid="adopt-error">
            {error}
          </Alert>
        )}

        {loading ? (
          <LoadingSkeleton variant="table" />
        ) : plants.length === 0 ? (
          <EmptyState message={t('pages.plantingRuns.noAvailablePlants')} />
        ) : (
          <>
            <TextField
              size="small"
              fullWidth
              placeholder={t('common.search')}
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              sx={{ mb: 1 }}
              slotProps={{
                input: {
                  startAdornment: (
                    <InputAdornment position="start">
                      <SearchIcon />
                    </InputAdornment>
                  ),
                },
              }}
              data-testid="adopt-search"
            />

            <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 1 }}>
              <Button size="small" onClick={handleSelectAll} data-testid="adopt-select-all">
                {selected.size === filteredPlants.length
                  ? t('common.deselectAll')
                  : t('common.selectAll')}
              </Button>
              <Typography variant="caption" color="text.secondary">
                {t('pages.plantingRuns.selectedCount', { count: selected.size })}
              </Typography>
            </Box>

            <List
              dense
              sx={{
                maxHeight: 400,
                overflow: 'auto',
                border: 1,
                borderColor: 'divider',
                borderRadius: 1,
              }}
              data-testid="adopt-plants-list"
            >
              {filteredPlants.map((plant) => (
                <ListItem key={plant.key} disablePadding>
                  <ListItemButton
                    onClick={() => handleToggle(plant.key)}
                    dense
                    data-testid={`adopt-plant-${plant.key}`}
                  >
                    <ListItemIcon sx={{ minWidth: 36 }}>
                      <Checkbox
                        edge="start"
                        checked={selected.has(plant.key)}
                        tabIndex={-1}
                        disableRipple
                        slotProps={{ input: {
                          'aria-label': plant.instance_id,
                        } }}
                      />
                    </ListItemIcon>
                    <ListItemText
                      primary={plant.plant_name ?? plant.instance_id}
                      secondary={plant.instance_id !== (plant.plant_name ?? plant.instance_id) ? plant.instance_id : undefined}
                    />
                    <Chip
                      label={plant.current_phase}
                      size="small"
                      color="primary"
                      variant="outlined"
                      sx={{ ml: 1 }}
                    />
                  </ListItemButton>
                </ListItem>
              ))}
            </List>
          </>
        )}
      </DialogContent>
      <DialogActions>
        <Button onClick={onClose} disabled={saving}>
          {t('common.cancel')}
        </Button>
        <Button
          variant="contained"
          onClick={handleAdopt}
          disabled={selected.size === 0 || saving || loading}
          startIcon={saving ? <CircularProgress size={16} /> : undefined}
          data-testid="adopt-confirm-button"
        >
          {t('pages.plantingRuns.adoptSelected', { count: selected.size })}
        </Button>
      </DialogActions>
    </Dialog>
  );
}
