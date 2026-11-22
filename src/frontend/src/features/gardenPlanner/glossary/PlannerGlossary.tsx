/**
 * The glossary of the garden planner (REQ-053 GP-UX-011, UI-NFR-011): the technical terms the planner shows
 * - crop rotation, rotation pause, companion planting, perennial crop, the feeder classes, green manure and
 * the three spacings - each explained by the shared `HelpTooltip`. The explanations live in the `glossary`
 * namespace (`glossary.<term>.*`, UI-NFR-011 §3); the visible term labels in `pages.gardenPlan.glossary`.
 *
 * `PlannerGlossary` renders a compact "Terms explained" line for a section; the spacing fields carry the
 * icon-only trigger next to the field instead (`PlannerTermField`).
 */
import type { ReactNode } from 'react';
import { useTranslation } from 'react-i18next';
import Box from '@mui/material/Box';
import Typography from '@mui/material/Typography';
import HelpTooltip from '@/components/common/HelpTooltip';

/** Every planner term with a glossary entry; the slug is the key below `glossary.` and `pages.gardenPlan.glossary.terms.`. */
export const PLANNER_GLOSSARY_TERMS = [
  'fruchtfolge',
  'anbaupause',
  'mischkultur',
  'dauerkultur',
  'zehrerklassen',
  'gruenduengung',
  'pflanzabstand',
  'reihenabstand',
  'randabstand',
] as const;

export type PlannerGlossaryTerm = (typeof PLANNER_GLOSSARY_TERMS)[number];

interface PlannerGlossaryProps {
  /** The terms this section uses, in reading order. */
  terms: readonly PlannerGlossaryTerm[];
  /** Distinguishes several glossary lines on one page (`planner-glossary-<id>`). */
  id: string;
}

/** A labelled line of term triggers; each opens its explanation on hover, keyboard focus or a long press (touch). */
export default function PlannerGlossary({ terms, id }: PlannerGlossaryProps) {
  const { t } = useTranslation();
  const titleId = `planner-glossary-${id}-title`;
  return (
    <Box
      role="group"
      aria-labelledby={titleId}
      data-testid={`planner-glossary-${id}`}
      sx={{ display: 'flex', flexWrap: 'wrap', alignItems: 'center', columnGap: 1.5, rowGap: 0.5 }}
    >
      <Typography id={titleId} variant="caption" color="text.secondary" component="span">
        {t('pages.gardenPlan.glossary.title')}
      </Typography>
      <Box
        component="ul"
        sx={{ display: 'flex', flexWrap: 'wrap', alignItems: 'center', columnGap: 1.5, rowGap: 0.5, m: 0, p: 0, listStyle: 'none' }}
      >
        {terms.map((term) => (
          <Box component="li" key={term} data-testid={`planner-glossary-term-${term}`}>
            <HelpTooltip term={term}>
              <Typography variant="body2" component="span">
                {t(`pages.gardenPlan.glossary.terms.${term}`)}
              </Typography>
            </HelpTooltip>
          </Box>
        ))}
      </Box>
    </Box>
  );
}

/**
 * A form field with the icon-only trigger of its term next to it - the placement `FormClimateZoneField`
 * established: the icon sits beside the input (not inside the label), vertically centred on it.
 */
export function PlannerTermField({ term, children }: { term: PlannerGlossaryTerm; children: ReactNode }) {
  return (
    <Box
      sx={{ display: 'flex', alignItems: 'flex-start', gap: 0.5, '& > :first-of-type': { flex: 1, minWidth: 0 } }}
      data-testid={`planner-term-field-${term}`}
    >
      {children}
      <Box component="span" sx={{ display: 'inline-flex', alignItems: 'center', minHeight: 48, flex: 'none' }}>
        <HelpTooltip term={term} iconOnly />
      </Box>
    </Box>
  );
}
