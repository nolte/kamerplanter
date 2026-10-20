/**
 * The zone panel (REQ-053 GP-FR-110, GP-FR-112..119; WP 7.6 + 7.7): the list of the site's irrigation zones, the
 * editor (create, change, assign beds, delete for the lead), the status of a zone and the watering round. This
 * module is its own `lazy()` chunk: the route chunk only carries the switch that mounts it (UI-NFR-003).
 */
import { useState } from 'react';
import { useTranslation } from 'react-i18next';
import Alert from '@mui/material/Alert';
import Box from '@mui/material/Box';
import Button from '@mui/material/Button';
import IconButton from '@mui/material/IconButton';
import Paper from '@mui/material/Paper';
import Typography from '@mui/material/Typography';
import AddIcon from '@mui/icons-material/Add';
import CloseIcon from '@mui/icons-material/Close';
import WaterDropIcon from '@mui/icons-material/WaterDrop';
import { useTenantPermissions } from '@/hooks/useTenantPermissions';
import type { PlanModel } from '../model/planModel';
import { WateringRoundDialog } from './WateringRoundDialog';
import { ZoneEditor } from './ZoneEditor';
import { ZoneStatusView } from './ZoneStatusView';
import type { UseIrrigationZones } from './useZoneData';

const PREFIX = 'pages.gardenPlan.editor.zones';

export interface ZonePanelProps {
  plan: PlanModel;
  zoneData: UseIrrigationZones;
  selectedBedKeys: readonly string[];
  /** A write happened: the editor reads the zones and the last-watered layer again. */
  onChanged: () => void;
  onClose: () => void;
}

type Mode = { kind: 'list' } | { kind: 'new' } | { kind: 'edit'; key: string };

export default function ZonePanel({ plan, zoneData, selectedBedKeys, onChanged, onClose }: ZonePanelProps) {
  const { t } = useTranslation();
  const { canEdit, canDelete, canConfigureIntegrations } = useTenantPermissions();
  const [mode, setMode] = useState<Mode>({ kind: 'list' });
  const [roundOpen, setRoundOpen] = useState(false);
  const [statusToken, setStatusToken] = useState(0);
  const { zones, records, status, reload } = zoneData;
  const selected = mode.kind === 'edit' ? (zones.find((zone) => zone.key === mode.key) ?? null) : null;
  // The full record (with the Home Assistant flag) once the endpoint answered; the plan's list before.
  const record = selected ? (records.find((zone) => zone.key === selected.key) ?? selected) : null;

  const changed = (key: string | null) => {
    reload();
    onChanged();
    setMode(key === null ? { kind: 'list' } : { kind: 'edit', key });
  };

  return (
    <Paper
      component="section"
      variant="outlined"
      aria-labelledby="garden-plan-zones-title"
      data-testid="garden-plan-zone-panel"
      sx={{ p: 2, display: 'grid', gap: 2 }}
    >
      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
        <Typography variant="h6" component="h3" id="garden-plan-zones-title" sx={{ flex: 1 }}>
          {t(`${PREFIX}.panel.title`)}
        </Typography>
        <IconButton
          onClick={onClose}
          aria-label={t(`${PREFIX}.panel.close`)}
          data-testid="garden-plan-zone-panel-close"
          sx={{ minWidth: 44, minHeight: 44 }}
        >
          <CloseIcon />
        </IconButton>
      </Box>

      {status === 'error' && (
        <Alert
          severity="warning"
          action={
            <Button color="inherit" size="small" onClick={reload} sx={{ minHeight: 44 }}>
              {t(`${PREFIX}.panel.retry`)}
            </Button>
          }
          data-testid="garden-plan-zone-load-failed"
        >
          {t(`${PREFIX}.panel.loadFailed`)}
        </Alert>
      )}
      {!canEdit && (
        <Typography variant="body2" color="text.secondary" data-testid="garden-plan-zone-readonly">
          {t(`${PREFIX}.panel.readOnly`)}
        </Typography>
      )}

      {mode.kind === 'list' && (
        <>
          {zones.length === 0 ? (
            <Typography variant="body2" color="text.secondary" data-testid="garden-plan-zone-empty">
              {t(`${PREFIX}.panel.empty`)}
            </Typography>
          ) : (
            <Box component="ul" aria-label={t(`${PREFIX}.panel.listLabel`)} sx={{ listStyle: 'none', m: 0, p: 0, display: 'grid', gap: 0.5 }}>
              {zones.map((zone) => (
                <Box component="li" key={zone.key}>
                  <Button
                    onClick={() => setMode({ kind: 'edit', key: zone.key })}
                    data-testid={`garden-plan-zone-row-${zone.key}`}
                    sx={{ minHeight: 48, width: '100%', justifyContent: 'flex-start', textTransform: 'none', gap: 1 }}
                  >
                    <Box
                      aria-hidden="true"
                      sx={{ width: 16, height: 16, border: 3, borderColor: zone.color, borderRadius: 0.5, flexShrink: 0 }}
                    />
                    <span>{zone.name}</span>
                    <Typography component="span" variant="body2" color="text.secondary">
                      {t(`${PREFIX}.panel.bedCount`, { count: zone.location_keys.length })}
                    </Typography>
                  </Button>
                </Box>
              ))}
            </Box>
          )}
          {canEdit && (
            <Button
              variant="outlined"
              startIcon={<AddIcon />}
              onClick={() => setMode({ kind: 'new' })}
              sx={{ minHeight: 44, justifySelf: 'start' }}
              data-testid="garden-plan-zone-new"
            >
              {t(`${PREFIX}.panel.new`)}
            </Button>
          )}
        </>
      )}

      {mode.kind === 'new' && canEdit && (
        <ZoneEditor
          key="new"
          zone={null}
          siteKey={plan.siteKey}
          plan={plan}
          zones={zones}
          selectedBedKeys={selectedBedKeys}
          canDelete={canDelete}
          technical={canConfigureIntegrations}
          onChanged={changed}
          onCancel={() => setMode({ kind: 'list' })}
        />
      )}

      {mode.kind === 'edit' && selected && record && (
        <>
          {canEdit ? (
            <ZoneEditor
              key={selected.key}
              zone={record}
              siteKey={plan.siteKey}
              plan={plan}
              zones={zones}
              selectedBedKeys={selectedBedKeys}
              canDelete={canDelete}
              technical={canConfigureIntegrations}
              onChanged={changed}
              onCancel={() => setMode({ kind: 'list' })}
            />
          ) : (
            <Button onClick={() => setMode({ kind: 'list' })} sx={{ minHeight: 44, justifySelf: 'start' }}>
              {t(`${PREFIX}.form.cancel`)}
            </Button>
          )}
          <ZoneStatusView zone={record} plan={plan} refreshToken={statusToken} technical={canConfigureIntegrations} />
          {canEdit && (
            <Button
              variant="contained"
              startIcon={<WaterDropIcon />}
              onClick={() => setRoundOpen(true)}
              sx={{ minHeight: 44, justifySelf: 'start' }}
              data-testid="garden-plan-zone-round-open"
            >
              {t(`${PREFIX}.round.open`)}
            </Button>
          )}
          {roundOpen && (
            <WateringRoundDialog
              open
              zone={selected}
              plan={plan}
              onClose={() => setRoundOpen(false)}
              onLogged={() => {
                setStatusToken((value) => value + 1);
                onChanged();
              }}
            />
          )}
        </>
      )}
      {mode.kind === 'edit' && !selected && (
        <Button onClick={() => setMode({ kind: 'list' })} sx={{ minHeight: 44, justifySelf: 'start' }}>
          {t(`${PREFIX}.form.cancel`)}
        </Button>
      )}
    </Paper>
  );
}
