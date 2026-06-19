import { useCallback, useEffect, useMemo, useState } from 'react';
import { useTranslation } from 'react-i18next';
import Box from '@mui/material/Box';
import CircularProgress from '@mui/material/CircularProgress';
import FormControlLabel from '@mui/material/FormControlLabel';
import FormHelperText from '@mui/material/FormHelperText';
import HomeIcon from '@mui/icons-material/Home';
import Switch from '@mui/material/Switch';
import Typography from '@mui/material/Typography';
import { useSmartHomeEnabled } from '@/hooks/useSmartHomeEnabled';
import { useNotification } from '@/hooks/useNotification';
import {
  getHaPublishStatus,
  setHaPublishStatus,
  type HaPublishEntityType,
} from '@/api/endpoints/haPublish';

interface HaPublishToggleProps {
  entityType: HaPublishEntityType;
  entityKey: string;
}

/**
 * Lets the user choose whether a single entity (plant/tank/location) is
 * published to Home Assistant as a sensor. Only rendered when the user has
 * enabled smart-home features (opt-in: publishing is off until toggled on).
 */
export default function HaPublishToggle({ entityType, entityKey }: HaPublishToggleProps) {
  const { t } = useTranslation();
  const { isSmartHomeEnabled } = useSmartHomeEnabled();
  const notify = useNotification();

  const [enabled, setEnabled] = useState(false);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);

  // Stable IDs for aria-describedby linkage (UI-NFR-002 R-013/R-014)
  const helperId = useMemo(
    () => `ha-publish-helper-${entityType}-${entityKey}`,
    [entityType, entityKey],
  );

  useEffect(() => {
    if (!isSmartHomeEnabled || !entityKey) return;
    let active = true;
    setLoading(true);
    getHaPublishStatus(entityType, entityKey)
      .then((s) => {
        if (active) setEnabled(s.enabled);
      })
      .catch(() => {
        if (active) notify.error(t('haPublish.loadError'));
      })
      .finally(() => {
        if (active) setLoading(false);
      });
    return () => {
      active = false;
    };
  }, [isSmartHomeEnabled, entityType, entityKey, notify, t]);

  const handleChange = useCallback(
    async (_event: React.ChangeEvent<HTMLInputElement>, checked: boolean) => {
      const previous = enabled;
      setEnabled(checked);
      setSaving(true);
      try {
        await setHaPublishStatus(entityType, entityKey, checked);
        notify.success(checked ? t('haPublish.enabled') : t('haPublish.disabled'));
      } catch {
        setEnabled(previous);
        notify.error(t('haPublish.saveError'));
      } finally {
        setSaving(false);
      }
    },
    [enabled, entityType, entityKey, notify, t],
  );

  const helperText = useMemo(() => t('haPublish.helper'), [t]);

  if (!isSmartHomeEnabled) return null;

  const busy = loading || saving;

  return (
    <Box sx={{ mt: 2 }} data-testid="ha-publish-toggle">
      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
        {/* Decorative icon — hidden from assistive technology (UI-NFR-002 R-012) */}
        <HomeIcon fontSize="small" color="action" aria-hidden="true" />
        <Typography variant="subtitle2">{t('haPublish.sectionTitle')}</Typography>
        {busy && (
          <CircularProgress
            size={16}
            aria-label={t('haPublish.loadingAriaLabel')}
          />
        )}
      </Box>
      <FormControlLabel
        sx={{ mt: 0.5 }}
        control={
          <Switch
            checked={enabled}
            onChange={handleChange}
            disabled={busy}
            aria-busy={busy}
            slotProps={{
              input: {
                'aria-label': t('haPublish.label'),
                'aria-describedby': helperId,
              },
            }}
          />
        }
        label={t('haPublish.label')}
      />
      {/* id links this helper text to the switch via aria-describedby (UI-NFR-002 R-013) */}
      <FormHelperText id={helperId}>{helperText}</FormHelperText>
    </Box>
  );
}
