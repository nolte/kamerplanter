import { useMemo } from 'react';
import { useTranslation } from 'react-i18next';
import Alert from '@mui/material/Alert';
import AlertTitle from '@mui/material/AlertTitle';
import Box from '@mui/material/Box';
import Chip from '@mui/material/Chip';
import Typography from '@mui/material/Typography';
import WarningAmberIcon from '@mui/icons-material/WarningAmber';
import type { Toxicity } from '@/api/types';

interface Props {
  toxicity: Toxicity | null | undefined;
}

/**
 * Level-independent species toxicity warning (REQ-001 / REQ-021 safety exception).
 *
 * Intentionally rendered outside any `useExpertiseLevel`/`ModuleGuard` gate: the
 * detail page mounts it unconditionally on every tab, for every experience level
 * including `beginner`, because it protects humans and pets. Do NOT wrap this in
 * an expertise-level or module-visibility guard.
 *
 * Returns `null` when the species is genuinely non-toxic — i.e. no affected
 * group is flagged and the severity is unset or `none` — so beginners are never
 * shown a false alarm. A warning appears only when real toxicity is present.
 */
export default function ToxicityBadge({ toxicity }: Props) {
  const { t } = useTranslation();

  // Affected groups, ordered by protective priority (children first). Memoised
  // because it returns a new array that feeds a mapped render below.
  const affectedGroups = useMemo(() => {
    if (!toxicity) return [] as const;
    const groups: ('children' | 'cats' | 'dogs')[] = [];
    if (toxicity.is_toxic_children) groups.push('children');
    if (toxicity.is_toxic_cats) groups.push('cats');
    if (toxicity.is_toxic_dogs) groups.push('dogs');
    return groups;
  }, [toxicity]);

  const severity = toxicity?.severity ?? null;
  const hasSeverity = severity !== null && severity !== 'none';
  const isToxic = affectedGroups.length > 0 || hasSeverity;

  // Non-toxic or missing data → render nothing (no false alarm for beginners).
  if (!toxicity || !isToxic) return null;

  // Severe toxicity gets the highest-contrast error palette; anything else uses
  // the amber warning palette. Both meet WCAG contrast on light/dark themes.
  const muiSeverity = severity === 'severe' ? 'error' : 'warning';

  return (
    <Alert
      severity={muiSeverity}
      icon={<WarningAmberIcon />}
      role="alert"
      aria-label={t('pages.species.toxicity.ariaLabel')}
      sx={{ mb: 2 }}
      data-testid="species-toxicity-badge"
    >
      <AlertTitle>{t('pages.species.toxicity.title')}</AlertTitle>
      <Typography variant="body2" sx={{ mb: affectedGroups.length > 0 ? 1 : 0 }}>
        {t('pages.species.toxicity.description')}
      </Typography>

      {affectedGroups.length > 0 && (
        <Box
          sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5, mb: 1 }}
          data-testid="toxicity-affected-groups"
        >
          {affectedGroups.map((group) => (
            <Chip
              key={group}
              size="small"
              color={muiSeverity}
              label={t(`pages.species.toxicity.affected.${group}`)}
              data-testid={`toxicity-affected-${group}`}
            />
          ))}
        </Box>
      )}

      {hasSeverity && (
        <Typography variant="body2">
          <strong>{t('pages.species.toxicity.severityLabel')}:</strong>{' '}
          {t(`enums.toxicitySeverity.${severity}`)}
        </Typography>
      )}

      {toxicity.toxic_parts.length > 0 && (
        <Typography variant="body2">
          <strong>{t('pages.species.toxicity.partsLabel')}:</strong>{' '}
          {toxicity.toxic_parts.join(', ')}
        </Typography>
      )}

      {toxicity.toxic_compounds.length > 0 && (
        <Typography variant="body2">
          <strong>{t('pages.species.toxicity.compoundsLabel')}:</strong>{' '}
          {toxicity.toxic_compounds.join(', ')}
        </Typography>
      )}
    </Alert>
  );
}
