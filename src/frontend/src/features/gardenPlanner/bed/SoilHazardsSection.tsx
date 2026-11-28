/**
 * "Bodengefahren" in the soil tab of a bed (REQ-054 §5.2, AP-API-012, #2888 F-20): each confirmed soil hazard with
 * its pathogen, the plants it endangers (from the knowledge table, each with its evidence status), the day it was
 * confirmed and how. A grower records one, only the lead removes one - the server is the gate, this section only
 * hides what the role cannot do. A vessel (planter, tent, shelf) and a hydroponic location carry none: no add button,
 * a sentence saying why. An area that is no bed (garden, zone, greenhouse on grown soil) takes juglone only, and its
 * entry also counts for the beds in it (REQ-053 §11.3a Nr. 5 v1.60); the server's `soil_hazard_scope` says which.
 *
 * Shown as data, judged nowhere: which hosts warn and for how long is the planting dialog's (F-21) and depends on
 * open operator decisions, so no host is marked "gesperrt" here and no duration is printed.
 */
import { lazy, Suspense, useState } from 'react';
import { useTranslation } from 'react-i18next';
import Alert from '@mui/material/Alert';
import Box from '@mui/material/Box';
import Button from '@mui/material/Button';
import Chip from '@mui/material/Chip';
import IconButton from '@mui/material/IconButton';
import Paper from '@mui/material/Paper';
import Stack from '@mui/material/Stack';
import Tooltip from '@mui/material/Tooltip';
import Typography from '@mui/material/Typography';
import AddIcon from '@mui/icons-material/Add';
import DeleteOutlinedIcon from '@mui/icons-material/DeleteOutlined';
import ConfirmDialog from '@/components/common/ConfirmDialog';
import type { SoilHazard } from '@/api/types';
import { useApiError } from '@/hooks/useApiError';
import { useNotification } from '@/hooks/useNotification';
import { formatDate } from '@/utils/formatting';
import { removeSoilHazard } from './soilHazardApi';
import {
  recordableSoilHazards,
  soilHazardsUnavailable,
  type BedSoilHazard,
  type SoilHazardHost,
  type SoilHazardScope,
} from './soilHazardTypes';

// The form loads when "Bodengefahr eintragen" is pressed.
const SoilHazardDialog = lazy(() => import('./SoilHazardDialog'));

const PREFIX = 'pages.bed.soilHazards';

interface SoilHazardsSectionProps {
  bedKey: string;
  bedName: string;
  /** `soil_hazard_scope` of the summary; absent (an older cached summary) offers nothing to add. */
  scope?: SoilHazardScope;
  hazards: BedSoilHazard[];
  /** Grower and above, online and not reading a cached summary. */
  canEdit: boolean;
  /** The lead role (removing is lead only). */
  canDelete: boolean;
  /** A hazard was recorded or removed; the page reloads its summary. */
  onChanged: () => void | Promise<void>;
}

function HostChip({ host }: { host: SoilHazardHost }) {
  const { t } = useTranslation();
  const evidenced = host.evidence_status === 'evidenced';
  const status = t(`${PREFIX}.evidence.${host.evidence_status}`);
  const level = t(`${PREFIX}.level.${host.level}`);
  return (
    <Chip
      size="small"
      variant={evidenced ? 'filled' : 'outlined'}
      label={`${host.name} · ${status}`}
      // The level is read out, not only the name: "Brassicaceae, Familie, belegt".
      aria-label={`${host.name}, ${level}, ${status}`}
      sx={{ fontStyle: host.level === 'family' ? 'normal' : 'italic', maxWidth: '100%' }}
    />
  );
}

export default function SoilHazardsSection({
  bedKey,
  bedName,
  scope,
  hazards,
  canEdit,
  canDelete,
  onChanged,
}: SoilHazardsSectionProps) {
  const { t } = useTranslation();
  const { handleError } = useApiError();
  const notification = useNotification();
  const [adding, setAdding] = useState(false);
  const [removing, setRemoving] = useState<SoilHazard | null>(null);
  const [busy, setBusy] = useState(false);
  const unavailable = scope ? soilHazardsUnavailable(scope) : null;
  const allowed = scope ? recordableSoilHazards(scope) : [];
  const mayAdd = canEdit && allowed.length > 0;
  const mayRemove = canEdit && canDelete;

  const confirmRemove = async () => {
    if (removing === null || busy) return;
    setBusy(true);
    try {
      await removeSoilHazard(bedKey, removing);
      notification.success(t(`${PREFIX}.removed`, { hazard: t(`enums.soilHazard.${removing}`) }));
      setRemoving(null);
      await onChanged();
    } catch (error) {
      handleError(error);
    } finally {
      setBusy(false);
    }
  };

  return (
    <Box
      component="section"
      aria-labelledby="soil-hazards-title"
      data-testid="soil-hazards-section"
      sx={{ display: 'flex', flexDirection: 'column', gap: 1.5, mt: 3 }}
    >
      <Typography id="soil-hazards-title" variant="h6" component="h2">
        {t(`${PREFIX}.title`)}
      </Typography>
      <Typography variant="body2" color="text.secondary">
        {t(scope === 'juglone_only' ? `${PREFIX}.introArea` : `${PREFIX}.intro`)}
      </Typography>

      {unavailable !== null && (
        <Alert severity="info" data-testid={`soil-hazards-unavailable-${unavailable}`}>
          {t(`${PREFIX}.unavailable.${unavailable}`)}
        </Alert>
      )}

      {hazards.length === 0 ? (
        <Typography variant="body2" data-testid="soil-hazards-empty">
          {t(scope === 'juglone_only' ? `${PREFIX}.emptyArea` : `${PREFIX}.empty`)}
        </Typography>
      ) : (
        <Stack component="ul" spacing={1.5} sx={{ listStyle: 'none', p: 0, m: 0 }}>
          {hazards.map((entry) => {
            const name = t(`enums.soilHazard.${entry.hazard}`);
            return (
              <Paper
                key={entry.hazard}
                component="li"
                variant="outlined"
                data-testid={`soil-hazard-row-${entry.hazard}`}
                sx={{ p: 2, display: 'flex', flexDirection: 'column', gap: 1 }}
              >
                <Box sx={{ display: 'flex', alignItems: 'flex-start', gap: 1 }}>
                  <Box sx={{ flex: 1, minWidth: 0 }}>
                    <Typography variant="subtitle1" component="h3">
                      {name}
                    </Typography>
                    <Typography variant="body2" color="text.secondary" sx={{ fontStyle: 'italic' }}>
                      {entry.pathogens.join(', ')}
                    </Typography>
                  </Box>
                  {mayRemove && (
                    <Tooltip title={t(`${PREFIX}.remove`, { hazard: name })}>
                      <IconButton
                        onClick={() => setRemoving(entry.hazard)}
                        aria-label={t(`${PREFIX}.remove`, { hazard: name })}
                        data-testid={`soil-hazard-remove-${entry.hazard}`}
                        sx={{ width: 48, height: 48 }}
                      >
                        <DeleteOutlinedIcon />
                      </IconButton>
                    </Tooltip>
                  )}
                </Box>
                <Typography variant="body2" data-testid={`soil-hazard-confirmed-${entry.hazard}`}>
                  {t(`${PREFIX}.confirmed`, {
                    date: formatDate(entry.confirmed_at),
                    source: t(`enums.pathogenConfirmationSource.${entry.source}`),
                  })}
                </Typography>
                <Typography variant="body2" component="h4" sx={{ fontWeight: 500 }}>
                  {t(`${PREFIX}.hosts`)}
                </Typography>
                <Box
                  component="ul"
                  sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.75, listStyle: 'none', p: 0, m: 0 }}
                  data-testid={`soil-hazard-hosts-${entry.hazard}`}
                >
                  {entry.hosts.map((host) => (
                    <li key={`${host.level}:${host.name}`}>
                      <HostChip host={host} />
                    </li>
                  ))}
                </Box>
                {entry.non_hosts.length > 0 && (
                  <>
                    {/* Shown with their evidence like the hosts: a non-host under 3/3 is no all-clear (review D1). */}
                    <Typography variant="body2" component="h4" sx={{ fontWeight: 500 }}>
                      {t(`${PREFIX}.nonHosts`)}
                    </Typography>
                    <Box
                      component="ul"
                      sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.75, listStyle: 'none', p: 0, m: 0 }}
                      data-testid={`soil-hazard-non-hosts-${entry.hazard}`}
                    >
                      {entry.non_hosts.map((host) => (
                        <li key={`${host.level}:${host.name}`}>
                          <HostChip host={host} />
                        </li>
                      ))}
                    </Box>
                  </>
                )}
                {entry.soft && (
                  <Typography variant="body2" color="text.secondary">
                    {t(`${PREFIX}.soft`)}
                  </Typography>
                )}
              </Paper>
            );
          })}
        </Stack>
      )}

      {hazards.some((entry) =>
        [...entry.hosts, ...entry.non_hosts].some((host) => host.evidence_status !== 'evidenced'),
      ) && (
        <Typography variant="caption" color="text.secondary">
          {t(`${PREFIX}.evidenceNote`)}
        </Typography>
      )}

      {mayAdd && (
        <Box>
          <Button
            variant="outlined"
            startIcon={<AddIcon />}
            onClick={() => setAdding(true)}
            sx={{ minHeight: 48 }}
            data-testid="soil-hazards-add"
          >
            {t(`${PREFIX}.add`)}
          </Button>
        </Box>
      )}

      {adding && (
        <Suspense fallback={null}>
          <SoilHazardDialog
            bedKey={bedKey}
            bedName={bedName}
            hazards={allowed}
            onClose={() => setAdding(false)}
            onSaved={() => {
              setAdding(false);
              void onChanged();
            }}
          />
        </Suspense>
      )}

      <ConfirmDialog
        open={removing !== null}
        title={t(`${PREFIX}.removeTitle`)}
        message={t(`${PREFIX}.removeMessage`, {
          hazard: removing ? t(`enums.soilHazard.${removing}`) : '',
          bed: bedName,
        })}
        confirmLabel={t(`${PREFIX}.removeConfirm`)}
        onConfirm={() => void confirmRemove()}
        onCancel={() => setRemoving(null)}
        destructive
        loading={busy}
        requiresConnectivity
      />
    </Box>
  );
}
