/**
 * The site hints beyond the light ladder (REQ-053 GP-FR-161): frost, wind and waterlogging, one line each, in
 * words as well as colour. Like the sun verdict they never block, and each is present only where the bed
 * feature and the species value are both known and the pair has a source (the calculator decides).
 */
import { useTranslation } from 'react-i18next';
import Alert from '@mui/material/Alert';
import type { SiteAxisHint } from '../model/siteFit';

interface SiteAxisHintsProps {
  speciesKey: string;
  speciesName: string;
  hints: readonly SiteAxisHint[];
}

export default function SiteAxisHints({ speciesKey, speciesName, hints }: SiteAxisHintsProps) {
  const { t } = useTranslation();
  return (
    <>
      {hints.map((hint) => (
        <Alert key={hint} severity="warning" data-testid={`planting-site-axis-${hint}-${speciesKey}`}>
          {t(`pages.bed.planting.siteFit.axis.${hint}`, { name: speciesName })}
        </Alert>
      ))}
    </>
  );
}
