import { type ReactElement, type ReactNode, cloneElement, isValidElement } from 'react';
import Box from '@mui/material/Box';
import Card from '@mui/material/Card';
import CardContent from '@mui/material/CardContent';
import Typography from '@mui/material/Typography';

/**
 * A single label/value pair rendered in the card's field grid.
 *
 * `id` is the id of the `DataTable` column this field mirrors. When it is set
 * the value carries the stable test hook `card-field-<id>` (UI-NFR-022 R-016),
 * so a test can address "the phase field of this card" instead of counting
 * captions or reading a `<td>` that does not exist in the card layout.
 */
export interface MobileCardField {
  /** Column id this field mirrors; emits `card-field-<id>` on the value. */
  id?: string;
  label: string;
  value: ReactNode;
}

/**
 * A chip rendered in the card's chip row, keyed by the column it mirrors.
 *
 * Passing `chips` as a `MobileCardChip[]` (instead of a plain node) makes every
 * chip addressable as `card-chip-<id>`; without it the chips are only
 * distinguishable by DOM order, which silently reads the wrong chip as soon as
 * one of them is conditional.
 */
export interface MobileCardChip {
  /** Column id this chip mirrors; emits `card-chip-<id>` on the chip. */
  id: string;
  /** The chip element (or any node) to render. */
  content: ReactNode;
}

interface MobileCardProps {
  title: ReactNode;
  subtitle?: ReactNode;
  /**
   * Column id the title mirrors. The title keeps its unconditional
   * `card-title` hook and *additionally* exposes `card-field-<titleId>`, so the
   * value a card renders as its headline stays addressable by the very column
   * id that addresses it on the desktop table (`cell-<id>`) — without moving it
   * into the field grid and changing the card's visual structure.
   */
  titleId?: string;
  /**
   * Column id the subtitle mirrors; emits `card-field-<subtitleId>` in addition
   * to `card-subtitle`. Only present when a subtitle is rendered at all — a
   * caller that must stay readable for an empty value belongs in `fields`.
   */
  subtitleId?: string;
  fields?: MobileCardField[];
  trailing?: ReactNode;
  /**
   * Either a plain node (legacy: chips are only addressable by DOM order) or a
   * keyed list, which additionally emits a `card-chip-<id>` per entry.
   */
  chips?: ReactNode | MobileCardChip[];
  /** Optional leading visual (e.g. a thumbnail/cover preview) shown on the left. */
  leading?: ReactNode;
}

/** Narrow the `chips` prop to the keyed list form. */
function isKeyedChipList(chips: ReactNode | MobileCardChip[]): chips is MobileCardChip[] {
  return (
    Array.isArray(chips) &&
    chips.every(
      (chip) =>
        chip !== null &&
        typeof chip === 'object' &&
        'id' in chip &&
        'content' in chip,
    )
  );
}

/**
 * Render a keyed chip with its test hook attached.
 *
 * The hook is cloned onto the chip element itself so the rendered DOM stays
 * byte-for-byte what the caller wrote. A caller-provided `data-testid` wins —
 * those are an existing contract and must not be overwritten. Non-element
 * content (a string, a fragment) gets an inline-flex span carrier instead.
 */
function renderKeyedChip(chip: MobileCardChip): ReactNode {
  const testId = `card-chip-${chip.id}`;
  if (isValidElement(chip.content) && typeof chip.content.type !== 'symbol') {
    const element = chip.content as ReactElement<Record<string, unknown>>;
    if (element.props['data-testid'] !== undefined) {
      return cloneElement(element, { key: chip.id });
    }
    return cloneElement(element, { key: chip.id, 'data-testid': testId });
  }
  return (
    <Box key={chip.id} component="span" data-testid={testId} sx={{ display: 'inline-flex' }}>
      {chip.content}
    </Box>
  );
}

/**
 * Wrap a title/subtitle value in an inline `card-field-<id>` carrier.
 *
 * A `<span>` inside the existing `Typography` keeps the rendered layout
 * byte-for-byte (phrasing content, no box of its own) while giving the value
 * the same column-keyed hook a field would carry.
 */
function withColumnHook(value: ReactNode, id: string | undefined): ReactNode {
  if (!id) return value;
  return (
    <Box component="span" data-testid={`card-field-${id}`}>
      {value}
    </Box>
  );
}

export default function MobileCard({
  title,
  subtitle,
  titleId,
  subtitleId,
  fields,
  trailing,
  chips,
  leading,
}: MobileCardProps) {
  const keyedChips = isKeyedChipList(chips) ? chips : null;
  const hasChips = keyedChips ? keyedChips.length > 0 : Boolean(chips);

  return (
    <Card variant="outlined" sx={{ '&:hover': { borderColor: 'primary.main' } }}>
      <CardContent sx={{ py: 1.5, px: 2, '&:last-child': { pb: 1.5 } }}>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', gap: 1 }}>
          {leading && <Box sx={{ flexShrink: 0 }}>{leading}</Box>}
          <Box sx={{ minWidth: 0, flex: 1 }}>
            <Typography variant="subtitle2" noWrap data-testid="card-title">
              {withColumnHook(title, titleId)}
            </Typography>
            {subtitle && (
              <Typography
                variant="caption"
                color="text.secondary"
                noWrap
                sx={{ display: 'block' }}
                data-testid="card-subtitle"
              >
                {withColumnHook(subtitle, subtitleId)}
              </Typography>
            )}
          </Box>
          {trailing && <Box sx={{ flexShrink: 0 }}>{trailing}</Box>}
        </Box>
        {hasChips && (
          <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5, mt: 0.75 }}>
            {keyedChips ? keyedChips.map(renderKeyedChip) : (chips as ReactNode)}
          </Box>
        )}
        {fields && fields.length > 0 && (
          <Box
            sx={{
              display: 'grid',
              gridTemplateColumns: 'auto 1fr',
              gap: '2px 8px',
              mt: 0.75,
            }}
          >
            {fields.map((f) => (
              <Box key={f.id ?? f.label} sx={{ display: 'contents' }}>
                <Typography variant="caption" color="text.secondary">{f.label}</Typography>
                <Typography
                  variant="caption"
                  data-testid={f.id ? `card-field-${f.id}` : undefined}
                >
                  {f.value}
                </Typography>
              </Box>
            ))}
          </Box>
        )}
      </CardContent>
    </Card>
  );
}
