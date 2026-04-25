import { useEffect, type ReactNode } from 'react';
import Box from '@mui/material/Box';
import Typography from '@mui/material/Typography';
import type { SxProps, Theme } from '@mui/material/styles';

interface PageTitleProps {
  title: string;
  /** Optional action element (e.g. "Create" button) rendered next to the title.
   *  Wraps below the title on small screens automatically. */
  action?: ReactNode;
  /** Optional meta-row content (Pattern C, UI-NFR-017 §3.3 R-010..R-012):
   *  status chips, badges, manufacturer text. Rendered as a second row below
   *  the title row, vertically aligned to its centre, with `flexWrap: 'wrap'`. */
  meta?: ReactNode;
  sx?: SxProps<Theme>;
}

export default function PageTitle({ title, action, meta, sx }: PageTitleProps) {
  useEffect(() => {
    document.title = `${title} — Kamerplanter`;
    return () => {
      document.title = 'Kamerplanter';
    };
  }, [title]);

  if (!action && !meta) {
    return (
      <Typography variant="h4" component="h1" sx={{ mb: 3, ...sx as object }} data-testid="page-title">
        {title}
      </Typography>
    );
  }

  return (
    <Box
      sx={{
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'flex-start',
        flexWrap: 'wrap',
        gap: 1,
        mb: 3,
        ...sx as object,
      }}
    >
      {/* Left side: title (and meta-row stacked below it per Pattern C) */}
      <Box sx={{ minWidth: 0, flex: '1 1 auto' }}>
        <Typography variant="h4" component="h1" data-testid="page-title" sx={{ mb: 0 }}>
          {title}
        </Typography>
        {meta && (
          <Box
            sx={{
              display: 'flex',
              alignItems: 'center',
              flexWrap: 'wrap',
              gap: 1,
              mt: 0.5,
            }}
            data-testid="page-title-meta"
          >
            {meta}
          </Box>
        )}
      </Box>
      {action && <Box sx={{ flexShrink: 0 }}>{action}</Box>}
    </Box>
  );
}
