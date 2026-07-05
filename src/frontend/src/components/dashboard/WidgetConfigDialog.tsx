import { useState } from 'react';
import { useTranslation } from 'react-i18next';
import Dialog from '@mui/material/Dialog';
import DialogTitle from '@mui/material/DialogTitle';
import DialogContent from '@mui/material/DialogContent';
import DialogActions from '@mui/material/DialogActions';
import TextField from '@mui/material/TextField';
import Button from '@mui/material/Button';
import Stack from '@mui/material/Stack';
import type { WidgetKey } from '@/config/dashboardWidgetCatalog';

interface ConfigField {
  name: string;
  type: 'text' | 'number';
}

/** Per-widget config field definitions (only for widgets with hasConfig). */
const CONFIG_SCHEMA: Partial<Record<WidgetKey, ConfigField[]>> = {
  weather_forecast: [{ name: 'location', type: 'text' }],
  sensor_live: [{ name: 'location', type: 'text' }],
  harvest_forecast: [{ name: 'timeframe_days', type: 'number' }],
};

export default function WidgetConfigDialog({
  open,
  widgetKey,
  config,
  onClose,
  onSave,
}: {
  open: boolean;
  widgetKey: string;
  config: Record<string, unknown>;
  onClose: () => void;
  onSave: (config: Record<string, unknown>) => void;
}) {
  const { t } = useTranslation();
  const fields = CONFIG_SCHEMA[widgetKey as WidgetKey] ?? [];
  const [draft, setDraft] = useState<Record<string, unknown>>({ ...config });

  const handleSave = () => {
    onSave(draft);
    onClose();
  };

  return (
    <Dialog open={open} onClose={onClose} fullWidth maxWidth="xs" data-testid="widget-config-dialog">
      <DialogTitle>
        {t('dashboard.config.title', { widget: t(`dashboard.widgets.${widgetKey}.label`) })}
      </DialogTitle>
      <DialogContent>
        <Stack spacing={2} sx={{ mt: 1 }}>
          {fields.length === 0 && (
            <TextField disabled label={t('dashboard.config.noOptions')} value="" variant="standard" />
          )}
          {fields.map((field) => (
            <TextField
              key={field.name}
              label={t(`dashboard.config.fields.${field.name}`, { defaultValue: field.name })}
              type={field.type}
              value={(draft[field.name] as string | number | undefined) ?? ''}
              onChange={(e) =>
                setDraft((prev) => ({
                  ...prev,
                  [field.name]: field.type === 'number' ? Number(e.target.value) : e.target.value,
                }))
              }
              fullWidth
              slotProps={{ htmlInput: { 'data-testid': `config-field-${field.name}` } }}
            />
          ))}
        </Stack>
      </DialogContent>
      <DialogActions>
        <Button onClick={onClose} sx={{ minHeight: 48 }}>
          {t('common.cancel')}
        </Button>
        <Button onClick={handleSave} variant="contained" sx={{ minHeight: 48 }} data-testid="widget-config-save">
          {t('common.save')}
        </Button>
      </DialogActions>
    </Dialog>
  );
}
