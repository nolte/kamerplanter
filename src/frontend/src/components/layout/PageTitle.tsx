import { useEffect } from 'react';
import Typography from '@mui/material/Typography';
import type { SxProps, Theme } from '@mui/material/styles';

interface PageTitleProps {
  title: string;
  sx?: SxProps<Theme>;
}

export default function PageTitle({ title, sx }: PageTitleProps) {
  useEffect(() => {
    document.title = `${title} — Kamerplanter`;
    return () => {
      document.title = 'Kamerplanter';
    };
  }, [title]);

  return (
    <Typography variant="h4" component="h1" sx={{ mb: 3, ...sx as object }} data-testid="page-title">
      {title}
    </Typography>
  );
}
