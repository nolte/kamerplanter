/**
 * The tab the bed view still reserves for a later package - History - with an honest empty state
 * instead of a dead tab.
 */
import { useTranslation } from 'react-i18next';
import Box from '@mui/material/Box';
import EmptyState from '@/components/common/EmptyState';

export type PlaceholderTab = 'history';

interface BedPlaceholderPanelProps {
  tab: PlaceholderTab;
}

export default function BedPlaceholderPanel({ tab }: BedPlaceholderPanelProps) {
  const { t } = useTranslation();
  return (
    <Box data-testid={`bed-${tab}-tab`}>
      <EmptyState
        message={t(`pages.bed.placeholder.${tab}.title`)}
        description={t(`pages.bed.placeholder.${tab}.description`)}
      />
    </Box>
  );
}
