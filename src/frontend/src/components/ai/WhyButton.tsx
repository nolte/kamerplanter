import { useState } from 'react';
import { useTranslation } from 'react-i18next';
import IconButton from '@mui/material/IconButton';
import Tooltip from '@mui/material/Tooltip';
import HelpOutlineIcon from '@mui/icons-material/HelpOutlined';
import WhyDrawer from './WhyDrawer';
import type { AiExplainRequest } from '@/api/types';

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
