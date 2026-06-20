import { useEffect, useState } from 'react';
import { useTranslation } from 'react-i18next';
import Button from '@mui/material/Button';
import PestControlIcon from '@mui/icons-material/PestControl';
import PestDetectionDialog from './PestDetectionDialog';
import { useAppDispatch, useAppSelector } from '@/store/hooks';
import { isLightMode } from '@/config/mode';
import { fetchPestDetectionStatus } from '@/store/slices/pestDetectionSlice';

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
 */
export default function PestScanButton({ plantKey, size = 'small' }: PestScanButtonProps) {
  const { t } = useTranslation();
  const dispatch = useAppDispatch();
  const status = useAppSelector((s) => s.pestDetection.status);
  const [open, setOpen] = useState(false);

  useEffect(() => {
    if (!isLightMode && status == null) {
      dispatch(fetchPestDetectionStatus());
    }
  }, [dispatch, status]);

  if (isLightMode || !status?.available) {
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
