/**
 * Skip links of the editor (REQ-053 GP-NFR-070): "To the object list" and "To the plan" are the
 * first tab stops, invisible until focused. The list link opens the list view when the plan is
 * showing. "To the properties panel" is always offered (§17.3, GP-UX-068): it focuses the side panel while it is
 * open and the panel switch while it is collapsed, so the panel is one key away (WP 10.5).
 */
import { useTranslation } from 'react-i18next';
import Box from '@mui/material/Box';
import { EDITOR_ANCHORS } from './anchors';

interface SkipLinksProps {
  listShown: boolean;
  onToList: () => void;
  onToPlan: () => void;
  onToPanel: () => void;
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
  // Hidden, not display:none: it has to be focusable (WCAG 2.4.1). Clipped in place rather than moved above the
  // editor: since the header bar opens the editor (§17.3), a link moved up would peek out under the app bar.
  clipPath: 'inset(50%)',
  pointerEvents: 'none',
  '&:focus': { clipPath: 'none', pointerEvents: 'auto' },
} as const;

export function SkipLinks({ listShown, onToList, onToPlan, onToPanel }: SkipLinksProps) {
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
      <Box
        component="a"
        href={`#${EDITOR_ANCHORS.panel}`}
        sx={linkSx}
        onClick={(event) => {
          event.preventDefault();
          onToPanel();
        }}
        data-testid="garden-plan-skip-panel"
      >
        {t(`${prefix}.panel`)}
      </Box>
    </Box>
  );
}
