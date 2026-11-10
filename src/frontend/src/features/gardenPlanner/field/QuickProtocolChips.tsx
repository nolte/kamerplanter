/**
 * The six quick-protocol chips of the bed sheet (REQ-053 GP-UX-029, GP-FR-090): Gegossen · Geerntet ·
 * Gesät · Gejätet/Gemulcht · Gepflanzt · Notiz. Each one is a 64 px touch target with its icon and its
 * name; the sheet decides what a tap does (one tap = one `care_event`, or the short form / shortcut).
 */
import { Fragment, type ReactNode } from 'react';
import { useTranslation } from 'react-i18next';
import Box from '@mui/material/Box';
import Button from '@mui/material/Button';
import Typography from '@mui/material/Typography';
import { KIOSK_TOUCH_TARGET } from '@/kiosk/kioskTheme';
import { chipIcon, FIELD_ICON_PX } from './fieldIcons';
import { QUICK_CHIPS, type QuickChip, type QuickChipId } from './quickChips';

interface QuickProtocolChipsProps {
  /** A write is running or the device is offline without the buffer: every chip waits. */
  disabled: boolean;
  /**
   * Offline with the write buffer (WP 9.4): only these chips work — the note is buffered, the others need the
   * server (a one-tap log, a harvest, planting). `undefined` = all chips.
   */
  onlyChips?: ReadonlySet<QuickChipId>;
  /** "Planted" needs a drawn bed (the planting dialog lays the plants out on its geometry). */
  plantingAvailable: boolean;
  onChip: (chip: QuickChip) => void;
}

/** A label with a line-break opportunity after each "/" (`<wbr>` adds no text: the label reads as it is written). */
function breakAfterSlash(label: string): ReactNode {
  const parts = label.split('/');
  return parts.map((part, index) => (
    <Fragment key={index}>
      {part}
      {index < parts.length - 1 && (
        <>
          /<wbr />
        </>
      )}
    </Fragment>
  ));
}

export default function QuickProtocolChips({ disabled, onlyChips, plantingAvailable, onChip }: QuickProtocolChipsProps) {
  const { t } = useTranslation();
  return (
    <Box component="section" aria-labelledby="field-quick-heading" data-testid="field-quick-protocol">
      <Typography id="field-quick-heading" variant="h6" component="h3" sx={{ mb: 1 }}>
        {t('pages.gardenPlan.field.quick.title')}
      </Typography>
      <Box
        sx={{
          display: 'grid',
          gridTemplateColumns: { xs: 'repeat(2, minmax(0, 1fr))', sm: 'repeat(3, minmax(0, 1fr))' },
          gap: 1,
        }}
      >
        {QUICK_CHIPS.map((chip) => {
          const Icon = chipIcon(chip.id);
          const unavailable =
            (chip.action === 'planting' && !plantingAvailable) || (onlyChips !== undefined && !onlyChips.has(chip.id));
          return (
            <Button
              key={chip.id}
              variant="outlined"
              color="inherit"
              onClick={() => onChip(chip)}
              disabled={disabled || unavailable}
              startIcon={<Icon sx={{ fontSize: FIELD_ICON_PX }} aria-hidden="true" />}
              sx={{
                minHeight: KIOSK_TOUCH_TARGET,
                justifyContent: 'flex-start',
                fontSize: '1rem',
                borderWidth: 2,
                textTransform: 'none',
                // At 390 px a label like "Gejätet/Gemulcht" must wrap inside its frame, not run out of it (#2764).
                minWidth: 0,
                textAlign: 'left',
                lineHeight: 1.25,
                '& .MuiButton-startIcon > *:nth-of-type(1)': { fontSize: FIELD_ICON_PX },
              }}
              data-testid={`field-chip-${chip.id}`}
            >
              <span>{breakAfterSlash(t(`pages.gardenPlan.field.quick.chips.${chip.id}`))}</span>
            </Button>
          );
        })}
      </Box>
      {onlyChips !== undefined && (
        <Typography variant="body2" sx={{ mt: 1 }} data-testid="field-chips-offline-hint">
          {t('pages.gardenPlan.field.buffer.chipsOffline')}
        </Typography>
      )}
      {!plantingAvailable && (
        <Typography variant="body2" sx={{ mt: 1 }} data-testid="field-chip-planted-hint">
          {t('pages.gardenPlan.field.quick.plantedNeedsGeometry')}
        </Typography>
      )}
    </Box>
  );
}
