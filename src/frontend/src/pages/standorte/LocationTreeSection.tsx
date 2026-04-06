import { useEffect, useState, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import Box from '@mui/material/Box';
import Typography from '@mui/material/Typography';
import Button from '@mui/material/Button';
import IconButton from '@mui/material/IconButton';
import Chip from '@mui/material/Chip';
import Tooltip from '@mui/material/Tooltip';
import AddIcon from '@mui/icons-material/Add';
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
import LocationCreateDialog from './LocationCreateDialog';
import LoadingSkeleton from '@/components/common/LoadingSkeleton';
import EmptyState from '@/components/common/EmptyState';
import { useApiError } from '@/hooks/useApiError';
import * as api from '@/api/endpoints/sites';
import type { LocationTreeNode } from '@/api/types';

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

interface Props {
  siteKey: string;
  locationTypeIcons?: Record<string, string>;
}

export default function LocationTreeSection({ siteKey }: Props) {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const { handleError } = useApiError();
  const [tree, setTree] = useState<LocationTreeNode[]>([]);
  const [locationTypes, setLocationTypes] = useState<Record<string, { name: string; icon: string | null }>>({});
  const [loading, setLoading] = useState(false);
  const [createOpen, setCreateOpen] = useState(false);
  const [createParentKey, setCreateParentKey] = useState<string | undefined>(undefined);
  const [createParentTypeKey, setCreateParentTypeKey] = useState<string | undefined>(undefined);

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const [treeData, ltData] = await Promise.all([
        api.getLocationTree(siteKey),
        api.listLocationTypes(),
      ]);
      setTree(treeData);
      const ltMap: Record<string, { name: string; icon: string | null }> = {};
      for (const lt of ltData) {
        ltMap[lt.key] = { name: lt.name, icon: lt.icon };
      }
      setLocationTypes(ltMap);
    } catch (err) {
      handleError(err);
    } finally {
      setLoading(false);
    }
  }, [siteKey, handleError]);

  useEffect(() => {
    load();
  }, [load]);

  const handleAddSublocation = (parentKey: string, typeKey?: string) => (e: React.MouseEvent) => {
    e.stopPropagation();
    setCreateParentKey(parentKey);
    setCreateParentTypeKey(typeKey);
    setCreateOpen(true);
  };

  const handleAddTopLevel = () => {
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

  return (
    <Box sx={{ mt: 4 }}>
      <Box
        sx={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: { xs: 'flex-start', sm: 'center' },
          flexWrap: 'wrap',
          gap: 1,
          mb: 1,
        }}
      >
        <Box>
          <Typography variant="h6">{t('pages.locations.title')}</Typography>
          <Typography variant="body2" color="text.secondary">
            {t('pages.locations.sectionIntro')}
          </Typography>
        </Box>
        <Button
          startIcon={<AddIcon />}
          onClick={handleAddTopLevel}
          data-testid="add-location-button"
        >
          {t('pages.locations.create')}
        </Button>
      </Box>

      {loading ? (
        <LoadingSkeleton rows={3} />
      ) : tree.length === 0 ? (
        <EmptyState
          message={t('pages.locations.noSublocations')}
          actionLabel={t('pages.locations.create')}
          onAction={handleAddTopLevel}
        />
      ) : (
        <SimpleTreeView defaultExpandedItems={tree.map((n) => n.key)}>
          {tree.map(renderNode)}
        </SimpleTreeView>
      )}

      <LocationCreateDialog
        siteKey={siteKey}
        parentLocationKey={createParentKey}
        parentLocationTypeKey={createParentTypeKey}
        open={createOpen}
        onClose={() => setCreateOpen(false)}
        onCreated={() => {
          setCreateOpen(false);
          load();
        }}
      />
    </Box>
  );
}
