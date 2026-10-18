/**
 * The tabs the bed view reserves for later packages - Planting, Care, History - with an honest empty
 * state instead of a dead tab. "Planting" points at the details tab, which still lists the runs and
 * plants of the location.
 */
import { useTranslation } from 'react-i18next';
import Box from '@mui/material/Box';
import EmptyState from '@/components/common/EmptyState';

export type PlaceholderTab = 'planting' | 'care' | 'history';

interface BedPlaceholderPanelProps {
  tab: PlaceholderTab;
  /** Switches to the details tab (only offered on the planting panel). */
  onShowDetails?: () => void;
}

export default function BedPlaceholderPanel({ tab, onShowDetails }: BedPlaceholderPanelProps) {
  const { t } = useTranslation();
  return (
    <Box data-testid={`bed-${tab}-tab`}>
      <EmptyState
        message={t(`pages.bed.placeholder.${tab}.title`)}
        description={t(`pages.bed.placeholder.${tab}.description`)}
        actionLabel={tab === 'planting' && onShowDetails ? t('pages.bed.placeholder.planting.action') : undefined}
        onAction={tab === 'planting' ? onShowDetails : undefined}
      />
    </Box>
  );
}
