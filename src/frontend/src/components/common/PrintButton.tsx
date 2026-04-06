import { useState, useCallback } from 'react';
import { useTranslation } from 'react-i18next';
import Button from '@mui/material/Button';
import IconButton from '@mui/material/IconButton';
import Tooltip from '@mui/material/Tooltip';
import CircularProgress from '@mui/material/CircularProgress';
import PrintIcon from '@mui/icons-material/Print';
import { useNotification } from '@/hooks/useNotification';

interface PrintButtonProps {
  /** Async function that returns the PDF blob to download. */
  onPrint: () => Promise<Blob>;
  /** The suggested filename for the downloaded file (e.g. "nutrient-plan-abc.pdf"). */
  filename: string;
  /** Visual variant: 'icon' renders a compact IconButton, 'button' renders a full Button. Default: 'icon'. */
  variant?: 'icon' | 'button';
  /** Accessible label and tooltip text. Falls back to the generic i18n key 'print.downloadPdf'. */
  label?: string;
  disabled?: boolean;
}

/**
 * Triggers a PDF download via blob URL.
 * Shows a loading state during generation, a success notification on completion,
 * and a persistent error snackbar on failure.
 *
 * Use variant="icon" inside page headers alongside other icon actions.
 * Use variant="button" in empty areas or action bars where more prominence is needed.
 */
export function PrintButton({
  onPrint,
  filename,
  variant = 'icon',
  label,
  disabled = false,
}: PrintButtonProps) {
  const { t } = useTranslation();
  const notification = useNotification();
  const [loading, setLoading] = useState(false);

  const handleClick = useCallback(async () => {
    setLoading(true);
    try {
      const blob = await onPrint();

      const url = URL.createObjectURL(blob);
      const anchor = document.createElement('a');
      anchor.href = url;
      anchor.download = filename;
      document.body.appendChild(anchor);
      anchor.click();
      document.body.removeChild(anchor);
      URL.revokeObjectURL(url);

      notification.success(t('print.success'));
    } catch {
      notification.error(t('print.error'));
    } finally {
      setLoading(false);
    }
  }, [onPrint, filename, notification, t]);

  const tooltipLabel = label ?? t('print.downloadPdf');
  const ariaLabel = loading ? t('print.printing') : tooltipLabel;

  if (variant === 'icon') {
    return (
      <Tooltip title={ariaLabel}>
        {/* span wrapper required so Tooltip works when button is disabled */}
        <span>
          <IconButton
            onClick={handleClick}
            disabled={disabled || loading}
            aria-label={ariaLabel}
            color="default"
            data-testid="print-button"
          >
            {loading ? <CircularProgress size={20} color="inherit" /> : <PrintIcon />}
          </IconButton>
        </span>
      </Tooltip>
    );
  }

  return (
    <Button
      variant="outlined"
      startIcon={loading ? <CircularProgress size={18} color="inherit" /> : <PrintIcon />}
      onClick={handleClick}
      disabled={disabled || loading}
      aria-label={ariaLabel}
      data-testid="print-button"
    >
      {loading ? t('print.printing') : (label ?? t('print.downloadPdf'))}
    </Button>
  );
}

// Default export for backwards compatibility with existing lazy-loaded usages.
export default PrintButton;
