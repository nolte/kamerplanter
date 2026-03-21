import { useEffect, useMemo, useState } from 'react';
import { useTranslation } from 'react-i18next';
import Dialog from '@mui/material/Dialog';
import DialogTitle from '@mui/material/DialogTitle';
import DialogContent from '@mui/material/DialogContent';
import DialogActions from '@mui/material/DialogActions';
import Box from '@mui/material/Box';
import Typography from '@mui/material/Typography';
import Chip from '@mui/material/Chip';
import List from '@mui/material/List';
import ListItemButton from '@mui/material/ListItemButton';
import ListItemIcon from '@mui/material/ListItemIcon';
import ListItemText from '@mui/material/ListItemText';
import ToggleButton from '@mui/material/ToggleButton';
import ToggleButtonGroup from '@mui/material/ToggleButtonGroup';
import TextField from '@mui/material/TextField';
import InputAdornment from '@mui/material/InputAdornment';
import Tooltip from '@mui/material/Tooltip';
import Button from '@mui/material/Button';
import CircularProgress from '@mui/material/CircularProgress';
import useMediaQuery from '@mui/material/useMediaQuery';
import { useTheme } from '@mui/material/styles';
import StarIcon from '@mui/icons-material/Star';
import StarBorderIcon from '@mui/icons-material/StarBorder';
import SearchIcon from '@mui/icons-material/Search';
import ScienceIcon from '@mui/icons-material/Science';
import CheckCircleIcon from '@mui/icons-material/CheckCircle';
import RadioButtonUncheckedIcon from '@mui/icons-material/RadioButtonUnchecked';
import EmptyState from '@/components/common/EmptyState';
import { useLocalFavorites } from '@/hooks/useLocalFavorites';
import type { NutrientPlan } from '@/api/types';
import * as planApi from '@/api/endpoints/nutrient-plans';

interface NutrientPlanAssignDialogProps {
  open: boolean;
  onClose: () => void;
  onAssign: (planKey: string) => Promise<void>;
}

export default function NutrientPlanAssignDialog({
  open,
  onClose,
  onAssign,
}: NutrientPlanAssignDialogProps) {
  const { t } = useTranslation();
  const theme = useTheme();
  const fullScreen = useMediaQuery(theme.breakpoints.down('sm'));

  const [plans, setPlans] = useState<NutrientPlan[]>([]);
  const { favorites, isFavorite } = useLocalFavorites('kamerplanter-nutrient-plan-favorites');
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [selectedPlanKey, setSelectedPlanKey] = useState<string | null>(null);
  const [search, setSearch] = useState('');
  const [filter, setFilter] = useState<'all' | 'favorites'>('all');

  useEffect(() => {
    if (!open) return;
    let cancelled = false;
    const loadData = async () => {
      setLoading(true);
      try {
        const planList = await planApi.fetchNutrientPlans(0, 200);
        if (cancelled) return;
        setPlans(planList);
      } catch {
        // plan fetch failed
      } finally {
        if (!cancelled) setLoading(false);
      }
    };
    loadData();
    setSelectedPlanKey(null);
    setSearch('');
    setFilter('all');
    return () => { cancelled = true; };
  }, [open]);

  const filteredPlans = useMemo(() => {
    let result = plans;

    if (filter === 'favorites') {
      result = result.filter((p) => isFavorite(p.key));
    }

    if (search.trim()) {
      const q = search.toLowerCase();
      result = result.filter(
        (p) =>
          p.name.toLowerCase().includes(q) ||
          (p.description && p.description.toLowerCase().includes(q)) ||
          (p.author && p.author.toLowerCase().includes(q)) ||
          p.tags.some((tag) => tag.toLowerCase().includes(q)),
      );
    }

    return result.sort((a, b) => {
      const aFav = isFavorite(a.key) ? 0 : 1;
      const bFav = isFavorite(b.key) ? 0 : 1;
      if (aFav !== bFav) return aFav - bFav;
      return a.name.localeCompare(b.name);
    });
  }, [plans, favorites, isFavorite, filter, search]);

  const onConfirm = async () => {
    if (!selectedPlanKey) return;
    try {
      setSaving(true);
      await onAssign(selectedPlanKey);
      onClose();
    } catch {
      // error handled by parent
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
      data-testid="assign-plan-dialog"
    >
      <DialogTitle>{t('pages.nutrientPlans.assignPlan')}</DialogTitle>
      <DialogContent dividers>
        <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
          {t('pages.nutrientPlans.assignPlanIntro')}
        </Typography>

        {/* Search + Filter bar */}
        <Box sx={{ display: 'flex', gap: 1, mb: 1, flexWrap: 'wrap', alignItems: 'center' }}>
          <TextField
            size="small"
            placeholder={t('common.search')}
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            sx={{ flex: 1, minWidth: 150 }}
            slotProps={{
              input: {
                startAdornment: (
                  <InputAdornment position="start">
                    <SearchIcon fontSize="small" />
                  </InputAdornment>
                ),
              },
            }}
            data-testid="plan-search"
          />
          <ToggleButtonGroup
            size="small"
            value={filter}
            exclusive
            onChange={(_, v) => { if (v) setFilter(v); }}
          >
            <ToggleButton value="all" data-testid="filter-all">
              {t('common.all')}
            </ToggleButton>
            <ToggleButton value="favorites" data-testid="filter-favorites">
              <StarIcon fontSize="small" sx={{ mr: 0.5 }} />
              {t('pages.nutrientPlans.favToggle')}
            </ToggleButton>
          </ToggleButtonGroup>
        </Box>

        {/* Plan list */}
        <List
          sx={{
            maxHeight: { xs: 'calc(100vh - 350px)', sm: 380 },
            overflowY: 'auto',
            mx: -2,
          }}
          disablePadding
        >
          {loading && (
            <Box sx={{ display: 'flex', justifyContent: 'center', py: 4 }}>
              <CircularProgress size={28} />
            </Box>
          )}

          {!loading && filteredPlans.length === 0 && (
            <EmptyState
              message={
                filter === 'favorites'
                  ? t('pages.nutrientPlans.noFavorites')
                  : t('pages.nutrientPlans.noPlansFound')
              }
            />
          )}

          {!loading &&
            filteredPlans.map((plan) => {
              const isFav = isFavorite(plan.key);
              const isSelected = selectedPlanKey === plan.key;

              return (
                <ListItemButton
                  key={plan.key}
                  selected={isSelected}
                  onClick={() => setSelectedPlanKey(plan.key)}
                  data-testid={`plan-item-${plan.key}`}
                  sx={{ alignItems: 'flex-start', py: 1.5 }}
                >
                  <ListItemIcon sx={{ mt: 0.5, minWidth: 36 }}>
                    {isSelected ? (
                      <CheckCircleIcon color="primary" />
                    ) : (
                      <RadioButtonUncheckedIcon color="disabled" />
                    )}
                  </ListItemIcon>
                  <ListItemText
                    primary={
                      <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
                        {isFav ? (
                          <StarIcon sx={{ fontSize: 16, color: 'warning.main' }} />
                        ) : (
                          <StarBorderIcon sx={{ fontSize: 16, color: 'text.disabled' }} />
                        )}
                        <Typography variant="subtitle2" sx={{ fontWeight: isSelected ? 700 : 500 }}>
                          {plan.name}
                        </Typography>
                        {plan.is_template && (
                          <Chip
                            label={t('pages.nutrientPlans.isTemplate')}
                            size="small"
                            variant="outlined"
                            color="info"
                            icon={<ScienceIcon />}
                            sx={{ ml: 0.5 }}
                          />
                        )}
                      </Box>
                    }
                    secondary={
                      <Box component="span" sx={{ display: 'block' }}>
                        {plan.description && (
                          <Typography
                            variant="body2"
                            color="text.secondary"
                            component="span"
                            sx={{
                              display: '-webkit-box',
                              WebkitLineClamp: 2,
                              WebkitBoxOrient: 'vertical',
                              overflow: 'hidden',
                            }}
                          >
                            {plan.description}
                          </Typography>
                        )}
                        <Box component="span" sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5, mt: 0.5 }}>
                          {plan.author && (
                            <Chip label={plan.author} size="small" variant="outlined" />
                          )}
                          {plan.recommended_substrate_type && (
                            <Tooltip title={t('pages.nutrientPlans.substrateType')} arrow enterTouchDelay={0}>
                              <Chip
                                label={t(`enums.substrateType.${plan.recommended_substrate_type}`, { defaultValue: plan.recommended_substrate_type })}
                                size="small"
                                variant="outlined"
                                color="secondary"
                              />
                            </Tooltip>
                          )}
                          {plan.version && plan.version !== '1.0' && (
                            <Chip label={`v${plan.version}`} size="small" variant="outlined" />
                          )}
                          {plan.watering_schedule && (
                            <Chip
                              label={t('pages.wateringSchedule.title')}
                              size="small"
                              variant="outlined"
                              color="info"
                            />
                          )}
                          {plan.tags.map((tag) => (
                            <Chip key={tag} label={tag} size="small" />
                          ))}
                        </Box>
                      </Box>
                    }
                    secondaryTypographyProps={{ component: 'div' }}
                  />
                </ListItemButton>
              );
            })}
        </List>
      </DialogContent>
      <DialogActions>
        <Button onClick={onClose} disabled={saving}>
          {t('common.cancel')}
        </Button>
        <Button
          variant="contained"
          onClick={onConfirm}
          disabled={!selectedPlanKey || saving}
          startIcon={saving ? <CircularProgress size={16} /> : undefined}
        >
          {t('pages.nutrientPlans.assignPlan')}
        </Button>
      </DialogActions>
    </Dialog>
  );
}
