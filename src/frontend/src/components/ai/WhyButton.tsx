import { useState } from 'react';
import { useTranslation } from 'react-i18next';
import IconButton from '@mui/material/IconButton';
import Tooltip from '@mui/material/Tooltip';
import HelpOutlineIcon from '@mui/icons-material/HelpOutlined';
import WhyDrawer from './WhyDrawer';
import type { AiExplainRequest } from '@/api/types';

// UI-NFR-001 R-011: 48x48 touch target on mobile/tablet, MUI's small
// IconButton default hit area (~30px) falls short there. R-013 allows the
// desktop reduction back to a compact 32px once mouse input dominates.
const TOUCH_TARGET_SX = { minWidth: { xs: 48, sm: 32 }, minHeight: { xs: 48, sm: 32 } } as const;

export interface WhyButtonProps {
  /** The explain request describing the recommendation to justify. */
  request: AiExplainRequest;
  /** Optional primary action forwarded to the drawer. */
  onFollow?: () => void;
  /** data-testid passthrough. */
  'data-testid'?: string;
}

/**
 * REQ-031 §6.4 — kleiner "Warum?"-Icon-Button.
 *
 * Wird auf Task-/Care-/Phasenuebergangs-/Feeding-Karten platziert und oeffnet
 * bei Klick den `<WhyDrawer>` mit der kontext-injizierten KI-Erklaerung.
 * Sichtbarkeit ist an Stufe-2 (Tenant-Setting) gebunden — der aufrufende
 * Kontext blendet den Button aus, wenn KI fuer den Tenant deaktiviert ist.
 */
export default function WhyButton({ request, onFollow, 'data-testid': dataTestId }: WhyButtonProps) {
  const { t } = useTranslation();
  const [open, setOpen] = useState(false);

  return (
    <>
      <Tooltip title={t('ai.why.tooltip')}>
        <IconButton
          size="small"
          onClick={() => setOpen(true)}
          aria-label={t('ai.why.tooltip')}
          data-testid={dataTestId ?? 'why-button'}
          sx={TOUCH_TARGET_SX}
        >
          <HelpOutlineIcon fontSize="small" />
        </IconButton>
      </Tooltip>
      <WhyDrawer
        open={open}
        onClose={() => setOpen(false)}
        request={request}
        onFollow={onFollow}
      />
    </>
  );
}
