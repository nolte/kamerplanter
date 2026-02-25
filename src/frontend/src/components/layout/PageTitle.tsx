import { useEffect } from 'react';
import Typography from '@mui/material/Typography';

interface PageTitleProps {
  title: string;
}

export default function PageTitle({ title }: PageTitleProps) {
  useEffect(() => {
    document.title = `${title} — Kamerplanter`;
    return () => {
      document.title = 'Kamerplanter';
    };
  }, [title]);

  return (
    <Typography variant="h4" component="h1" sx={{ mb: 3 }} data-testid="page-title">
      {title}
    </Typography>
  );
}
