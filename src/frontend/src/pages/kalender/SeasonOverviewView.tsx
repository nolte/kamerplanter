import { useTranslation } from 'react-i18next';
import Box from '@mui/material/Box';
import Card from '@mui/material/Card';
import CardActionArea from '@mui/material/CardActionArea';
import CardContent from '@mui/material/CardContent';
import Grid from '@mui/material/Grid';
import Typography from '@mui/material/Typography';
import { useTheme, alpha } from '@mui/material/styles';
import GrassIcon from '@mui/icons-material/Grass';
import AgricultureIcon from '@mui/icons-material/Agriculture';
import LocalFloristIcon from '@mui/icons-material/LocalFlorist';
import AssignmentIcon from '@mui/icons-material/Assignment';
import EmptyState from '@/components/common/EmptyState';
import type { MonthSummary } from '@/api/types';

interface SeasonOverviewViewProps {
  months: MonthSummary[];
  year: number;
  onMonthClick?: (month: number) => void;
}

export default function SeasonOverviewView({ months, year, onMonthClick }: SeasonOverviewViewProps) {
  const { t, i18n } = useTranslation();
  const theme = useTheme();

  if (months.length === 0) {
    return <EmptyState message={t('pages.calendar.seasonOverview.noData')} />;
  }

  return (
    <Box>
      <Typography variant="subtitle2" color="text.secondary" sx={{ mb: 1.5 }}>
        {t('pages.calendar.seasonOverview.title')} {year}
      </Typography>
      <Grid container spacing={1.5}>
        {months.map((ms) => {
          const fullMonthName = new Date(year, ms.month - 1).toLocaleDateString(
            i18n.language === 'de' ? 'de-DE' : 'en-US',
            { month: 'long' },
          );

          return (
            <Grid key={ms.month} size={{ xs: 6, sm: 4, md: 3 }}>
              <Card
                variant={ms.is_current ? 'outlined' : 'elevation'}
                sx={{
                  ...(ms.is_current && {
                    borderColor: 'primary.main',
                    borderWidth: 2,
                    bgcolor: alpha(theme.palette.primary.main, 0.04),
                  }),
                }}
              >
                <CardActionArea
                  onClick={() => onMonthClick?.(ms.month)}
                  disabled={!onMonthClick}
                >
                  <CardContent sx={{ py: 1.5, px: 2, '&:last-child': { pb: 1.5 } }}>
                    <Typography
                      variant="subtitle1"
                      sx={{
                        fontWeight: ms.is_current ? 700 : 600,
                        color: ms.is_current ? 'primary.main' : 'text.primary',
                        mb: 0.5,
                      }}
                    >
                      {fullMonthName}
                    </Typography>

                    <Box sx={{ display: 'flex', flexDirection: 'column', gap: 0.25 }}>
                      <CountRow
                        icon={<GrassIcon sx={{ fontSize: 16, color: '#66BB6A' }} />}
                        label={t('pages.calendar.seasonOverview.sowing')}
                        count={ms.sowing_count}
                      />
                      <CountRow
                        icon={<AgricultureIcon sx={{ fontSize: 16, color: '#FFA726' }} />}
                        label={t('pages.calendar.seasonOverview.harvestLabel')}
                        count={ms.harvest_count}
                      />
                      <CountRow
                        icon={<LocalFloristIcon sx={{ fontSize: 16, color: '#EC407A' }} />}
                        label={t('pages.calendar.seasonOverview.bloomLabel')}
                        count={ms.bloom_count}
                      />
                      <CountRow
                        icon={<AssignmentIcon sx={{ fontSize: 16, color: '#42A5F5' }} />}
                        label={t('pages.calendar.seasonOverview.tasks')}
                        count={ms.task_count}
                      />
                    </Box>
                  </CardContent>
                </CardActionArea>
              </Card>
            </Grid>
          );
        })}
      </Grid>
    </Box>
  );
}

function CountRow({ icon, label, count }: { icon: React.ReactNode; label: string; count: number }) {
  return (
    <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
      {icon}
      <Typography variant="caption" color="text.secondary" sx={{ flex: 1 }}>
        {label}
      </Typography>
      <Typography variant="caption" sx={{ fontWeight: 600 }}>
        {count}
      </Typography>
    </Box>
  );
}
