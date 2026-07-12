import { useTranslation } from 'react-i18next';
import Grid from '@mui/material/Grid';
import Typography from '@mui/material/Typography';
import PageTitle from '@/components/layout/PageTitle';
import VpdCalculatorCard from './calculations/VpdCalculatorCard';
import GddCalculatorCard from './calculations/GddCalculatorCard';
import PhotoperiodCalculatorCard from './calculations/PhotoperiodCalculatorCard';
import SlotCapacityCalculatorCard from './calculations/SlotCapacityCalculatorCard';
import SunTimesCalculatorCard from './calculations/SunTimesCalculatorCard';

/**
 * Grower calculators (REQ-003 / REQ-004 domain helpers). The page is a thin
 * layout shell; each calculator owns its own state, inputs and server call
 * (`POST /calculations/*`). The computations stay server-side — this component
 * only arranges the input surfaces.
 */
export default function CalculationsPage() {
  const { t } = useTranslation();

  return (
    <>
      <PageTitle title={t('pages.calculations.title')} />
      <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
        {t('pages.calculations.intro')}
      </Typography>

      <Grid container spacing={3}>
        <Grid size={{ xs: 12, md: 6 }}>
          <VpdCalculatorCard />
        </Grid>
        <Grid size={{ xs: 12, md: 6 }}>
          <GddCalculatorCard />
        </Grid>
        <Grid size={{ xs: 12, md: 6 }}>
          <PhotoperiodCalculatorCard />
        </Grid>
        <Grid size={{ xs: 12, md: 6 }}>
          <SlotCapacityCalculatorCard />
        </Grid>
        <Grid size={{ xs: 12, md: 6 }}>
          <SunTimesCalculatorCard />
        </Grid>
      </Grid>
    </>
  );
}
