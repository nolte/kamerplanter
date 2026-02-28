import { useTranslation } from 'react-i18next';
import Box from '@mui/material/Box';
import Chip from '@mui/material/Chip';
import Tooltip from '@mui/material/Tooltip';
import type { DeliveryChannel } from '@/api/types';

interface Props {
  channels: DeliveryChannel[];
}

export default function DeliveryChannelChips({ channels }: Props) {
  const { t } = useTranslation();

  if (channels.length === 0) return null;

  return (
    <Box sx={{ display: 'flex', gap: 0.5, flexWrap: 'wrap', mt: 0.5 }}>
      {channels.map((ch) => (
        <Tooltip
          key={ch.channel_id}
          title={
            ch.notes
              ? `${t(`enums.applicationMethod.${ch.application_method}`)} — ${ch.notes}`
              : t(`enums.applicationMethod.${ch.application_method}`)
          }
        >
          <Chip
            label={ch.label || ch.channel_id}
            size="small"
            variant={ch.enabled ? 'filled' : 'outlined'}
            color={ch.enabled ? 'info' : 'default'}
            sx={{ opacity: ch.enabled ? 1 : 0.6 }}
          />
        </Tooltip>
      ))}
    </Box>
  );
}
