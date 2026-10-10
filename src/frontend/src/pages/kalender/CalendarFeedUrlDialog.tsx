import { useTranslation } from 'react-i18next';
import Alert from '@mui/material/Alert';
import Button from '@mui/material/Button';
import Dialog from '@mui/material/Dialog';
import DialogActions from '@mui/material/DialogActions';
import DialogContent from '@mui/material/DialogContent';
import DialogTitle from '@mui/material/DialogTitle';
import TextField from '@mui/material/TextField';
import Typography from '@mui/material/Typography';
import useMediaQuery from '@mui/material/useMediaQuery';
import { useTheme } from '@mui/material/styles';
import ContentCopyIcon from '@mui/icons-material/ContentCopy';

interface CalendarFeedUrlDialogProps {
  /** Name of the feed the URL belongs to; `null` keeps the dialog closed. */
  feedName: string | null;
  /** The subscription URL carrying the freshly issued token. */
  url: string | null;
  onCopy: (url: string) => void;
  onClose: () => void;
}

/**
 * Shows a calendar feed's subscription URL right after it was created or rotated.
 *
 * The server stores only a hash of the feed token (#2171), so this is the one
 * moment the URL exists in the UI: closing the dialog discards it, and a lost URL
 * is replaced by rotating the token.
 */
export default function CalendarFeedUrlDialog({ feedName, url, onCopy, onClose }: CalendarFeedUrlDialogProps) {
  const { t } = useTranslation();
  const theme = useTheme();
  const fullScreen = useMediaQuery(theme.breakpoints.down('sm'));
  const open = feedName !== null && url !== null;

  return (
    <Dialog
      open={open}
      onClose={(_event, reason) => {
        // A stray click beside the dialog must not discard the only copy of the URL;
        // closing takes the button or Escape (#2171).
        if (reason !== 'backdropClick') onClose();
      }}
      fullScreen={fullScreen}
      maxWidth="sm"
      fullWidth
      aria-labelledby="feed-url-dialog-title"
      data-testid="feed-url-dialog"
    >
      <DialogTitle id="feed-url-dialog-title">{t('pages.calendar.feedUrlTitle', { name: feedName ?? '' })}</DialogTitle>
      <DialogContent>
        <Alert severity="warning" sx={{ mb: 2 }} data-testid="feed-url-shown-once">
          {t('pages.calendar.feedUrlShownOnce')}
        </Alert>
        <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
          {t('pages.calendar.feedUrlHelper')}
        </Typography>
        <TextField
          value={url ?? ''}
          label={t('pages.calendar.feedUrlLabel')}
          fullWidth
          multiline
          slotProps={{
            input: { readOnly: true, sx: { fontFamily: 'monospace', wordBreak: 'break-all' } },
            htmlInput: { 'data-testid': 'feed-url-value' },
          }}
          onFocus={(event) => event.target.select()}
        />
      </DialogContent>
      <DialogActions>
        <Button
          startIcon={<ContentCopyIcon />}
          onClick={() => {
            if (url) onCopy(url);
          }}
          data-testid="feed-url-copy-btn"
        >
          {t('pages.calendar.copyUrl')}
        </Button>
        <Button variant="contained" onClick={onClose} data-testid="feed-url-close-btn">
          {t('common.close')}
        </Button>
      </DialogActions>
    </Dialog>
  );
}
