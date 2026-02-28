import { useEffect, useState, useMemo, useCallback } from 'react';
import { useTranslation } from 'react-i18next';
import Box from '@mui/material/Box';
import Card from '@mui/material/Card';
import CardContent from '@mui/material/CardContent';
import Typography from '@mui/material/Typography';
import Chip from '@mui/material/Chip';
import IconButton from '@mui/material/IconButton';
import Tooltip from '@mui/material/Tooltip';
import CircularProgress from '@mui/material/CircularProgress';
import CheckCircleIcon from '@mui/icons-material/CheckCircle';
import SnoozeIcon from '@mui/icons-material/Snooze';
import OpacityIcon from '@mui/icons-material/Opacity';
import YardIcon from '@mui/icons-material/Yard';
import SwapVertIcon from '@mui/icons-material/SwapVert';
import BugReportIcon from '@mui/icons-material/BugReport';
import PlaceIcon from '@mui/icons-material/Place';
import WaterDropIcon from '@mui/icons-material/WaterDrop';
import EditIcon from '@mui/icons-material/Edit';
import PageTitle from '@/components/layout/PageTitle';
import LoadingSkeleton from '@/components/common/LoadingSkeleton';
import EmptyState from '@/components/common/EmptyState';
import { useAppDispatch, useAppSelector } from '@/store/hooks';
import { fetchDashboard, fetchProfile } from '@/store/slices/careRemindersSlice';
import { useNotification } from '@/hooks/useNotification';
import { useApiError } from '@/hooks/useApiError';
import * as careApi from '@/api/endpoints/careReminders';
import type { CareDashboardEntry, ReminderType, CareProfile } from '@/api/types';
import CareProfileEditDialog from './components/CareProfileEditDialog';

type UrgencyLevel = 'overdue' | 'due_today' | 'upcoming';

const URGENCY_ORDER: UrgencyLevel[] = ['overdue', 'due_today', 'upcoming'];

const urgencyColorMap: Record<UrgencyLevel, 'error' | 'warning' | 'info'> = {
  overdue: 'error',
  due_today: 'warning',
  upcoming: 'info',
};

const urgencySectionColorMap: Record<UrgencyLevel, string> = {
  overdue: 'error.main',
  due_today: 'warning.main',
  upcoming: 'info.main',
};

function getReminderIcon(type: ReminderType) {
  switch (type) {
    case 'watering':
      return <OpacityIcon />;
    case 'fertilizing':
      return <YardIcon />;
    case 'repotting':
      return <SwapVertIcon />;
    case 'pest_check':
      return <BugReportIcon />;
    case 'location_check':
      return <PlaceIcon />;
    case 'humidity_check':
      return <WaterDropIcon />;
  }
}

export default function PflegeDashboardPage() {
  const { t } = useTranslation();
  const dispatch = useAppDispatch();
  const notification = useNotification();
  const { handleError } = useApiError();
  const { dashboard, loading, currentProfile } = useAppSelector(
    (s) => s.careReminders,
  );
  const [actionLoading, setActionLoading] = useState<string | null>(null);
  const [editDialogOpen, setEditDialogOpen] = useState(false);
  const [editPlantKey, setEditPlantKey] = useState<string | null>(null);

  useEffect(() => {
    dispatch(fetchDashboard());
  }, [dispatch]);

  const grouped = useMemo(() => {
    const groups: Record<UrgencyLevel, CareDashboardEntry[]> = {
      overdue: [],
      due_today: [],
      upcoming: [],
    };

    for (const entry of dashboard) {
      if (entry.urgency === 'overdue') {
        groups.overdue.push(entry);
      } else if (entry.urgency === 'due_today') {
        groups.due_today.push(entry);
      } else if (entry.urgency === 'upcoming') {
        groups.upcoming.push(entry);
      }
    }

    return groups;
  }, [dashboard]);

  const handleConfirm = useCallback(
    async (plantKey: string, reminderType: ReminderType) => {
      const id = `${plantKey}-${reminderType}`;
      try {
        setActionLoading(id);
        await careApi.confirmReminder(plantKey, reminderType);
        notification.success(t('pages.pflege.confirmAction'));
        dispatch(fetchDashboard());
      } catch (err) {
        handleError(err);
      } finally {
        setActionLoading(null);
      }
    },
    [dispatch, notification, handleError, t],
  );

  const handleSnooze = useCallback(
    async (plantKey: string, reminderType: ReminderType) => {
      const id = `${plantKey}-${reminderType}`;
      try {
        setActionLoading(id);
        await careApi.snoozeReminder(plantKey, reminderType);
        notification.info(t('pages.pflege.snoozeAction'));
        dispatch(fetchDashboard());
      } catch (err) {
        handleError(err);
      } finally {
        setActionLoading(null);
      }
    },
    [dispatch, notification, handleError, t],
  );

  const handleEditProfile = useCallback(
    (plantKey: string) => {
      setEditPlantKey(plantKey);
      dispatch(fetchProfile({ plantKey }));
      setEditDialogOpen(true);
    },
    [dispatch],
  );

  const handleProfileUpdated = useCallback(
    (_profile: CareProfile) => {
      setEditDialogOpen(false);
      setEditPlantKey(null);
      dispatch(fetchDashboard());
    },
    [dispatch],
  );

  const renderCard = useCallback(
    (entry: CareDashboardEntry) => {
      const id = `${entry.plant_key}-${entry.reminder_type}`;
      const isLoading = actionLoading === id;

      return (
        <Card key={id} sx={{ mb: 1 }} data-testid={`care-card-${id}`}>
          <CardContent
            sx={{
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
              flexWrap: 'wrap',
              gap: 1,
              pb: '0.5rem !important',
            }}
          >
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.5, flexGrow: 1 }}>
              <Box
                sx={{
                  color:
                    entry.urgency === 'overdue'
                      ? 'error.main'
                      : entry.urgency === 'due_today'
                        ? 'warning.main'
                        : 'info.main',
                }}
              >
                {getReminderIcon(entry.reminder_type)}
              </Box>
              <Box>
                <Typography variant="subtitle1" component="span">
                  {entry.plant_name}
                </Typography>
                {entry.species_name && (
                  <Typography
                    variant="body2"
                    color="text.secondary"
                    component="span"
                    sx={{ ml: 1 }}
                  >
                    ({entry.species_name})
                  </Typography>
                )}
                <Typography variant="body2" color="text.secondary" display="block">
                  {t(`enums.reminderType.${entry.reminder_type}`)}
                  {entry.due_date && (
                    <> &mdash; {new Date(entry.due_date).toLocaleDateString()}</>
                  )}
                </Typography>
              </Box>
            </Box>

            <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
              <Chip
                label={t(`pages.pflege.${entry.urgency === 'due_today' ? 'dueToday' : entry.urgency}`)}
                size="small"
                color={urgencyColorMap[entry.urgency as UrgencyLevel] ?? 'default'}
              />
              <Tooltip title={t('pages.pflege.editProfile')}>
                <IconButton
                  size="small"
                  onClick={() => handleEditProfile(entry.plant_key)}
                  data-testid={`edit-profile-${entry.plant_key}`}
                >
                  <EditIcon fontSize="small" />
                </IconButton>
              </Tooltip>
              <Tooltip title={t('pages.pflege.confirmAction')}>
                <span>
                  <IconButton
                    size="small"
                    color="success"
                    onClick={() => handleConfirm(entry.plant_key, entry.reminder_type)}
                    disabled={isLoading}
                    data-testid={`confirm-${id}`}
                  >
                    {isLoading ? (
                      <CircularProgress size={18} />
                    ) : (
                      <CheckCircleIcon fontSize="small" />
                    )}
                  </IconButton>
                </span>
              </Tooltip>
              <Tooltip title={t('pages.pflege.snoozeAction')}>
                <span>
                  <IconButton
                    size="small"
                    color="default"
                    onClick={() => handleSnooze(entry.plant_key, entry.reminder_type)}
                    disabled={isLoading}
                    data-testid={`snooze-${id}`}
                  >
                    {isLoading ? (
                      <CircularProgress size={18} />
                    ) : (
                      <SnoozeIcon fontSize="small" />
                    )}
                  </IconButton>
                </span>
              </Tooltip>
            </Box>
          </CardContent>
        </Card>
      );
    },
    [actionLoading, handleConfirm, handleSnooze, handleEditProfile, t],
  );

  const renderSection = useCallback(
    (urgency: UrgencyLevel, entries: CareDashboardEntry[]) => {
      if (entries.length === 0) return null;

      const sectionKeys: Record<UrgencyLevel, string> = {
        overdue: 'pages.pflege.overdue',
        due_today: 'pages.pflege.dueToday',
        upcoming: 'pages.pflege.upcoming',
      };

      return (
        <Box key={urgency} sx={{ mb: 3 }} data-testid={`care-section-${urgency}`}>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}>
            <Typography variant="h6" sx={{ color: urgencySectionColorMap[urgency] }}>
              {t(sectionKeys[urgency])}
            </Typography>
            <Chip label={entries.length} size="small" />
          </Box>
          {entries.map(renderCard)}
        </Box>
      );
    },
    [renderCard, t],
  );

  if (loading) return <LoadingSkeleton variant="card" />;

  const totalEntries =
    grouped.overdue.length + grouped.due_today.length + grouped.upcoming.length;

  return (
    <Box data-testid="pflege-dashboard-page">
      <PageTitle title={t('pages.pflege.title')} />
      <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
        {t('pages.pflege.title')}
      </Typography>

      {totalEntries === 0 ? (
        <EmptyState message={t('pages.pflege.noReminders')} />
      ) : (
        URGENCY_ORDER.map((urgency) => renderSection(urgency, grouped[urgency]))
      )}

      {currentProfile && editPlantKey && (
        <CareProfileEditDialog
          open={editDialogOpen}
          onClose={() => {
            setEditDialogOpen(false);
            setEditPlantKey(null);
          }}
          profile={currentProfile}
          onUpdated={handleProfileUpdated}
        />
      )}
    </Box>
  );
}
