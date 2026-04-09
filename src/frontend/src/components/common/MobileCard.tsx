import type { ReactNode } from 'react';
import Box from '@mui/material/Box';
import Card from '@mui/material/Card';
import CardContent from '@mui/material/CardContent';
import Typography from '@mui/material/Typography';

interface MobileCardField {
  label: string;
  value: ReactNode;
}

interface MobileCardProps {
  title: ReactNode;
  subtitle?: ReactNode;
  fields?: MobileCardField[];
  trailing?: ReactNode;
  chips?: ReactNode;
}

export default function MobileCard({ title, subtitle, fields, trailing, chips }: MobileCardProps) {
  return (
    <Card variant="outlined" sx={{ '&:hover': { borderColor: 'primary.main' } }}>
      <CardContent sx={{ py: 1.5, px: 2, '&:last-child': { pb: 1.5 } }}>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', gap: 1 }}>
          <Box sx={{ minWidth: 0, flex: 1 }}>
            <Typography variant="subtitle2" noWrap>{title}</Typography>
            {subtitle && (
              <Typography variant="caption" color="text.secondary" noWrap sx={{ display: 'block' }}>
                {subtitle}
              </Typography>
            )}
          </Box>
          {trailing && <Box sx={{ flexShrink: 0 }}>{trailing}</Box>}
        </Box>
        {chips && (
          <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5, mt: 0.75 }}>
            {chips}
          </Box>
        )}
        {fields && fields.length > 0 && (
          <Box
            sx={{
              display: 'grid',
              gridTemplateColumns: 'auto 1fr',
              gap: '2px 8px',
              mt: 0.75,
            }}
          >
            {fields.map((f) => (
              <Box key={f.label} sx={{ display: 'contents' }}>
                <Typography variant="caption" color="text.secondary">{f.label}</Typography>
                <Typography variant="caption">{f.value}</Typography>
              </Box>
            ))}
          </Box>
        )}
      </CardContent>
    </Card>
  );
}
