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
  /**
   * Interactive row-level controls (favourite toggle, overflow menu), pinned to
   * the top-right and wrapped in a `card-actions` hook.
   *
   * This exists because `trailing` is a *visual* slot and is frequently already
   * spoken for. `SpeciesListPage` is the case that forced the decision (#778
   * A1): it renders a dedicated favourite column on the desktop table, and its
   * card put a `SpeciesThumbnail` in `trailing` — so below the `sm` breakpoint
   * the favourite toggle had nowhere to go and the action was simply
   * unreachable. Giving card-level actions their own slot means the answer is
   * no longer "whatever the page improvises".
   */
  actions?: ReactNode;
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
 *
 * A chip that carries a semantic palette colour (`color="error"`, …) also emits
 * that colour as `data-chip-color`. The colour is *product* information — it is
 * how the card says "this state is a problem" — and without a product-owned
 * carrier the only readable form is MUI's `MuiChip-color<Palette>` class, i.e.
 * a styling implementation detail that renames itself on a library upgrade.
 * A caller-supplied `data-chip-color` wins, and a chip left on the palette
 * default emits nothing (it asserts no colour semantics).
 */
/**
 * Read the semantic palette colour a keyed chip should advertise.
 *
 * Several list pages wrap their chip in a `Tooltip` to explain what the label
 * means. MUI forwards unrecognised props to the tooltip's child, so the
 * `data-testid` still lands on the chip — but the `color` prop does *not* live
 * on the wrapper, so reading it there yields nothing and the chip silently
 * stops advertising its colour. Falling through to a lone child element keeps
 * the wrapped and unwrapped forms equivalent, which is the only way a reader
 * can treat them the same.
 */
function paletteColorOf(element: ReactElement<Record<string, unknown>>): string | undefined {
  if (typeof element.props.color === 'string') return element.props.color;
  const child = element.props.children;
  if (isValidElement(child) && typeof child.type !== 'symbol') {
    const inner = (child as ReactElement<Record<string, unknown>>).props.color;
    if (typeof inner === 'string') return inner;
  }
  return undefined;
}

function renderKeyedChip(chip: MobileCardChip): ReactNode {
  const testId = `card-chip-${chip.id}`;
  if (isValidElement(chip.content) && typeof chip.content.type !== 'symbol') {
    const element = chip.content as ReactElement<Record<string, unknown>>;
    const props: Record<string, unknown> = { key: chip.id };
    if (element.props['data-testid'] === undefined) {
      props['data-testid'] = testId;
    }
    const paletteColor = paletteColorOf(element);
    if (element.props['data-chip-color'] === undefined && paletteColor !== undefined) {
      props['data-chip-color'] = paletteColor;
    }
    return cloneElement(element, props);
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
  actions,
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
          {actions && (
            <Box
              data-testid="card-actions"
              sx={{ flexShrink: 0, display: 'flex', alignItems: 'center', gap: 0.5 }}
            >
              {actions}
            </Box>
          )}
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
