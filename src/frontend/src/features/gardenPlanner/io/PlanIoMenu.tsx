/**
 * "Export / Import" of the garden plan page (REQ-053 GP-UX-050/051). The two dialogs are loaded
 * when first opened, so the route chunk keeps its budget (UI-NFR-003). The entries state why they are off:
 * import is the lead's (a replace deletes) and it waits for unsaved edits. Field mode has no such menu at all
 * (GP-UX-023): import and export stay in planning mode.
 *
 * Two ways in, one set of dialogs (`usePlanIo`): with the editor on screen the entries are part of the overflow
 * "⋮" of its header bar (§17.3, GP-UX-063); without it (an empty plan) the page header shows this menu button.
 */
import { lazy, Suspense, useId, useMemo, useState, type ReactNode } from 'react';
import { useTranslation } from 'react-i18next';
import Button from '@mui/material/Button';
import ListItemIcon from '@mui/material/ListItemIcon';
import ListItemText from '@mui/material/ListItemText';
import Menu from '@mui/material/Menu';
import MenuItem from '@mui/material/MenuItem';
import FileDownloadOutlinedIcon from '@mui/icons-material/FileDownloadOutlined';
import EventRepeatOutlinedIcon from '@mui/icons-material/EventRepeatOutlined';
import FileUploadOutlinedIcon from '@mui/icons-material/FileUploadOutlined';
import TableViewOutlinedIcon from '@mui/icons-material/TableViewOutlined';
import ImportExportIcon from '@mui/icons-material/ImportExport';
import type { MenuAction } from '../editor/ContextMenu';
import type { PlanSelection } from './types';

const ExportDialog = lazy(() => import('./ExportDialog'));
const ImportWizard = lazy(() => import('./ImportWizard'));
const NewSeasonDialog = lazy(() => import('../season/NewSeasonDialog'));

const PREFIX = 'pages.gardenPlan.io';

export interface PlanIoMenuProps {
  siteKey: string;
  siteName: string;
  /** Only a lead may import (`replace` deletes, SR-010). */
  canImport: boolean;
  /** Unsaved edits would be lost by a reload of the plan. */
  dirty: boolean;
  /** An import was written; reload the plan. */
  onImported: () => void;
  /** What is selected on the plan, so the backup can be limited to it (GP-FR-172). */
  selection?: PlanSelection;
  /** Bed names by key, so the new-season report can name the beds it lists (WP 7.17). */
  bedNames?: Record<string, string>;
  /** A CSV bed list was written (GP-FR-174): reload the plan and select the new beds. Falls back to `onImported`. */
  onBedsImported?: (locationKeys: string[]) => void;
}

type IoDialog = 'export' | 'import' | 'csv' | 'season';

export interface PlanIo {
  /** Why import, CSV and new season are off (lead only, unsaved edits), or `null`. */
  importOff: string | null;
  open: (which: IoDialog) => void;
  /** The overflow entries, with the test ids of the menu entries (GP-UX-070). */
  items: MenuAction[];
  /** The open dialog, loaded on first use; render it once. */
  dialogs: ReactNode;
}

/** The export/import dialogs and their entries, for the overflow of the editor header bar and for `PlanIoMenu`. */
export function usePlanIo({
  siteKey,
  siteName,
  canImport,
  dirty,
  onImported,
  selection,
  bedNames,
  onBedsImported,
}: PlanIoMenuProps): PlanIo {
  const { t } = useTranslation();
  const [dialog, setDialog] = useState<IoDialog | null>(null);

  let importOff: string | null = null;
  if (!canImport) importOff = t(`${PREFIX}.menu.leadOnly`);
  else if (dirty) importOff = t(`${PREFIX}.menu.unsaved`);

  const items = useMemo<MenuAction[]>(
    () => [
      {
        id: 'io-export',
        label: t(`${PREFIX}.menu.export`),
        icon: <FileDownloadOutlinedIcon fontSize="small" />,
        onClick: () => setDialog('export'),
        testId: 'garden-plan-io-export',
        separated: true,
      },
      {
        id: 'io-import',
        label: t(`${PREFIX}.menu.import`),
        icon: <FileUploadOutlinedIcon fontSize="small" />,
        onClick: () => setDialog('import'),
        disabled: importOff !== null,
        secondary: importOff,
        testId: 'garden-plan-io-import',
      },
      {
        id: 'io-csv',
        label: t(`${PREFIX}.menu.csv`),
        icon: <TableViewOutlinedIcon fontSize="small" />,
        onClick: () => setDialog('csv'),
        disabled: importOff !== null,
        secondary: !canImport ? t(`${PREFIX}.menu.csvLeadOnly`) : importOff,
        testId: 'garden-plan-io-csv',
      },
      {
        id: 'io-season',
        label: t(`${PREFIX}.menu.season`),
        icon: <EventRepeatOutlinedIcon fontSize="small" />,
        onClick: () => setDialog('season'),
        disabled: importOff !== null,
        secondary: !canImport ? t(`${PREFIX}.menu.seasonLeadOnly`) : importOff,
        testId: 'garden-plan-io-season',
      },
    ],
    [canImport, importOff, t],
  );

  const dialogs = (
    <Suspense fallback={null}>
      {dialog === 'export' && (
        <ExportDialog open siteKey={siteKey} selection={selection} onClose={() => setDialog(null)} />
      )}
      {(dialog === 'import' || dialog === 'csv') && (
        <ImportWizard
          open
          siteKey={siteKey}
          siteName={siteName}
          initialView={dialog === 'csv' ? 'csv' : 'import'}
          onClose={() => setDialog(null)}
          onImported={onImported}
          onBedsImported={onBedsImported}
        />
      )}
      {dialog === 'season' && (
        <NewSeasonDialog
          open
          siteKey={siteKey}
          bedNames={bedNames ?? {}}
          onClose={() => setDialog(null)}
          onApplied={onImported}
        />
      )}
    </Suspense>
  );

  return { importOff, open: setDialog, items, dialogs };
}

export function PlanIoMenu(props: PlanIoMenuProps) {
  const { canImport } = props;
  const { t } = useTranslation();
  const menuId = useId();
  const [anchor, setAnchor] = useState<HTMLElement | null>(null);
  const io = usePlanIo(props);
  const { importOff } = io;

  const open = (which: IoDialog) => {
    setAnchor(null);
    io.open(which);
  };

  return (
    <>
      <Button
        startIcon={<ImportExportIcon />}
        onClick={(event) => setAnchor(event.currentTarget)}
        aria-haspopup="menu"
        aria-controls={anchor !== null ? menuId : undefined}
        aria-expanded={anchor !== null}
        sx={{ minHeight: 44 }}
        data-testid="garden-plan-io-menu"
      >
        {t(`${PREFIX}.menu.open`)}
      </Button>
      <Menu
        id={menuId}
        open={anchor !== null}
        anchorEl={anchor}
        onClose={() => setAnchor(null)}
        slotProps={{ list: { 'aria-label': t(`${PREFIX}.menu.open`) } }}
      >
        <MenuItem
          onClick={() => open('export')}
          sx={{ minHeight: 48 }}
          data-testid="garden-plan-io-export"
        >
          <ListItemIcon>
            <FileDownloadOutlinedIcon />
          </ListItemIcon>
          <ListItemText primary={t(`${PREFIX}.menu.export`)} />
        </MenuItem>
        <MenuItem
          onClick={() => open('import')}
          disabled={importOff !== null}
          sx={{ minHeight: 48 }}
          data-testid="garden-plan-io-import"
        >
          <ListItemIcon>
            <FileUploadOutlinedIcon />
          </ListItemIcon>
          <ListItemText primary={t(`${PREFIX}.menu.import`)} secondary={importOff} />
        </MenuItem>
        <MenuItem
          onClick={() => open('csv')}
          disabled={importOff !== null}
          sx={{ minHeight: 48 }}
          data-testid="garden-plan-io-csv"
        >
          <ListItemIcon>
            <TableViewOutlinedIcon />
          </ListItemIcon>
          <ListItemText
            primary={t(`${PREFIX}.menu.csv`)}
            secondary={!canImport ? t(`${PREFIX}.menu.csvLeadOnly`) : importOff}
          />
        </MenuItem>
        <MenuItem
          onClick={() => open('season')}
          disabled={importOff !== null}
          sx={{ minHeight: 48 }}
          data-testid="garden-plan-io-season"
        >
          <ListItemIcon>
            <EventRepeatOutlinedIcon />
          </ListItemIcon>
          <ListItemText
            primary={t(`${PREFIX}.menu.season`)}
            secondary={!canImport ? t(`${PREFIX}.menu.seasonLeadOnly`) : importOff}
          />
        </MenuItem>
      </Menu>
      {io.dialogs}
    </>
  );
}
