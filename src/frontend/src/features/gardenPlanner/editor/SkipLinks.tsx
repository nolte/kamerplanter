/**
 * Skip links of the editor (REQ-053 GP-NFR-070): "To the object list" and "To the plan" are the
 * first tab stops, invisible until focused. The list link opens the list view when the plan is
 * showing; the target of "To the properties panel" arrives with the panel (WP 2.6).
 */
import { useTranslation } from 'react-i18next';
import Box from '@mui/material/Box';
import { EDITOR_ANCHORS } from './anchors';

interface SkipLinksProps {
  listShown: boolean;
  onToList: () => void;
  onToPlan: () => void;
}

const linkSx = {
  position: 'absolute',
  left: 8,
  top: 8,
  zIndex: 10,
  px: 2,
  py: 1.25,
  minHeight: 44,
  display: 'inline-flex',
  alignItems: 'center',
  borderRadius: 1,
  bgcolor: 'background.paper',
  color: 'primary.main',
  border: 2,
  borderColor: 'primary.main',
  // Off-screen, not display:none: it has to be focusable (WCAG 2.4.1).
  transform: 'translateY(-300%)',
  '&:focus': { transform: 'none' },
} as const;

export function SkipLinks({ listShown, onToList, onToPlan }: SkipLinksProps) {
  const { t } = useTranslation();
  const prefix = 'pages.gardenPlan.editor.skip';
  return (
    <Box data-testid="garden-plan-skip-links" sx={{ position: 'relative' }}>
      <Box
        component="a"
        href={`#${EDITOR_ANCHORS.list}`}
        sx={linkSx}
        onClick={(event) => {
          event.preventDefault();
          onToList();
        }}
        data-testid="garden-plan-skip-list"
      >
        {t(`${prefix}.list`)}
      </Box>
      {listShown && (
        <Box
          component="a"
          href={`#${EDITOR_ANCHORS.canvas}`}
          sx={linkSx}
          onClick={(event) => {
            event.preventDefault();
            onToPlan();
          }}
          data-testid="garden-plan-skip-plan"
        >
          {t(`${prefix}.plan`)}
        </Box>
      )}
    </Box>
  );
}
