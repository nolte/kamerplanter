/**
 * "Export / Import" in the header of the garden plan page (REQ-053 GP-UX-050/051). The two dialogs are loaded
 * when first opened, so the route chunk keeps its budget (UI-NFR-003). The entries state why they are off:
 * import is the lead's (a replace deletes) and it waits for unsaved edits. Field mode has no such menu at all
 * (GP-UX-023): import and export stay in planning mode.
 */
import { lazy, Suspense, useId, useState } from 'react';
import { useTranslation } from 'react-i18next';
import Button from '@mui/material/Button';
import ListItemIcon from '@mui/material/ListItemIcon';
import ListItemText from '@mui/material/ListItemText';
import Menu from '@mui/material/Menu';
import MenuItem from '@mui/material/MenuItem';
import FileDownloadOutlinedIcon from '@mui/icons-material/FileDownloadOutlined';
import FileUploadOutlinedIcon from '@mui/icons-material/FileUploadOutlined';
import ImportExportIcon from '@mui/icons-material/ImportExport';
import type { PlanSelection } from './types';

const ExportDialog = lazy(() => import('./ExportDialog'));
const ImportWizard = lazy(() => import('./ImportWizard'));

const PREFIX = 'pages.gardenPlan.io';

interface PlanIoMenuProps {
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
}

export function PlanIoMenu({ siteKey, siteName, canImport, dirty, onImported, selection }: PlanIoMenuProps) {
  const { t } = useTranslation();
  const menuId = useId();
  const [anchor, setAnchor] = useState<HTMLElement | null>(null);
  const [dialog, setDialog] = useState<'export' | 'import' | null>(null);

  let importOff: string | null = null;
  if (!canImport) importOff = t(`${PREFIX}.menu.leadOnly`);
  else if (dirty) importOff = t(`${PREFIX}.menu.unsaved`);

  const open = (which: 'export' | 'import') => {
    setAnchor(null);
    setDialog(which);
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
      </Menu>
      <Suspense fallback={null}>
        {dialog === 'export' && (
          <ExportDialog open siteKey={siteKey} selection={selection} onClose={() => setDialog(null)} />
        )}
        {dialog === 'import' && (
          <ImportWizard
            open
            siteKey={siteKey}
            siteName={siteName}
            onClose={() => setDialog(null)}
            onImported={onImported}
          />
        )}
      </Suspense>
    </>
  );
}
