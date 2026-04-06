import { useEffect, useState, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import Button from '@mui/material/Button';
import Box from '@mui/material/Box';
import Card from '@mui/material/Card';
import CardContent from '@mui/material/CardContent';
import Chip from '@mui/material/Chip';
import Collapse from '@mui/material/Collapse';
import IconButton from '@mui/material/IconButton';
import Typography from '@mui/material/Typography';
import Tooltip from '@mui/material/Tooltip';
import AddIcon from '@mui/icons-material/Add';
import ExpandMoreIcon from '@mui/icons-material/ExpandMore';
import PlaceIcon from '@mui/icons-material/Place';
import FolderIcon from '@mui/icons-material/Folder';
import ParkIcon from '@mui/icons-material/Park';
import HomeIcon from '@mui/icons-material/Home';
import MeetingRoomIcon from '@mui/icons-material/MeetingRoom';
import WarehouseIcon from '@mui/icons-material/Warehouse';
import CampaignIcon from '@mui/icons-material/Campaign';
import GrassIcon from '@mui/icons-material/Grass';
import BalconyIcon from '@mui/icons-material/Balcony';
import DeckIcon from '@mui/icons-material/Deck';
import Inventory2Icon from '@mui/icons-material/Inventory2';
import LandscapeIcon from '@mui/icons-material/Landscape';
import AccountTreeIcon from '@mui/icons-material/AccountTree';
import WaterDropIcon from '@mui/icons-material/WaterDrop';
import { SimpleTreeView } from '@mui/x-tree-view/SimpleTreeView';
import { TreeItem } from '@mui/x-tree-view/TreeItem';
import PageTitle from '@/components/layout/PageTitle';
import LoadingSkeleton from '@/components/common/LoadingSkeleton';
import EmptyState from '@/components/common/EmptyState';
import { useAppDispatch, useAppSelector } from '@/store/hooks';
import { fetchSites } from '@/store/slices/sitesSlice';
import { useApiError } from '@/hooks/useApiError';
import * as api from '@/api/endpoints/sites';
import type { Site, LocationTreeNode, LocationType } from '@/api/types';
import SiteCreateDialog from './SiteCreateDialog';
import LocationCreateDialog from './LocationCreateDialog';
import { kamiLocations } from '@/assets/brand/illustrations';

const ICON_MAP: Record<string, React.ReactElement> = {
  AccountTree: <AccountTreeIcon fontSize="small" />,
  Landscape: <LandscapeIcon fontSize="small" />,
  Park: <ParkIcon fontSize="small" />,
  Home: <HomeIcon fontSize="small" />,
  MeetingRoom: <MeetingRoomIcon fontSize="small" />,
  Warehouse: <WarehouseIcon fontSize="small" />,
  Campaign: <CampaignIcon fontSize="small" />,
  Grass: <GrassIcon fontSize="small" />,
  Balcony: <BalconyIcon fontSize="small" />,
  Deck: <DeckIcon fontSize="small" />,
  Inventory2: <Inventory2Icon fontSize="small" />,
  Shelves: <Inventory2Icon fontSize="small" />,
};

function getIcon(iconName: string | undefined): React.ReactElement {
  if (iconName && ICON_MAP[iconName]) return ICON_MAP[iconName];
  return <FolderIcon fontSize="small" />;
}

function countLocations(nodes: LocationTreeNode[]): number {
  let count = 0;
  for (const n of nodes) {
    count += 1 + countLocations(n.children);
  }
  return count;
}

interface SiteCardProps {
  site: Site;
  locationTypes: Record<string, LocationType>;
}

function SiteCard({ site, locationTypes }: SiteCardProps) {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const { handleError } = useApiError();
  const [expanded, setExpanded] = useState(false);
  const [tree, setTree] = useState<LocationTreeNode[] | null>(null);
  const [loadingTree, setLoadingTree] = useState(false);
  const [createOpen, setCreateOpen] = useState(false);
  const [createParentKey, setCreateParentKey] = useState<string | undefined>(undefined);
  const [createParentTypeKey, setCreateParentTypeKey] = useState<string | undefined>(undefined);

  const loadTree = useCallback(async () => {
    setLoadingTree(true);
    try {
      const data = await api.getLocationTree(site.key);
      setTree(data);
    } catch (err) {
      handleError(err);
    } finally {
      setLoadingTree(false);
    }
  }, [site.key, handleError]);

  useEffect(() => {
    if (expanded && tree === null) {
      loadTree();
    }
  }, [expanded, tree, loadTree]);

  const handleAddSublocation = (parentKey: string, typeKey?: string) => (e: React.MouseEvent) => {
    e.stopPropagation();
    setCreateParentKey(parentKey);
    setCreateParentTypeKey(typeKey);
    setCreateOpen(true);
  };

  const handleAddTopLevel = (e: React.MouseEvent) => {
    e.stopPropagation();
    setCreateParentKey(undefined);
    setCreateParentTypeKey(undefined);
    setCreateOpen(true);
  };

  const renderNode = (node: LocationTreeNode): React.ReactNode => {
    const ltInfo = locationTypes[node.location_type_key];
    const icon = getIcon(ltInfo?.icon ?? undefined);

    return (
      <TreeItem
        key={node.key}
        itemId={node.key}
        label={
          <Box
            sx={{
              display: 'flex',
              alignItems: 'center',
              gap: 0.5,
              py: 0.5,
              minHeight: 44,
              flexWrap: { xs: 'wrap', sm: 'nowrap' },
            }}
          >
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5, flexShrink: 0 }}>
              {icon}
              <Typography
                variant="body2"
                component="span"
                sx={{ cursor: 'pointer', '&:hover': { textDecoration: 'underline' } }}
                onClick={(e) => {
                  e.stopPropagation();
                  navigate(`/standorte/locations/${node.key}`);
                }}
              >
                {node.name}
              </Typography>
            </Box>
            <Box
              sx={{
                display: 'flex',
                alignItems: 'center',
                gap: 0.5,
                flexWrap: 'wrap',
                flex: 1,
                minWidth: 0,
              }}
            >
              {ltInfo && (
                <Chip
                  label={ltInfo.name}
                  size="small"
                  variant="outlined"
                  sx={{ fontSize: '0.7rem', height: 20, maxWidth: 'none' }}
                />
              )}
              {node.slot_count > 0 && (
                <Chip
                  label={`${node.slot_count} ${t('entities.slots')}`}
                  size="small"
                  variant="outlined"
                  sx={{ fontSize: '0.7rem', height: 20 }}
                />
              )}
              {node.active_plant_count > 0 && (
                <Chip
                  label={`${node.active_plant_count} ${t('entities.plantInstances')}`}
                  size="small"
                  color="success"
                  variant="outlined"
                  sx={{ fontSize: '0.7rem', height: 20 }}
                />
              )}
              {node.tank_name && (
                <Chip
                  label={node.tank_name}
                  size="small"
                  color="info"
                  variant="outlined"
                  icon={<WaterDropIcon sx={{ fontSize: '0.85rem !important' }} />}
                  sx={{ fontSize: '0.7rem', height: 20, maxWidth: 'none' }}
                />
              )}
            </Box>
            <Tooltip title={t('pages.locations.addSublocation')} placement="top">
              <IconButton
                size="small"
                onClick={handleAddSublocation(node.key, node.location_type_key)}
                aria-label={t('pages.locations.addSublocation')}
                data-testid={`add-sublocation-${node.key}`}
                sx={{ flexShrink: 0, minWidth: 32, minHeight: 32 }}
              >
                <AddIcon fontSize="small" />
              </IconButton>
            </Tooltip>
          </Box>
        }
      >
        {node.children.map(renderNode)}
      </TreeItem>
    );
  };

  const locationCount = tree ? countLocations(tree) : null;
  const expandLabel = expanded
    ? t('pages.sites.collapseSite')
    : t('pages.sites.expandSite');

  return (
    <Card variant="outlined" data-testid={`site-card-${site.key}`}>
      {/* Card header — manually built to allow keyboard-accessible expand control separate from site navigation */}
      <Box
        sx={{
          display: 'flex',
          alignItems: 'center',
          gap: 1,
          px: 2,
          py: 1.5,
          cursor: 'pointer',
          '&:hover': { bgcolor: 'action.hover' },
          '&:focus-visible': { outline: (theme) => `2px solid ${theme.palette.primary.main}`, outlineOffset: -2 },
        }}
        role="button"
        tabIndex={0}
        aria-expanded={expanded}
        aria-controls={`site-tree-${site.key}`}
        onClick={() => setExpanded((prev) => !prev)}
        onKeyDown={(e) => {
          if (e.key === 'Enter' || e.key === ' ') {
            e.preventDefault();
            setExpanded((prev) => !prev);
          }
        }}
      >
        <PlaceIcon color="primary" aria-hidden="true" />
        <Box sx={{ flex: 1, minWidth: 0 }}>
          <Box
            sx={{
              display: 'flex',
              alignItems: 'center',
              gap: 1,
              flexWrap: 'wrap',
            }}
          >
            <Typography
              variant="subtitle1"
              component="span"
              data-testid={`site-name-${site.key}`}
              sx={{ fontWeight: 600, cursor: 'pointer', '&:hover': { textDecoration: 'underline' } }}
              onClick={(e) => {
                e.stopPropagation();
                navigate(`/standorte/sites/${site.key}`);
              }}
            >
              {site.name}
            </Typography>
            {site.climate_zone && (
              <Chip label={site.climate_zone} size="small" variant="outlined" />
            )}
            {site.total_area_m2 ? (
              <Chip label={`${site.total_area_m2}\u00A0m\u00B2`} size="small" variant="outlined" />
            ) : null}
            {locationCount != null && locationCount > 0 && (
              <Chip
                label={`${locationCount} ${t('pages.locations.title')}`}
                size="small"
                color="primary"
                variant="outlined"
              />
            )}
          </Box>
          {site.timezone && (
            <Typography variant="caption" color="text.secondary">
              {site.timezone}
            </Typography>
          )}
        </Box>
        <Tooltip title={expandLabel}>
          <Box
            component="span"
            aria-label={expandLabel}
            sx={{ display: 'flex', alignItems: 'center', flexShrink: 0 }}
          >
            <ExpandMoreIcon
              aria-hidden="true"
              sx={{
                transform: expanded ? 'rotate(180deg)' : 'rotate(0deg)',
                transition: 'transform 0.2s',
                color: 'action.active',
              }}
            />
          </Box>
        </Tooltip>
      </Box>

      <Collapse in={expanded} id={`site-tree-${site.key}`}>
        <CardContent sx={{ pt: 0, pb: 2, px: 2 }}>
          {loadingTree ? (
            <LoadingSkeleton rows={3} />
          ) : tree && tree.length > 0 ? (
            <>
              <Box
                sx={{
                  display: 'flex',
                  justifyContent: 'space-between',
                  alignItems: 'center',
                  mb: 1,
                  mt: 1,
                  flexWrap: 'wrap',
                  gap: 1,
                }}
              >
                <Box>
                  <Typography variant="subtitle2" color="text.secondary">
                    {t('pages.locations.title')}
                  </Typography>
                  <Typography variant="caption" color="text.secondary">
                    {t('pages.locations.sectionIntro')}
                  </Typography>
                </Box>
                <Button
                  size="small"
                  startIcon={<AddIcon />}
                  onClick={handleAddTopLevel}
                  data-testid={`add-location-${site.key}`}
                >
                  {t('pages.locations.create')}
                </Button>
              </Box>
              <SimpleTreeView defaultExpandedItems={tree.map((n) => n.key)}>
                {tree.map(renderNode)}
              </SimpleTreeView>
            </>
          ) : (
            <Box sx={{ mt: 1 }}>
              <EmptyState
                message={t('pages.locations.noSublocations')}
                actionLabel={t('pages.locations.create')}
                onAction={() => {
                  setCreateParentKey(undefined);
                  setCreateParentTypeKey(undefined);
                  setCreateOpen(true);
                }}
              />
            </Box>
          )}
        </CardContent>
      </Collapse>

      <LocationCreateDialog
        siteKey={site.key}
        parentLocationKey={createParentKey}
        parentLocationTypeKey={createParentTypeKey}
        open={createOpen}
        onClose={() => setCreateOpen(false)}
        onCreated={() => {
          setCreateOpen(false);
          loadTree();
        }}
      />
    </Card>
  );
}

export default function SiteListPage() {
  const { t } = useTranslation();
  const dispatch = useAppDispatch();
  const { sites, loading } = useAppSelector((s) => s.sites);
  const [createOpen, setCreateOpen] = useState(false);
  const [locationTypes, setLocationTypes] = useState<Record<string, LocationType>>({});

  useEffect(() => {
    dispatch(fetchSites({}));
    api
      .listLocationTypes()
      .then((types) => {
        const map: Record<string, LocationType> = {};
        for (const lt of types) map[lt.key] = lt;
        setLocationTypes(map);
      })
      .catch(() => {});
  }, [dispatch]);

  return (
    <Box data-testid="site-list-page">
      <PageTitle
        title={t('pages.sites.title')}
        action={
          <Button
            variant="contained"
            startIcon={<AddIcon />}
            onClick={() => setCreateOpen(true)}
            data-testid="create-button"
          >
            {t('pages.sites.create')}
          </Button>
        }
      />

      {!loading && sites.length > 0 && (
        <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
          {t('pages.sites.intro')}
        </Typography>
      )}

      {loading ? (
        <LoadingSkeleton rows={5} />
      ) : sites.length === 0 ? (
        <EmptyState
          message={t('pages.sites.noSites')}
          actionLabel={t('pages.sites.create')}
          onAction={() => setCreateOpen(true)}
          illustration={kamiLocations}
        />
      ) : (
        <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
          {sites.map((site) => (
            <SiteCard key={site.key} site={site} locationTypes={locationTypes} />
          ))}
        </Box>
      )}

      <SiteCreateDialog
        open={createOpen}
        onClose={() => setCreateOpen(false)}
        onCreated={() => {
          setCreateOpen(false);
          dispatch(fetchSites({}));
        }}
      />
    </Box>
  );
}
