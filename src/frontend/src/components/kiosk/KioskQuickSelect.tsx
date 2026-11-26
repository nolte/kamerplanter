import { useTranslation } from 'react-i18next';
import Box from '@mui/material/Box';
import Button from '@mui/material/Button';
import KeyboardIcon from '@mui/icons-material/Keyboard';
import type { QuickSelectPreset } from '@/kiosk/quickSelectPresets';
import { formatNumber } from '@/utils/formatting';

interface KioskQuickSelectProps {
  preset: QuickSelectPreset;
  value: number | null | undefined;
  /** Label of the field the tiles fill — names the group for assistive technology. */
  fieldLabel: string;
  onSelect: (value: number) => void;
  /** "Manuell" — hands over to the free number entry beside the tiles (R-026). */
  onManual: () => void;
  testIdPrefix: string;
}

/**
 * UI-NFR-019 R-024..R-026 — quick-select tiles for a frequently logged measurement. One tap
 * stores a predefined value instead of typing it with gloves on; the tile of the current value is
 * pressed (`aria-pressed`). Tiles are ≥ 48 px with 12 px between them (R-025; the kiosk theme
 * raises every button to its 64 px touch target anyway), and the "Manuell" tile moves the focus
 * into the regular number field, which stays visible for any other value (R-026).
 */
export default function KioskQuickSelect({
  preset,
  value,
  fieldLabel,
  onSelect,
  onManual,
  testIdPrefix,
}: KioskQuickSelectProps) {
  const { t } = useTranslation();
  const digits = { minimumFractionDigits: preset.fractionDigits, maximumFractionDigits: preset.fractionDigits };

  return (
    <Box
      role="group"
      aria-label={t('pages.kiosk.quickSelect.groupLabel', { field: fieldLabel })}
      sx={{ display: 'flex', flexWrap: 'wrap', gap: 1.5, mb: 2 }}
      data-testid={`${testIdPrefix}-quick-select`}
    >
      {preset.values.map((presetValue) => {
        const selected = value === presetValue;
        return (
          <Button
            key={presetValue}
            variant={selected ? 'contained' : 'outlined'}
            aria-pressed={selected}
            onClick={() => onSelect(presetValue)}
            sx={{ minWidth: 72, minHeight: 48, fontSize: '1.125rem', fontWeight: 700 }}
            data-testid={`${testIdPrefix}-quick-${presetValue}`}
          >
            {formatNumber(presetValue, digits)}
          </Button>
        );
      })}
      <Button
        variant="outlined"
        startIcon={<KeyboardIcon />}
        onClick={onManual}
        sx={{ minHeight: 48 }}
        data-testid={`${testIdPrefix}-quick-manual`}
      >
        {t('pages.kiosk.quickSelect.manual')}
      </Button>
    </Box>
  );
}
