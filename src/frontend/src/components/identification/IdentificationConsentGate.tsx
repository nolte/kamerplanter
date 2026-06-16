import { useTranslation } from 'react-i18next';
import Box from '@mui/material/Box';
import Button from '@mui/material/Button';
import List from '@mui/material/List';
import ListItem from '@mui/material/ListItem';
import ListItemIcon from '@mui/material/ListItemIcon';
import ListItemText from '@mui/material/ListItemText';
import Link from '@mui/material/Link';
import Typography from '@mui/material/Typography';
import Alert from '@mui/material/Alert';
import Divider from '@mui/material/Divider';
import CircularProgress from '@mui/material/CircularProgress';
import PrivacyTipIcon from '@mui/icons-material/PrivacyTip';
import SendIcon from '@mui/icons-material/Send';
import DeleteOutlinedIcon from '@mui/icons-material/DeleteOutlined';
import StorageIcon from '@mui/icons-material/Storage';
import InfoOutlinedIcon from '@mui/icons-material/InfoOutlined';

interface IdentificationConsentGateProps {
  /** True once the user has granted `plant_identification`. */
  granted: boolean;
  loading: boolean;
  granting: boolean;
  error: string | null;
  onGrant: () => void;
  onDecline: () => void;
  /**
   * Whether to render the revocation hint with the link to the privacy
   * settings. In the Light mode (REQ-027) there is no backend consent record
   * and no privacy settings tab, so the link would be dead — the parent passes
   * `false` there to avoid a broken link while keeping the transparency notice.
   * Defaults to `true` (full mode behaviour).
   */
  showPrivacyLink?: boolean;
}

/**
 * REQ-029 §5 / REQ-029-A §0.1.1 point 2 / UI-NFR-013 — hard consent gate.
 *
 * In Phase 1 every identification sends the photo to Pl@ntNet (third-country
 * transfer), so consent is a precondition, not an optional fallback. This panel
 * blocks the capture UI until `plant_identification` is granted and is
 * transparent about the recipient and the stored query metadata.
 *
 * Usability improvements over v1:
 * - Structured bullet list replaces a dense paragraph (easier to scan)
 * - Icons per bullet give visual anchors (sent to / stripped / not stored / metadata)
 * - Revocation hint with link to privacy settings (UI-NFR-013 §3.4)
 * - Buttons stacked on xs (full-width, column-reverse so Accept stays on top),
 *   side-by-side on sm+ with Decline left / Accept right
 * - autoFocus on Accept button (primary action, dialog focus management)
 * - minHeight 44px on both buttons (touch target compliance UI-NFR-001 R-011)
 */
export default function IdentificationConsentGate({
  granted,
  loading,
  granting,
  error,
  onGrant,
  onDecline,
  showPrivacyLink = true,
}: IdentificationConsentGateProps) {
  const { t } = useTranslation();

  if (loading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', py: 4 }}>
        <CircularProgress size={28} data-testid="consent-gate-loading" />
      </Box>
    );
  }

  if (granted) return null;

  const bullets: Array<{ icon: React.ReactElement; labelKey: string }> = [
    { icon: <SendIcon fontSize="small" color="action" />, labelKey: 'consentBullet1' },
    { icon: <DeleteOutlinedIcon fontSize="small" color="action" />, labelKey: 'consentBullet2' },
    { icon: <StorageIcon fontSize="small" color="action" />, labelKey: 'consentBullet3' },
    { icon: <InfoOutlinedIcon fontSize="small" color="action" />, labelKey: 'consentBullet4' },
  ];

  return (
    <Box
      role="region"
      aria-label={t('pages.plantIdentification.consentTitle')}
      data-testid="identification-consent-gate"
      sx={{ py: 1 }}
    >
      {/* Header */}
      <Box sx={{ display: 'flex', gap: 1.5, alignItems: 'center', mb: 1.5 }}>
        <PrivacyTipIcon color="primary" aria-hidden fontSize="medium" />
        <Typography variant="h6" component="h2">
          {t('pages.plantIdentification.consentTitle')}
        </Typography>
      </Box>

      <Typography variant="body2" color="text.secondary" sx={{ mb: 1.5 }}>
        {t('pages.plantIdentification.consentDataSentTo')}
      </Typography>

      {/* Structured data-flow bullets — scannable for the casual user */}
      <List dense disablePadding sx={{ mb: 1.5 }}>
        {bullets.map(({ icon, labelKey }) => (
          <ListItem key={labelKey} disableGutters sx={{ alignItems: 'flex-start', py: 0.25 }}>
            <ListItemIcon sx={{ minWidth: 32, mt: 0.25 }}>{icon}</ListItemIcon>
            <ListItemText
              primary={
                <Typography variant="body2">
                  {t(`pages.plantIdentification.${labelKey}`)}
                </Typography>
              }
            />
          </ListItem>
        ))}
      </List>

      <Divider sx={{ my: 1.5 }} />

      {/* Revocation hint — the privacy-settings link only exists in full mode. */}
      <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mb: 1.5 }}>
        {showPrivacyLink ? (
          <>
            {t('pages.plantIdentification.consentRevoke')}{' '}
            <Link href="/settings#privacy" variant="caption">
              {t('pages.plantIdentification.consentPrivacyLink')}
            </Link>
          </>
        ) : (
          t('pages.plantIdentification.consentRevokeLocal')
        )}
      </Typography>

      {error && (
        <Alert severity="error" sx={{ mb: 2 }} data-testid="consent-gate-error">
          {error}
        </Alert>
      )}

      {/* Action buttons: stacked column-reverse on xs so Accept stays on top (thumb zone),
          side-by-side on sm+ */}
      <Box
        sx={{
          display: 'flex',
          flexDirection: { xs: 'column-reverse', sm: 'row' },
          gap: 1,
          justifyContent: 'flex-end',
        }}
      >
        <Button
          variant="text"
          onClick={onDecline}
          data-testid="consent-decline"
          aria-label={t('pages.plantIdentification.consentDeclineAria')}
          sx={{ minHeight: 44 }}
        >
          {t('pages.plantIdentification.consentDecline')}
        </Button>
        <Button
          variant="contained"
          onClick={onGrant}
          disabled={granting}
          autoFocus
          startIcon={granting ? <CircularProgress size={16} /> : undefined}
          data-testid="consent-accept"
          sx={{ minHeight: 44 }}
        >
          {t('pages.plantIdentification.consentAccept')}
        </Button>
      </Box>
    </Box>
  );
}
