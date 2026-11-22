/**
 * The one editor header bar of the planning mode (REQ-053 §17.3, GP-UX-063, AC-1/AC-3/AC-15): back to the site,
 * the save group (`SaveBar`: undo/redo, status, auto-save, "Save"), the tabs Plan · Liste · Beete, the switch to
 * field mode, the panel switch and the overflow "⋮" (`EditorHeaderActions`). It is exactly one line on every width:
 * what does not fit moves into the overflow in the order of GP-UX-063 - (1) auto-save, (2) field mode, (3) the panel
 * switch, (4) the tabs, as three entries with the active one marked. Once nothing is left to move, the site name of
 * the back link gives way (ellipsis; the full name stays in its accessible name and tooltip), and if even that is not
 * enough (5) the save status becomes compact, as below md. Below md the bar holds only back (an icon with its
 * `aria-label`), the compact save status, "Save" and "⋮"; undo and redo stand in the `TouchBar` then. "Save" is the
 * only primary action and never moves (UI-NFR-021 R-017). So the bar fits at md beside the app navigation (#2879).
 *
 * The same items render inline or as menu entries from one description, so desktop, tablet and phone come from one
 * component tree (GP-UX-069). Inline controls keep their test ids (GP-UX-070); their entries in the overflow carry
 * `garden-plan-menu-<id>`. A focused control that moves into the overflow gives the focus to "⋮" (GP-NFR-070).
 */
import { useEffect, useMemo, useRef, type ReactNode, type Ref } from 'react';
import { Link as RouterLink } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import Box from '@mui/material/Box';
import Button from '@mui/material/Button';
import IconButton from '@mui/material/IconButton';
import Paper from '@mui/material/Paper';
import Tab from '@mui/material/Tab';
import Tabs from '@mui/material/Tabs';
import Tooltip from '@mui/material/Tooltip';
import { useForkRef } from '@mui/material/utils';
import ArrowBackIcon from '@mui/icons-material/ArrowBack';
import AutorenewIcon from '@mui/icons-material/Autorenew';
import TouchAppIcon from '@mui/icons-material/TouchApp';
import type { MenuAction } from './ContextMenu';
import { EditorHeaderActions } from './EditorHeaderActions';
import { SaveBar } from './SaveBar';
import type { AutoSave } from './useAutoSave';
import { useHeaderFocusRescue, useHeaderOverflow } from './useHeaderOverflow';

const PREFIX = 'pages.gardenPlan';
const TARGET_PX = 48;

/**
 * The move order of GP-UX-063: a control is in the overflow once the bar's level reaches its step. From the tabs'
 * step on the back link's site name may shrink; the last step makes the save status compact. Below md the level is
 * `HEADER_LEVEL_ALL`.
 */
export const HEADER_STEP = { autoSave: 1, fieldMode: 2, panel: 3, tabs: 4, compactStatus: 5 } as const;
export const HEADER_LEVEL_ALL = 5;

/** One tab of the plan route (`?tab=`, GP-UX-064). */
export interface HeaderTab {
  value: string;
  label: string;
  icon: ReactNode;
  /** The id of the tab element; also its test id. */
  id: string;
  /** The id of the tab panel it shows. */
  controls: string;
}

export interface HeaderTabs {
  value: string;
  items: readonly HeaderTab[];
  /** The accessible name of the tab list. */
  label: string;
  onChange: (value: string) => void;
}

/** What only the route knows: where "back" and field mode lead, and the export/import entries. */
export interface HeaderNav {
  backHref: string;
  siteName: string;
  /** Field mode (GP-UX-020); absent where the route offers none. */
  fieldHref?: string;
  onFieldMode?: () => void;
  /** Export and import (GP-UX-050/051), entries of the overflow. */
  ioItems?: readonly MenuAction[];
}

/** The switch of the side panel (GP-UX-068, WP 10.5): `aria-expanded` and `aria-controls` on the panel. */
export interface HeaderPanelToggle {
  label: string;
  /** The text of its overflow entry (GP-UX-063 step 3: "Seitenpanel ein-/ausblenden"); defaults to `label`. */
  menuLabel?: string;
  icon: ReactNode;
  expanded: boolean;
  controls: string;
  onToggle: () => void;
  testId: string;
}

/** The tabs Plan · Liste · Beete (WAI-ARIA "Tabs"): in the header bar, or above a plan the editor cannot show. */
export function PlanViewTabs({ tabs }: { tabs: HeaderTabs }) {
  return (
    <Tabs
      value={tabs.value}
      onChange={(_event, next: string) => tabs.onChange(next)}
      aria-label={tabs.label}
      variant="standard"
      data-testid="garden-plan-tabs"
      // The scroller of standard tabs is `width: 100%`, which a row that sizes to its content resolves to the whole
      // free width: the tabs take only what their labels need.
      sx={{ minHeight: TARGET_PX, flex: '0 0 auto', '& .MuiTabs-scroller': { flex: '0 0 auto', width: 'auto' } }}
    >
      {tabs.items.map((item) => (
        <Tab
          key={item.value}
          value={item.value}
          label={item.label}
          id={item.id}
          aria-controls={item.controls}
          data-testid={item.id}
          sx={{ minHeight: TARGET_PX, minWidth: 0, px: 2 }}
        />
      ))}
    </Tabs>
  );
}

interface EditorHeaderBarProps {
  autoSave: AutoSave;
  /** Below md: everything but back, the save status, "Save" and "⋮" is in the overflow (GP-UX-063). */
  narrow: boolean;
  /** Undo and redo in the bar; below md they are in the `TouchBar` while it is on screen. */
  undoRedo: boolean;
  nav?: HeaderNav;
  tabs?: HeaderTabs;
  panelToggle?: HeaderPanelToggle;
  /** The inline panel switch, so a panel that closes can give the focus back to it. */
  panelButtonRef?: Ref<HTMLButtonElement>;
  /** The rare actions of the overflow (keyboard help, underlay, select all, …), after the moved controls. */
  overflowItems: readonly MenuAction[];
  overflowButtonRef?: Ref<HTMLButtonElement>;
  /** Told whether the tabs are in the bar (`true`) or in the overflow, so a tab panel names itself right. */
  onTabsInline?: (inline: boolean) => void;
}

export function EditorHeaderBar({
  autoSave,
  narrow,
  undoRedo,
  nav,
  tabs,
  panelToggle,
  panelButtonRef,
  overflowItems,
  overflowButtonRef,
  onTabsInline,
}: EditorHeaderBarProps) {
  const { t } = useTranslation();
  const barRef = useRef<HTMLDivElement | null>(null);
  const level = useHeaderOverflow(barRef, narrow ? HEADER_LEVEL_ALL : 0, HEADER_LEVEL_ALL);
  // A focused control that moves into the overflow hands the focus to "⋮" (GP-NFR-070).
  const ownOverflowRef = useRef<HTMLButtonElement | null>(null);
  const overflowRef = useForkRef(ownOverflowRef, overflowButtonRef);
  const focusRescue = useHeaderFocusRescue(barRef, ownOverflowRef);
  const inline = {
    autoSave: level < HEADER_STEP.autoSave,
    fieldMode: level < HEADER_STEP.fieldMode,
    panel: level < HEADER_STEP.panel,
    tabs: level < HEADER_STEP.tabs,
  };
  // Nothing is left to move: the site name gives way before anything else does (#2879).
  const nameShrinks = level >= HEADER_STEP.tabs;
  const compactStatus = narrow || level >= HEADER_STEP.compactStatus;
  const tabsInline = tabs !== undefined && inline.tabs;
  useEffect(() => {
    if (tabs) onTabsInline?.(tabsInline);
  }, [onTabsInline, tabs, tabsInline]);

  const fieldLabel = t(`${PREFIX}.field.toField`);
  const autoSaveLabel = t(`${PREFIX}.editor.save.autoSave.label`);
  const fieldHref = nav?.fieldHref;
  const onFieldMode = nav?.onFieldMode;
  const ioItems = nav?.ioItems;

  // The overflow: the controls moved out, in the bar's order, then the rare actions (GP-UX-063, UI-NFR-021 R-019).
  const menu = useMemo<MenuAction[]>(() => {
    const moved: MenuAction[] = [];
    if (!inline.autoSave) {
      moved.push({
        id: 'autosave',
        label: autoSaveLabel,
        icon: <AutorenewIcon fontSize="small" />,
        kind: 'checkbox',
        checked: autoSave.enabled,
        onClick: () => autoSave.setEnabled(!autoSave.enabled),
      });
    }
    if (tabs && !inline.tabs) {
      for (const item of tabs.items) {
        moved.push({
          id: `tab-${item.value}`,
          label: item.label,
          icon: item.icon,
          kind: 'radio',
          checked: item.value === tabs.value,
          onClick: () => tabs.onChange(item.value),
        });
      }
    }
    if (onFieldMode && !inline.fieldMode) {
      moved.push({
        id: 'field-mode',
        label: fieldLabel,
        icon: <TouchAppIcon fontSize="small" />,
        onClick: onFieldMode,
      });
    }
    if (panelToggle && !inline.panel) {
      moved.push({
        id: 'panel',
        label: panelToggle.menuLabel ?? panelToggle.label,
        icon: panelToggle.icon,
        kind: 'checkbox',
        checked: panelToggle.expanded,
        onClick: panelToggle.onToggle,
      });
    }
    const rest = [...overflowItems, ...(ioItems ?? [])];
    // The first rare action is set off from the moved controls.
    return moved.length > 0 && rest.length > 0
      ? [...moved, { ...rest[0], separated: true }, ...rest.slice(1)]
      : [...moved, ...rest];
  }, [
    inline.autoSave,
    inline.tabs,
    inline.fieldMode,
    inline.panel,
    autoSave,
    autoSaveLabel,
    tabs,
    onFieldMode,
    fieldLabel,
    panelToggle,
    overflowItems,
    ioItems,
  ]);

  const backLabel = nav ? t(`${PREFIX}.header.backTo`, { name: nav.siteName }) : '';

  return (
    <Paper
      ref={barRef}
      variant="outlined"
      role="group"
      aria-label={t(`${PREFIX}.header.label`)}
      data-testid="garden-plan-header-bar"
      data-overflow-level={level}
      onFocus={focusRescue.onFocus}
      onBlur={focusRescue.onBlur}
      sx={{
        display: 'flex',
        alignItems: 'center',
        flexWrap: 'nowrap',
        gap: 0.5,
        p: 0.5,
        minWidth: 0,
        // Nothing in the bar shrinks below its content: a line too long is measured and moved, not squeezed. Only the
        // back link's site name gives way, once nothing is left to move.
        '& > *': { flexShrink: 0 },
      }}
    >
      {nav &&
        (narrow ? (
          <Tooltip title={backLabel}>
            <IconButton
              component={RouterLink}
              to={nav.backHref}
              aria-label={backLabel}
              data-testid="garden-plan-back-link"
              sx={{ width: TARGET_PX, height: TARGET_PX }}
            >
              <ArrowBackIcon />
            </IconButton>
          </Tooltip>
        ) : (
          <Tooltip title={backLabel}>
            <Button
              component={RouterLink}
              to={nav.backHref}
              startIcon={<ArrowBackIcon />}
              aria-label={backLabel}
              data-testid="garden-plan-back-link"
              sx={{
                minHeight: TARGET_PX,
                maxWidth: 240,
                // Shrinks down to the arrow, a 48 px target; before that the bar moves its controls out.
                minWidth: TARGET_PX,
                ...(nameShrinks && { '&&': { flexShrink: 1 } }),
              }}
            >
              <Box
                component="span"
                data-testid="garden-plan-back-link-name"
                sx={{ minWidth: 0, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}
              >
                {nav.siteName}
              </Box>
            </Button>
          </Tooltip>
        ))}
      <SaveBar autoSave={autoSave} compact={compactStatus} showUndoRedo={undoRedo} showAutoSave={inline.autoSave} />
      {tabs && inline.tabs && <PlanViewTabs tabs={tabs} />}
      <Box sx={{ flex: '1 1 0', minWidth: 0, '&&': { flexShrink: 1 } }} />
      {fieldHref && inline.fieldMode && (
        <Button
          component={RouterLink}
          to={fieldHref}
          variant="outlined"
          startIcon={<TouchAppIcon />}
          data-testid="garden-plan-mode-field"
          sx={{ minHeight: TARGET_PX, whiteSpace: 'nowrap' }}
        >
          {fieldLabel}
        </Button>
      )}
      {panelToggle && inline.panel && (
        <Button
          ref={panelButtonRef}
          startIcon={panelToggle.icon}
          onClick={panelToggle.onToggle}
          aria-expanded={panelToggle.expanded}
          aria-controls={panelToggle.controls}
          data-testid={panelToggle.testId}
          sx={{ minHeight: TARGET_PX, whiteSpace: 'nowrap' }}
        >
          {panelToggle.label}
        </Button>
      )}
      <EditorHeaderActions actions={menu} buttonRef={overflowRef} />
    </Paper>
  );
}
