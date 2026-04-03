import { useEffect, type ReactNode } from 'react';
import Box from '@mui/material/Box';
import Typography from '@mui/material/Typography';
import type { SxProps, Theme } from '@mui/material/styles';

interface PageTitleProps {
  title: string;
  /** Optional action element (e.g. "Erstellen" button) rendered next to the title.
   *  Wraps below the title on small screens automatically. */
  action?: ReactNode;
  sx?: SxProps<Theme>;
}

export default function PageTitle({ title, action, sx }: PageTitleProps) {
  useEffect(() => {
    document.title = `${title} — Kamerplanter`;
    return () => {
      document.title = 'Kamerplanter';
    };
  }, [title]);

  if (!action) {
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
        alignItems: 'center',
        flexWrap: 'wrap',
        gap: 1,
        mb: 3,
        ...sx as object,
      }}
    >
      <Typography variant="h4" component="h1" data-testid="page-title" sx={{ minWidth: 0 }}>
        {title}
      </Typography>
      {action}
    </Box>
  );
}
