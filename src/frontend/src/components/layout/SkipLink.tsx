import type { MouseEvent } from 'react';
import { useTranslation } from 'react-i18next';
import Box from '@mui/material/Box';

interface SkipLinkProps {
  /** Id of the `<main>` landmark the link jumps to. */
  targetId: string;
}

/**
 * "Skip to content" link (WCAG 2.4.1): off-screen until it receives keyboard focus, then pinned to
 * the top-left corner. Shared by the standard shell and the kiosk shell (#3025 W-09: the kiosk
 * shell had none).
 *
 * The jump moves the focus itself instead of following the `href` (#3018): following it would replace the
 * URL fragment, which the tabbed pages read as their tab (`useTabUrl`) — `/kalender#list` fell back to the
 * month view — and add a history entry. The `href` stays for the link's semantics and without script.
 */
export default function SkipLink({ targetId }: SkipLinkProps) {
  const { t } = useTranslation();
  return (
    <Box
      component="a"
      href={`#${targetId}`}
      onClick={(event: MouseEvent<HTMLAnchorElement>) => {
        const target = document.getElementById(targetId);
        if (!target) return;
        event.preventDefault();
        // The landmark carries tabIndex={-1} in both shells; set it where a caller's target lacks it.
        if (!target.hasAttribute('tabindex')) target.setAttribute('tabindex', '-1');
        target.focus();
        target.scrollIntoView?.({ block: 'start' });
      }}
      sx={{
        position: 'absolute',
        left: '-9999px',
        top: 'auto',
        width: '1px',
        height: '1px',
        overflow: 'hidden',
        '&:focus': {
          position: 'fixed',
          top: 8,
          left: 8,
          width: 'auto',
          height: 'auto',
          overflow: 'visible',
          zIndex: (theme) => theme.zIndex.tooltip + 1,
          bgcolor: 'background.paper',
          color: 'text.primary',
          px: 2,
          py: 1,
          borderRadius: 1,
          boxShadow: 3,
        },
      }}
    >
      {t('common.skipToContent')}
    </Box>
  );
}
