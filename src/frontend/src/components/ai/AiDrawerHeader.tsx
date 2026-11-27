import { useTranslation } from 'react-i18next';
import Stack from '@mui/material/Stack';
import Typography from '@mui/material/Typography';
import IconButton from '@mui/material/IconButton';
import CloseIcon from '@mui/icons-material/Close';

// UI-NFR-001 R-011: a 48x48 touch target; a phone-wide drawer leaves no backdrop to tap away (#3162).
const CLOSE_SX = { minWidth: 48, minHeight: 48 } as const;

interface AiDrawerHeaderProps {
  title: string;
  onClose: () => void;
  closeTestId: string;
}

/** Title row of a KI drawer with its close button top right (#3162); the button calls the drawer's `onClose`. */
export default function AiDrawerHeader({ title, onClose, closeTestId }: AiDrawerHeaderProps) {
  const { t } = useTranslation();
  return (
    <Stack direction="row" spacing={1} sx={{ alignItems: 'center', justifyContent: 'space-between', mb: 1 }}>
      <Typography variant="h6">{title}</Typography>
      <IconButton onClick={onClose} edge="end" aria-label={t('common.close')} data-testid={closeTestId} sx={CLOSE_SX}>
        <CloseIcon />
      </IconButton>
    </Stack>
  );
}
