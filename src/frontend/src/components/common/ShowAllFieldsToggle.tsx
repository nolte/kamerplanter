import { useTranslation } from 'react-i18next';
import Button from '@mui/material/Button';
import ExpandMoreIcon from '@mui/icons-material/ExpandMore';
import ExpandLessIcon from '@mui/icons-material/ExpandLess';

interface ShowAllFieldsToggleProps {
  showAll: boolean;
  onToggle: () => void;
}

export default function ShowAllFieldsToggle({ showAll, onToggle }: ShowAllFieldsToggleProps) {
  const { t } = useTranslation();

  return (
    <Button
      size="small"
      onClick={onToggle}
      startIcon={showAll ? <ExpandLessIcon /> : <ExpandMoreIcon />}
      sx={{ mb: 1 }}
      // A disclosure button: its state is announced (WCAG 4.1.2), and it is what
      // the E2E harness reads to know the fields really are shown (#1897).
      aria-expanded={showAll}
      data-testid="show-all-fields-toggle"
    >
      {showAll ? t('common.showFewerFields') : t('common.showAllFields')}
    </Button>
  );
}
