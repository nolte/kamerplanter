/**
 * "My beds · due today" (REQ-053 GP-UX-030, F-18): the entry of field mode. The beds of the site, the
 * signed-in user's first, then by what is due; each row is one large target that opens the bed sheet.
 * Text is at least 16 px; overdue is said in words, not only in red.
 */
import { useTranslation } from 'react-i18next';
import Box from '@mui/material/Box';
import ButtonBase from '@mui/material/ButtonBase';
import Typography from '@mui/material/Typography';
import ChevronRightIcon from '@mui/icons-material/ChevronRight';
import EmptyState from '@/components/common/EmptyState';
import { KIOSK_TOUCH_TARGET } from '@/kiosk/kioskTheme';
import { formatBedDate } from '../bed/bedFormat';
import type { BedListItem } from '../bed/types';
import { bedIsDue } from './fieldDue';

interface FieldBedListProps {
  beds: readonly BedListItem[];
  mine: ReadonlySet<string>;
  today: string;
  onOpen: (bed: BedListItem) => void;
}

export default function FieldBedList({ beds, mine, today, onOpen }: FieldBedListProps) {
  const { t, i18n } = useTranslation();
  const language = i18n.language;

  if (beds.length === 0) {
    return (
      <Box data-testid="field-bed-list-empty">
        <EmptyState
          message={t('pages.gardenPlan.field.list.empty')}
          description={t('pages.gardenPlan.field.list.emptyHint')}
        />
      </Box>
    );
  }

  return (
    <Box
      component="ul"
      aria-label={t('pages.gardenPlan.field.list.label')}
      data-testid="field-bed-list"
      sx={{ listStyle: 'none', p: 0, m: 0, display: 'flex', flexDirection: 'column', gap: 1 }}
    >
      {beds.map((bed) => {
        const overdue = bed.overdue_task_count ?? 0;
        const open = bed.open_task_count ?? 0;
        const due = bedIsDue(bed, today);
        const next = formatBedDate(bed.next_due_at, language);
        return (
          <Box component="li" key={bed.key}>
            <ButtonBase
              onClick={() => onOpen(bed)}
              data-testid={`field-bed-row-${bed.key}`}
              sx={{
                width: '100%',
                minHeight: KIOSK_TOUCH_TARGET,
                p: 1.5,
                gap: 1.5,
                justifyContent: 'flex-start',
                textAlign: 'left',
                border: 2,
                borderColor: overdue > 0 ? 'error.main' : 'divider',
                borderRadius: 1,
                '&.Mui-focusVisible': { outline: 3, outlineColor: 'primary.main', outlineOffset: 2 },
              }}
            >
              <Box component="span" sx={{ flexGrow: 1, minWidth: 0 }}>
                <Box component="span" sx={{ display: 'flex', flexWrap: 'wrap', alignItems: 'center', gap: 1 }}>
                  <Typography variant="h6" component="span" sx={{ overflowWrap: 'anywhere' }}>
                    {bed.name}
                  </Typography>
                  {mine.has(bed.key) && (
                    <Box
                      component="span"
                      sx={{ px: 1, border: 2, borderColor: 'text.primary', borderRadius: 4, fontWeight: 700 }}
                      data-testid={`field-bed-mine-${bed.key}`}
                    >
                      {t('pages.gardenPlan.field.list.mine')}
                    </Box>
                  )}
                </Box>
                <Typography variant="body1" component="span" sx={{ display: 'block' }}>
                  {t('pages.gardenPlan.field.list.counts', {
                    plants: bed.active_plant_count ?? 0,
                    tasks: open,
                  })}
                </Typography>
                {overdue > 0 && (
                  <Typography
                    variant="body1"
                    component="span"
                    sx={{ display: 'block', color: 'error.main', fontWeight: 700 }}
                    data-testid={`field-bed-overdue-${bed.key}`}
                  >
                    {t('pages.gardenPlan.field.list.overdue', { count: overdue })}
                  </Typography>
                )}
                {overdue === 0 && due && (
                  <Typography
                    variant="body1"
                    component="span"
                    sx={{ display: 'block', fontWeight: 700 }}
                    data-testid={`field-bed-due-${bed.key}`}
                  >
                    {t('pages.gardenPlan.field.list.dueToday')}
                  </Typography>
                )}
                {!due && next && (
                  <Typography variant="body1" component="span" sx={{ display: 'block' }}>
                    {t('pages.gardenPlan.field.list.next', { date: next })}
                  </Typography>
                )}
              </Box>
              <ChevronRightIcon sx={{ fontSize: 32, flexShrink: 0 }} aria-hidden="true" />
            </ButtonBase>
          </Box>
        );
      })}
    </Box>
  );
}
