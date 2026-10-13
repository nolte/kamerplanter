import { useCallback, useEffect, useMemo, useState } from 'react';
import { useTranslation } from 'react-i18next';
import Card from '@mui/material/Card';
import CardContent from '@mui/material/CardContent';
import Typography from '@mui/material/Typography';
import Alert from '@mui/material/Alert';
import Box from '@mui/material/Box';
import Stack from '@mui/material/Stack';
import TextField from '@mui/material/TextField';
import Button from '@mui/material/Button';
import Chip from '@mui/material/Chip';
import List from '@mui/material/List';
import ListItem from '@mui/material/ListItem';
import ListItemText from '@mui/material/ListItemText';
import Switch from '@mui/material/Switch';
import FormControlLabel from '@mui/material/FormControlLabel';
import InputAdornment from '@mui/material/InputAdornment';
import SearchIcon from '@mui/icons-material/Search';
import AddIcon from '@mui/icons-material/Add';
import { useSnackbar } from 'notistack';
import LoadingSkeleton from '@/components/common/LoadingSkeleton';
import { parseApiError } from '@/api/errors';
import {
  HA_ENTITY_ID_PATTERN,
  getHaEntityInventory,
  grantHaEntities,
  revokeHaEntityGrant,
  type HaEntityInventory,
  type HaEntityInventoryItem,
} from '@/api/endpoints/adminHaEntityGrants';

/** How many entities the list renders at once — the inventory of a real instance runs into the thousands. */
const MAX_VISIBLE = 100;

interface Props {
  tenantKey: string;
  tenantName: string;
}

function toTestIdSuffix(entityId: string): string {
  return entityId.replace(/[^a-z0-9]+/g, '-');
}

/**
 * MT-015 (#2112) — the platform admin releases Home Assistant entities for one tenant.
 *
 * Kamerplanter talks to one Home Assistant instance, the operator's. A garden can
 * bind, read and switch only the entities released here; withdrawing a grant
 * stops the readings and the switching of every sensor or actuator that names it.
 */
export default function HaEntityGrantsCard({ tenantKey, tenantName }: Props) {
  const { t } = useTranslation();
  const { enqueueSnackbar } = useSnackbar();
  const [inventory, setInventory] = useState<HaEntityInventory | null>(null);
  const [loading, setLoading] = useState(true);
  const [loadFailed, setLoadFailed] = useState(false);
  const [search, setSearch] = useState('');
  const [onlyGranted, setOnlyGranted] = useState(false);
  const [busy, setBusy] = useState<string | null>(null);
  const [manualId, setManualId] = useState('');

  const [reloadToken, setReloadToken] = useState(0);

  useEffect(() => {
    let cancelled = false;
    getHaEntityInventory(tenantKey)
      .then((loaded) => {
        if (!cancelled) setInventory(loaded);
      })
      .catch(() => {
        if (!cancelled) setLoadFailed(true);
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, [tenantKey, reloadToken]);

  const retry = () => {
    setLoading(true);
    setLoadFailed(false);
    setReloadToken((n) => n + 1);
  };

  const grantedCount = useMemo(
    () => (inventory ? inventory.entities.filter((e) => e.granted).length : 0),
    [inventory],
  );

  const filtered = useMemo(() => {
    if (!inventory) return [];
    const needle = search.trim().toLowerCase();
    return inventory.entities.filter(
      (e) =>
        (!onlyGranted || e.granted) &&
        (!needle ||
          e.entity_id.includes(needle) ||
          (e.friendly_name ?? '').toLowerCase().includes(needle)),
    );
  }, [inventory, search, onlyGranted]);

  const setGranted = useCallback(
    (entityId: string, granted: boolean) => {
      setInventory((prev) =>
        prev
          ? {
              ...prev,
              entities: prev.entities.some((e) => e.entity_id === entityId)
                ? prev.entities.map((e) => (e.entity_id === entityId ? { ...e, granted } : e))
                : [
                    ...prev.entities,
                    {
                      entity_id: entityId,
                      domain: entityId.split('.')[0],
                      friendly_name: null,
                      unit_of_measurement: null,
                      device_class: null,
                      granted,
                      present: false,
                    },
                  ].sort((a, b) => a.entity_id.localeCompare(b.entity_id)),
            }
          : prev,
      );
    },
    [],
  );

  const toggle = async (item: HaEntityInventoryItem) => {
    setBusy(item.entity_id);
    try {
      if (item.granted) {
        await revokeHaEntityGrant(tenantKey, item.entity_id);
        setGranted(item.entity_id, false);
        enqueueSnackbar(t('pages.admin.haGrants.revoked', { entity: item.entity_id }), { variant: 'success' });
      } else {
        await grantHaEntities(tenantKey, [item.entity_id]);
        setGranted(item.entity_id, true);
        enqueueSnackbar(t('pages.admin.haGrants.granted', { entity: item.entity_id }), { variant: 'success' });
      }
    } catch (err) {
      enqueueSnackbar(parseApiError(err), { variant: 'error' });
    } finally {
      setBusy(null);
    }
  };

  const manualValid = HA_ENTITY_ID_PATTERN.test(manualId.trim());

  const grantManual = async () => {
    const entityId = manualId.trim();
    if (!HA_ENTITY_ID_PATTERN.test(entityId)) return;
    setBusy(entityId);
    try {
      await grantHaEntities(tenantKey, [entityId]);
      setGranted(entityId, true);
      setManualId('');
      enqueueSnackbar(t('pages.admin.haGrants.granted', { entity: entityId }), { variant: 'success' });
    } catch (err) {
      enqueueSnackbar(parseApiError(err), { variant: 'error' });
    } finally {
      setBusy(null);
    }
  };

  return (
    <Card data-testid="ha-entity-grants-card">
      <CardContent>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, flexWrap: 'wrap', mb: 1 }}>
          <Typography variant="h6" component="h2">
            {t('pages.admin.haGrants.title')}
          </Typography>
          {inventory && <Chip label={t('pages.admin.haGrants.grantedCount', { count: grantedCount })} size="small" />}
        </Box>
        <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
          {t('pages.admin.haGrants.intro', { tenant: tenantName })}
        </Typography>

        {loading && <LoadingSkeleton variant="table" />}

        {!loading && loadFailed && (
          <Alert
            severity="error"
            action={
              <Button color="inherit" size="small" onClick={retry} data-testid="ha-entity-grants-retry">
                {t('common.retry')}
              </Button>
            }
            data-testid="ha-entity-grants-load-error"
          >
            {t('pages.admin.haGrants.loadError')}
          </Alert>
        )}

        {!loading && inventory && (
          <Stack spacing={2}>
            {!inventory.ha_configured && (
              <Alert severity="info" data-testid="ha-entity-grants-not-configured">
                {t('pages.admin.haGrants.notConfigured')}
              </Alert>
            )}

            <Stack direction={{ xs: 'column', sm: 'row' }} spacing={1} sx={{ alignItems: { sm: 'center' } }}>
              <TextField
                size="small"
                fullWidth
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                label={t('pages.admin.haGrants.search')}
                slotProps={{
                  input: {
                    startAdornment: (
                      <InputAdornment position="start">
                        <SearchIcon fontSize="small" />
                      </InputAdornment>
                    ),
                  },
                }}
                data-testid="ha-entity-grants-search"
              />
              <FormControlLabel
                sx={{ flexShrink: 0, ml: { sm: 1 } }}
                control={
                  <Switch
                    checked={onlyGranted}
                    onChange={(e) => setOnlyGranted(e.target.checked)}
                    data-testid="ha-entity-grants-only-granted"
                  />
                }
                label={t('pages.admin.haGrants.onlyGranted')}
              />
            </Stack>

            {filtered.length === 0 ? (
              <Typography variant="body2" color="text.secondary" data-testid="ha-entity-grants-empty">
                {inventory.entities.length === 0
                  ? t('pages.admin.haGrants.emptyInventory')
                  : t('pages.admin.haGrants.noMatch')}
              </Typography>
            ) : (
              <List dense disablePadding data-testid="ha-entity-grants-list">
                {filtered.slice(0, MAX_VISIBLE).map((item) => (
                  <ListItem
                    key={item.entity_id}
                    divider
                    disableGutters
                    data-testid={`ha-entity-grant-row-${toTestIdSuffix(item.entity_id)}`}
                    secondaryAction={
                      <Switch
                        edge="end"
                        checked={item.granted}
                        disabled={busy !== null}
                        onChange={() => toggle(item)}
                        slotProps={{
                          input: {
                            'aria-label': t('pages.admin.haGrants.toggleAria', { entity: item.entity_id }),
                          },
                        }}
                        data-testid={`ha-entity-grant-toggle-${toTestIdSuffix(item.entity_id)}`}
                      />
                    }
                    sx={{ pr: 7, minHeight: 48 }}
                  >
                    <ListItemText
                      primary={item.friendly_name || item.entity_id}
                      secondary={
                        <Box component="span" sx={{ display: 'flex', gap: 1, flexWrap: 'wrap', alignItems: 'center' }}>
                          <Box component="span" sx={{ fontFamily: 'monospace', wordBreak: 'break-all' }}>
                            {item.entity_id}
                          </Box>
                          {!item.present && (
                            <Chip
                              component="span"
                              size="small"
                              variant="outlined"
                              label={t('pages.admin.haGrants.notPresent')}
                            />
                          )}
                        </Box>
                      }
                    />
                  </ListItem>
                ))}
              </List>
            )}
            {filtered.length > MAX_VISIBLE && (
              <Typography variant="caption" color="text.secondary" data-testid="ha-entity-grants-truncated">
                {t('pages.admin.haGrants.truncated', { shown: MAX_VISIBLE, total: filtered.length })}
              </Typography>
            )}

            <Stack direction={{ xs: 'column', sm: 'row' }} spacing={1} sx={{ alignItems: { sm: 'flex-start' } }}>
              <TextField
                size="small"
                fullWidth
                value={manualId}
                onChange={(e) => setManualId(e.target.value)}
                label={t('pages.admin.haGrants.manualLabel')}
                helperText={
                  manualId && !manualValid
                    ? t('pages.admin.haGrants.manualInvalid')
                    : t('pages.admin.haGrants.manualHelper')
                }
                error={!!manualId && !manualValid}
                data-testid="ha-entity-grants-manual-input"
              />
              <Button
                variant="outlined"
                startIcon={<AddIcon />}
                onClick={grantManual}
                disabled={!manualValid || busy !== null}
                sx={{ flexShrink: 0, minHeight: 40 }}
                data-testid="ha-entity-grants-manual-submit"
              >
                {t('pages.admin.haGrants.manualSubmit')}
              </Button>
            </Stack>
          </Stack>
        )}
      </CardContent>
    </Card>
  );
}
