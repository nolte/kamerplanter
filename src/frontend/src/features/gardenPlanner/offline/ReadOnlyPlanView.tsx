/**
 * The garden plan without its editor (REQ-053 WP 9.2, GP-UX-024): what planning mode shows while there
 * is no connection or the plan comes from the plan cache. Geometry changes stay online-only (conflict
 * risk), so the drawing is read-only and a hint says why — a locked tool is explained, never an error.
 * Bed details and field mode stay one tap away.
 */
import { useMemo } from 'react';
import { useTranslation } from 'react-i18next';
import Alert from '@mui/material/Alert';
import Box from '@mui/material/Box';
import LockOutlinedIcon from '@mui/icons-material/LockOutlined';
import type { PlanModel } from '../model/planModel';
import type { PlanRenderer, RendererLabels, Viewport } from '../renderer/types';

interface ReadOnlyPlanViewProps {
  plan: PlanModel;
  viewport: Viewport;
  renderer: PlanRenderer;
  labels: RendererLabels;
  /** `offline` (no connection) or `cached` (connected, but the shown plan is the cached one). */
  reason: 'offline' | 'cached';
}

const NO_SELECTION = { selectedKeys: new Set<string>() };

export default function ReadOnlyPlanView({ plan, viewport, renderer, labels, reason }: ReadOnlyPlanViewProps) {
  const { t } = useTranslation();
  const drawing = useMemo(
    () => renderer.render(plan, viewport, NO_SELECTION, { labels }),
    [renderer, plan, viewport, labels],
  );
  return (
    <Box data-testid="garden-plan-read-only">
      <Alert
        severity="info"
        role="status"
        icon={<LockOutlinedIcon />}
        sx={{ mb: 2 }}
        data-testid="garden-plan-geometry-locked"
      >
        {t(`pages.gardenPlan.offline.geometryLocked.${reason}`)}
      </Alert>
      <Box
        sx={{ border: 1, borderColor: 'divider', borderRadius: 1, overflow: 'hidden', bgcolor: 'background.paper' }}
      >
        {drawing}
      </Box>
    </Box>
  );
}
