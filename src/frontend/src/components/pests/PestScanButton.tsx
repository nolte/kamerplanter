import { useEffect, useState } from 'react';
import { useTranslation } from 'react-i18next';
import Button from '@mui/material/Button';
import PestControlIcon from '@mui/icons-material/PestControl';
import PestDetectionDialog from './PestDetectionDialog';
import { useAppDispatch, useAppSelector } from '@/store/hooks';
import { isLightMode } from '@/config/mode';
import { fetchPestDetectionStatus } from '@/store/slices/pestDetectionSlice';
import { useTenantPermissions } from '@/hooks/useTenantPermissions';

interface PestScanButtonProps {
  plantKey: string;
  size?: 'small' | 'medium' | 'large';
}

/**
 * REQ-044 §7 — "Auf Schädlinge prüfen" entry point on a plant.
 *
 * Fetches the tenant-scoped feature status once and hides itself when no
 * adapter is active (Szenario 7) or in Light mode (§7), so the app stays fully
 * functional when the feature is off.
 *
 * It also hides itself below grower (#1333): the server refuses
 * `POST /pests/plants/{key}/detect` and the feedback write for a viewer, and a
 * button that opens a dialog only to end in a 403 is a guard that is visible
 * and inert. The gate sits here, on the shared entry point, so every page that
 * mounts the button inherits it. "No active tenant yet" is not a refusal — the
 * same reading as `RequireRole` — so the button does not flash away during the
 * tenant bootstrap.
 */
export default function PestScanButton({ plantKey, size = 'small' }: PestScanButtonProps) {
  const { t } = useTranslation();
  const dispatch = useAppDispatch();
  const status = useAppSelector((s) => s.pestDetection.status);
  const { canEdit, hasTenant } = useTenantPermissions();
  const [open, setOpen] = useState(false);

  useEffect(() => {
    if (status == null) {
      dispatch(fetchPestDetectionStatus());
    }
  }, [dispatch, status]);

  // Self-hosted / demo adapters work in light mode (no consent, no egress);
  // only the cloud path (which needs consent) stays blocked there (§3.3).
  const active = status?.active_adapter;
  const activeRequiresConsent = active != null && status?.adapters?.[active]?.requires_consent != null;
  const roleRestricted = hasTenant && !canEdit;
  if (!status?.available || (isLightMode && activeRequiresConsent) || roleRestricted) {
    return null;
  }

  return (
    <>
      <Button
        startIcon={<PestControlIcon />}
        onClick={() => setOpen(true)}
        data-testid="pest-scan-button"
        size={size}
        variant="outlined"
        sx={{ minHeight: 44 }}
      >
        {t('pages.pests.scanButton')}
      </Button>
      <PestDetectionDialog open={open} onClose={() => setOpen(false)} plantKey={plantKey} />
    </>
  );
}
