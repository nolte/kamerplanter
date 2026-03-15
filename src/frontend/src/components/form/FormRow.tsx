import Box from '@mui/material/Box';
import type { ReactNode } from 'react';

interface FormRowProps {
  children: ReactNode;
}

export default function FormRow({ children }: FormRowProps) {
  return (
    <Box sx={{
      display: 'grid',
      gridTemplateColumns: { xs: '1fr', md: '1fr 1fr' },
      columnGap: 2,
    }}>
      {children}
    </Box>
  );
}
