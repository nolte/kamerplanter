import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import { useTranslation } from 'react-i18next';
import Alert from '@mui/material/Alert';
import Box from '@mui/material/Box';
import Button from '@mui/material/Button';
import Dialog from '@mui/material/Dialog';
import DialogActions from '@mui/material/DialogActions';
import DialogContent from '@mui/material/DialogContent';
import DialogTitle from '@mui/material/DialogTitle';
import Skeleton from '@mui/material/Skeleton';
import Typography from '@mui/material/Typography';
import useMediaQuery from '@mui/material/useMediaQuery';
import { useTheme } from '@mui/material/styles';
import RefreshIcon from '@mui/icons-material/Refresh';
import { QRCodeSVG } from 'qrcode.react';
import ErrorDisplay from '@/components/common/ErrorDisplay';
import { createDevicePairing } from '@/api/endpoints/auth';
import { parseApiError } from '@/api/errors';
import { isLightMode } from '@/config/mode';
import type { DevicePairingCreated } from '@/api/types';

interface ConnectDeviceDialogProps {
  open: boolean;
  onClose: () => void;
}

/** Edge length of the rendered QR code, in CSS pixels. */
const QR_SIZE_DESKTOP = 240;
const QR_SIZE_MOBILE = 200;

/**
 * Shared visual shell for the QR's footprint — the loaded QR (either variant)
 * and its loading placeholder alike. The fixed white background is
 * intentional and MUST stay: it is what keeps the QR's own black/white
 * modules scannable on a dark theme, independent of the app palette. The
 * `divider` border is what this shell adds on top of that: in light mode the
 * dialog surface (`background.paper`) is the same white as this box, so
 * without a border the QR card has no perceivable boundary at all (UI-NFR-002
 * R-017 / WCAG 1.4.11 non-text contrast). Reusing the identical shell for the
 * loading placeholder also means the skeleton occupies exactly the footprint
 * the real QR will take, so nothing visibly jumps once the fetch resolves.
 */
const QR_CONTAINER_SX = {
  p: 2,
  bgcolor: 'common.white',
  border: 1,
  borderColor: 'divider',
  borderRadius: 1,
  lineHeight: 0,
} as const;

/**
 * Version carried by the light-mode instance-discovery deep link (#1118 P13). It
 * shares the `v` version space with the full-mode pairing payload on purpose: a
 * future app branches on it, and it lets the app refuse a shape it does not
 * recognize instead of misinterpreting it.
 */
const DISCOVERY_PAYLOAD_VERSION = 1;

/**
 * Fixed deep-link path the discovery URL points at (#1118 P13). The future
 * Android app declares an `intent-filter` on this path with a **wildcard host**
 * (`android:host="*"`), so scanning `https://<any-instance>/connect?v=1` with the
 * phone's system camera offers to open the app (or, without it, this instance's
 * `/connect` browser landing). It is a fixed literal, not a route import, because
 * the string is a wire contract the app is built against.
 */
const DISCOVERY_DEEP_LINK_PATH = '/connect';

/**
 * "Connect mobile device" — a QR dialog with two mode-dependent variants (#1118).
 *
 * **Full mode (`isLightMode === false`) — account pairing.** Renders one
 * short-lived QR *pairing code*. The code inside is a bearer credential: whoever
 * scans it within its ~90 s window receives a full token pair for this account.
 * Three consequences shape this variant, and each is pinned by a test:
 *
 * 1. **The code is never shown as text.** It goes into the QR payload and
 *    nowhere else — not into a copyable field, not into an error message. A
 *    bystander (or a screen share, or a screenshot in a support ticket) must not
 *    be able to read it. Only a camera pointed at the screen can.
 * 2. **The code never leaves component state.** No Redux, no `localStorage`, no
 *    URL parameter. Closing the dialog drops it, and a response that arrives
 *    after the close is discarded rather than stored — otherwise a code would
 *    outlive the moment the user chose to show it.
 * 3. **Expiry is visible.** The server's `expires_in` seeds a per-second
 *    countdown; at zero the QR is replaced by an expired state, because a QR
 *    that still looks scannable but is not produces exactly the kind of silent
 *    failure the user cannot diagnose. Refreshing asks for a new code.
 *
 * **Light mode (`isLightMode === true`, REQ-027 anonymous) — instance discovery.**
 * A light-mode instance has no accounts and the pairing endpoints answer 404, so
 * there is nothing to log in to. This variant instead renders a **plain-URL** QR
 * — an app-link-style deep link `https://<this instance's origin>/connect?v=1`,
 * not a JSON blob. A JSON payload is opaque to a phone's system camera; an https
 * URL is recognized as a link, so the camera can offer to open the Kamerplanter
 * app (which declares a wildcard-host `intent-filter` on `/connect`) or fall back
 * to the browser landing at the same path. It carries no credential, no `code`,
 * makes no backend call, has no countdown and no expiry: scanning it only points
 * a mobile app at this instance and never grants account access. The origin is
 * taken from `window.location.origin` (the address the user actually reaches the
 * instance through) because the runtime config exposes no base URL.
 *
 * The full-mode pairing QR above stays deliberately **opaque JSON, in-app-scan
 * only** — a one-time bearer credential must not become an interceptable deep
 * link a system camera would route anywhere.
 */
export default function ConnectDeviceDialog({ open, onClose }: ConnectDeviceDialogProps) {
  const { t } = useTranslation();
  const theme = useTheme();
  const fullScreen = useMediaQuery(theme.breakpoints.down('sm'));

  // Read once per render: which variant this dialog is. The whole pairing
  // machinery below stays dormant in the discovery variant — no request, no
  // timer, no credential in state.
  const discovery = isLightMode;

  const [pairing, setPairing] = useState<DevicePairingCreated | null>(null);
  const [remaining, setRemaining] = useState(0);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  /**
   * Sequence number of the newest issuance request. Bumping it invalidates every
   * response still in flight, which is what makes "closing discards the code"
   * true even when the user closes the dialog mid-request: the late response
   * finds a stale id and is dropped instead of populating state behind a closed
   * dialog.
   */
  const requestIdRef = useRef(0);

  const requestCode = useCallback(async () => {
    const requestId = ++requestIdRef.current;
    setLoading(true);
    setError(null);
    // Drop the previous code *before* asking for the next one. Nothing renders
    // it at this point anyway (the refresh action only exists in the expired
    // state), so this is about lifetime, not pixels: a superseded credential
    // should not sit in memory for the duration of a network round-trip.
    setPairing(null);
    setRemaining(0);
    try {
      const created = await createDevicePairing();
      if (requestIdRef.current !== requestId) return;
      setPairing(created);
      setRemaining(created.expires_in);
    } catch (err) {
      if (requestIdRef.current !== requestId) return;
      setError(parseApiError(err));
    } finally {
      if (requestIdRef.current === requestId) setLoading(false);
    }
  }, []);

  useEffect(() => {
    // The discovery variant makes NO backend call: the instance already knows
    // its own URL, so there is nothing to fetch and nothing to expire.
    if (!open || discovery) return;
    void requestCode();
    return () => {
      // Closing (or unmounting) is a hard reset, not a pause: the code is a live
      // credential and must not survive the dialog. MUI unmounts the dialog body
      // on close, so the *visible* half is free — this clears the half the DOM
      // cannot show, and the id bump disowns any request still in flight.
      requestIdRef.current += 1;
      setPairing(null);
      setRemaining(0);
      setError(null);
      setLoading(false);
    };
  }, [open, discovery, requestCode]);

  const expired = pairing !== null && remaining <= 0;

  useEffect(() => {
    if (!open || discovery || pairing === null || expired) return;
    const interval = setInterval(() => {
      setRemaining((seconds) => (seconds <= 1 ? 0 : seconds - 1));
    }, 1000);
    return () => clearInterval(interval);
    // `expired` in the deps is what stops the ticking: it flips exactly once,
    // which re-runs this effect and clears the interval.
  }, [open, discovery, pairing, expired]);

  /**
   * The documented full-mode QR payload contract — `{"v": …, "url": …, "code": …}`.
   * Field order is part of the shape a scanner built against v1 reads, so it is
   * written out literally rather than spread from the response object.
   */
  const qrPayload = useMemo(
    () =>
      pairing === null
        ? ''
        : JSON.stringify({ v: pairing.payload_version, url: pairing.server_url, code: pairing.code }),
    [pairing],
  );

  /**
   * The light-mode instance-discovery deep link —
   * `https://<origin>/connect?v=1`, a plain URL string (never JSON) so a phone's
   * system camera recognizes it as a link. It carries no credential (`code` has
   * no place in it), so it is derived synchronously from the address the browser
   * reached this instance through. `window.location.origin` already includes the
   * scheme and host, so the value is an absolute https URL on production hosts.
   */
  const discoveryUrl = useMemo(
    () =>
      `${window.location.origin}${DISCOVERY_DEEP_LINK_PATH}?v=${DISCOVERY_PAYLOAD_VERSION}`,
    [],
  );

  const qrSize = fullScreen ? QR_SIZE_MOBILE : QR_SIZE_DESKTOP;

  const titleKey = discovery
    ? 'pages.auth.devicePairing.discovery.dialogTitle'
    : 'pages.auth.devicePairing.dialogTitle';
  const introKey = discovery
    ? 'pages.auth.devicePairing.discovery.intro'
    : 'pages.auth.devicePairing.intro';

  return (
    <Dialog
      open={open}
      onClose={onClose}
      fullScreen={fullScreen}
      maxWidth="xs"
      fullWidth
      data-testid="connect-device-dialog"
      aria-labelledby="connect-device-dialog-title"
      aria-describedby="connect-device-dialog-intro"
    >
      <DialogTitle id="connect-device-dialog-title">{t(titleKey)}</DialogTitle>
      <DialogContent>
        <Typography id="connect-device-dialog-intro" variant="body2" color="text.secondary" sx={{ mb: 1.5 }}>
          {t(introKey)}
        </Typography>
        <Box component="ol" sx={{ pl: 2.5, m: 0, mb: 2 }}>
          <Typography component="li" variant="body2" color="text.secondary">
            {t(discovery ? 'pages.auth.devicePairing.discovery.stepInstall' : 'pages.auth.devicePairing.stepInstall')}
          </Typography>
          <Typography component="li" variant="body2" color="text.secondary">
            {t(discovery ? 'pages.auth.devicePairing.discovery.stepScan' : 'pages.auth.devicePairing.stepScan')}
          </Typography>
          <Typography component="li" variant="body2" color="text.secondary">
            {t(discovery ? 'pages.auth.devicePairing.discovery.stepDone' : 'pages.auth.devicePairing.stepDone')}
          </Typography>
        </Box>

        <Box sx={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 1.5 }}>
          {discovery ? (
            // Instance discovery: a static, credential-free QR. No loading, no
            // error, no countdown, no expiry — the instance already knows its URL.
            <Box data-testid="device-discovery-qr" sx={QR_CONTAINER_SX}>
              <QRCodeSVG
                value={discoveryUrl}
                size={qrSize}
                level="M"
                title={t('pages.auth.devicePairing.discovery.qrTitle')}
              />
            </Box>
          ) : (
            <>
              {loading && (
                // A distinct loading state, not an empty frame: an absent QR and a
                // pending QR look identical otherwise (UI-NFR-004 R-020).
                <Box
                  data-testid="loading-skeleton"
                  aria-busy="true"
                  aria-label={t('common.loading')}
                  sx={QR_CONTAINER_SX}
                >
                  <Skeleton variant="rectangular" width={qrSize} height={qrSize} />
                </Box>
              )}

              {!loading && error !== null && (
                <Box sx={{ width: '100%' }} data-testid="device-pairing-error">
                  <ErrorDisplay error={error} onRetry={requestCode} />
                </Box>
              )}

              {!loading && error === null && pairing !== null && !expired && (
                <>
                  <Box data-testid="device-pairing-qr" sx={QR_CONTAINER_SX}>
                    <QRCodeSVG
                      value={qrPayload}
                      size={qrSize}
                      level="M"
                      title={t('pages.auth.devicePairing.qrTitle')}
                    />
                  </Box>
                  <Typography
                    variant="body2"
                    role="timer"
                    data-testid="device-pairing-countdown"
                    sx={{ fontVariantNumeric: 'tabular-nums' }}
                  >
                    {t('pages.auth.devicePairing.expiresIn', { seconds: remaining })}
                  </Typography>
                </>
              )}

              {!loading && error === null && expired && (
                <>
                  <Alert severity="warning" sx={{ width: '100%' }} data-testid="device-pairing-expired">
                    {t('pages.auth.devicePairing.expired')}
                  </Alert>
                  <Button
                    variant="contained"
                    startIcon={<RefreshIcon />}
                    onClick={requestCode}
                    data-testid="device-pairing-refresh"
                    // UI-NFR-001 R-011 — 48px minimum touch target on mobile.
                    sx={{ minHeight: 48 }}
                  >
                    {t('pages.auth.devicePairing.refresh')}
                  </Button>
                </>
              )}
            </>
          )}

          <Alert
            severity="info"
            icon={false}
            sx={{ width: '100%', mt: 0.5 }}
            data-testid={discovery ? 'device-discovery-note' : undefined}
          >
            <Typography variant="body2">
              {t(discovery ? 'pages.auth.devicePairing.discovery.securityNote' : 'pages.auth.devicePairing.securityHint')}
            </Typography>
          </Alert>
        </Box>
      </DialogContent>
      <DialogActions>
        {/* UI-NFR-001 R-011 — 48px minimum touch target on mobile. */}
        <Button onClick={onClose} data-testid="connect-device-close" sx={{ minHeight: 48 }}>
          {t('common.close')}
        </Button>
      </DialogActions>
    </Dialog>
  );
}
