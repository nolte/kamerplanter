import { useCallback, useEffect, useMemo, useState } from 'react';
import { useTranslation } from 'react-i18next';
import Box from '@mui/material/Box';
import Button from '@mui/material/Button';
import Chip from '@mui/material/Chip';
import type { ChipProps } from '@mui/material/Chip';
import IconButton from '@mui/material/IconButton';
import Tooltip from '@mui/material/Tooltip';
import Typography from '@mui/material/Typography';
import AddIcon from '@mui/icons-material/Add';
import DeleteIcon from '@mui/icons-material/Delete';
import PageTitle from '@/components/layout/PageTitle';
import DataTable, { type Column } from '@/components/common/DataTable';
import ConfirmDialog from '@/components/common/ConfirmDialog';
import MobileCard from '@/components/common/MobileCard';
import { useTableUrlState } from '@/hooks/useTableState';
import { useAppDispatch, useAppSelector } from '@/store/hooks';
import { useNotification } from '@/hooks/useNotification';
import { useApiError } from '@/hooks/useApiError';
import { fetchOverwinteringProfiles } from '@/store/slices/overwinteringProfilesSlice';
import * as api from '@/api/endpoints/overwinteringProfiles';
import * as plantApi from '@/api/endpoints/plantInstances';
import type {
  HardinessRating,
  OverwinteringProfile,
  PlantInstance,
} from '@/api/types';
import OverwinteringProfileDialog from './OverwinteringProfileDialog';

/** REQ-022 hardiness rating → traffic-light palette token for the list chip. */
const hardinessColor: Record<HardinessRating, ChipProps['color']> = {
  hardy: 'success',
  needs_protection: 'warning',
  frost_free: 'error',
  dig_and_store: 'error',
};

export default function OverwinteringListPage() {
  const { t, i18n } = useTranslation();
  const dispatch = useAppDispatch();
  const notification = useNotification();
  const { handleError } = useApiError();
  const { items, loading } = useAppSelector((s) => s.overwinteringProfiles);
  const [plants, setPlants] = useState<PlantInstance[]>([]);
  const [dialogOpen, setDialogOpen] = useState(false);
  const [editProfile, setEditProfile] = useState<OverwinteringProfile | null>(
    null,
  );
  const [deleteTarget, setDeleteTarget] = useState<OverwinteringProfile | null>(
    null,
  );
  const tableState = useTableUrlState({
    defaultSort: { column: 'hardinessRating', direction: 'asc' },
  });

  const reload = () => {
    dispatch(fetchOverwinteringProfiles({}));
  };

  useEffect(() => {
    dispatch(fetchOverwinteringProfiles({}));
    plantApi
      .listPlantInstances(0, 200)
      .then(setPlants)
      .catch(() => setPlants([]));
  }, [dispatch]);

  const plantNames = useMemo(() => {
    const map = new Map<string, string>();
    for (const p of plants) {
      map.set(p.key, p.plant_name ? `${p.plant_name} (${p.instance_id})` : p.instance_id);
    }
    return map;
  }, [plants]);

  const subjectLabel = useCallback(
    (p: OverwinteringProfile): string => {
      if (p.plant_key) return plantNames.get(p.plant_key) ?? p.plant_key;
      if (p.planting_run_key) return p.planting_run_key;
      return '—';
    },
    [plantNames],
  );

  /** Renders a 1–12 month number as a localised month name (e.g. "Oktober"). */
  const monthLabel = useCallback(
    (month: number) =>
      new Date(2000, month - 1, 1).toLocaleDateString(i18n.language, { month: 'long' }),
    [i18n.language],
  );

  const openCreate = () => {
    setEditProfile(null);
    setDialogOpen(true);
  };

  const openEdit = (p: OverwinteringProfile) => {
    setEditProfile(p);
    setDialogOpen(true);
  };

  const onDelete = async () => {
    if (!deleteTarget) return;
    try {
      await api.deleteOverwinteringProfile(deleteTarget.key);
      notification.success(t('common.delete'));
      reload();
    } catch (err) {
      handleError(err);
    } finally {
      setDeleteTarget(null);
    }
  };

  // REQ-022 / UI-NFR-011: the hardiness rating is a "fachspezifischer Status" —
  // every chip carries a hover tooltip explaining what the rating means in
  // practice, not just its (translated) enum label.
  const hardinessTooltip = useCallback(
    (rating: HardinessRating): string =>
      t(`pages.overwintering.hardinessRatingHelp.${rating}`),
    [t],
  );

  const hardinessChip = (r: OverwinteringProfile) => (
    <Tooltip title={hardinessTooltip(r.hardiness_rating)}>
      <Chip
        label={t(`enums.hardinessRating.${r.hardiness_rating}`)}
        size="small"
        color={hardinessColor[r.hardiness_rating] ?? 'default'}
        data-testid={`hardiness-chip-${r.key}`}
      />
    </Tooltip>
  );

  const columns: Column<OverwinteringProfile>[] = [
    {
      id: 'subject',
      label: t('pages.overwintering.subject'),
      render: (r) => subjectLabel(r),
      searchValue: (r) => subjectLabel(r),
    },
    {
      id: 'hardinessRating',
      label: t('pages.overwintering.hardinessRating'),
      render: hardinessChip,
      searchValue: (r) => t(`enums.hardinessRating.${r.hardiness_rating}`),
    },
    {
      id: 'winterAction',
      label: t('pages.overwintering.winterAction'),
      render: (r) => t(`enums.winterAction.${r.winter_action}`),
      searchValue: (r) => t(`enums.winterAction.${r.winter_action}`),
    },
    {
      id: 'winterActionMonth',
      label: t('pages.overwintering.winterActionMonth'),
      render: (r) => monthLabel(r.winter_action_month),
      searchValue: (r) => monthLabel(r.winter_action_month),
      hideBelowBreakpoint: 'md',
    },
    {
      id: 'autoGenerated',
      label: t('pages.overwintering.autoGenerated'),
      hideBelowBreakpoint: 'md',
      render: (r) =>
        r.auto_generated ? (
          <Tooltip title={t('pages.overwintering.autoGeneratedHelp')}>
            <Chip
              label={t('pages.overwintering.auto')}
              size="small"
              variant="outlined"
              color="info"
            />
          </Tooltip>
        ) : (
          '—'
        ),
    },
    {
      id: 'actions',
      label: t('common.actions'),
      width: 64,
      sortable: false,
      searchable: false,
      render: (r) => (
        <Tooltip title={t('common.delete')}>
          <IconButton
            size="small"
            color="error"
            onClick={(e) => {
              e.stopPropagation();
              setDeleteTarget(r);
            }}
            data-testid={`delete-${r.key}`}
            aria-label={t('common.delete')}
          >
            <DeleteIcon fontSize="small" />
          </IconButton>
        </Tooltip>
      ),
    },
  ];

  const renderMobileCard = useCallback(
    (r: OverwinteringProfile) => (
      <MobileCard
        title={subjectLabel(r)}
        subtitle={t(`enums.winterAction.${r.winter_action}`)}
        chips={
          <>
            <Tooltip title={hardinessTooltip(r.hardiness_rating)}>
              <Chip
                label={t(`enums.hardinessRating.${r.hardiness_rating}`)}
                size="small"
                color={hardinessColor[r.hardiness_rating] ?? 'default'}
                data-testid={`hardiness-chip-${r.key}`}
              />
            </Tooltip>
            {r.auto_generated && (
              <Tooltip title={t('pages.overwintering.autoGeneratedHelp')}>
                <Chip
                  label={t('pages.overwintering.auto')}
                  size="small"
                  variant="outlined"
                  color="info"
                />
              </Tooltip>
            )}
          </>
        }
        fields={[
          { label: t('pages.overwintering.winterActionMonth'), value: monthLabel(r.winter_action_month) },
        ]}
        trailing={
          <Tooltip title={t('common.delete')}>
            <IconButton
              size="medium"
              color="error"
              onClick={(e) => {
                e.stopPropagation();
                setDeleteTarget(r);
              }}
              data-testid={`delete-mobile-${r.key}`}
              aria-label={t('common.delete')}
            >
              <DeleteIcon fontSize="small" />
            </IconButton>
          </Tooltip>
        }
      />
    ),
    [subjectLabel, hardinessTooltip, monthLabel, t],
  );

  return (
    <Box data-testid="overwintering-list-page">
      <PageTitle
        title={t('pages.overwintering.title')}
        action={
          <Button
            variant="contained"
            startIcon={<AddIcon />}
            onClick={openCreate}
            data-testid="create-button"
          >
            {t('pages.overwintering.create')}
          </Button>
        }
      />
      <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
        {t('pages.overwintering.listIntro')}
      </Typography>
      <DataTable
        columns={columns}
        rows={items}
        loading={loading}
        onRowClick={openEdit}
        getRowKey={(r) => r.key}
        emptyMessage={t('pages.overwintering.empty')}
        emptyActionLabel={t('pages.overwintering.create')}
        onEmptyAction={openCreate}
        tableState={tableState}
        ariaLabel={t('pages.overwintering.title')}
        mobileCardRenderer={renderMobileCard}
      />

      <OverwinteringProfileDialog
        open={dialogOpen}
        profile={editProfile}
        plants={plants}
        onClose={() => setDialogOpen(false)}
        onSaved={() => {
          setDialogOpen(false);
          reload();
        }}
      />

      <ConfirmDialog
        open={!!deleteTarget}
        title={t('common.delete')}
        message={t('common.deleteConfirm', {
          name: deleteTarget ? subjectLabel(deleteTarget) : '',
        })}
        onConfirm={onDelete}
        onCancel={() => setDeleteTarget(null)}
        destructive
      />
    </Box>
  );
}
