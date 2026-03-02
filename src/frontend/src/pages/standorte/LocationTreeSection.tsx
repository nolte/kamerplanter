import { useEffect, useState, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import Box from '@mui/material/Box';
import Typography from '@mui/material/Typography';
import Button from '@mui/material/Button';
import IconButton from '@mui/material/IconButton';
import Chip from '@mui/material/Chip';
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
import { SimpleTreeView } from '@mui/x-tree-view/SimpleTreeView';
import { TreeItem } from '@mui/x-tree-view/TreeItem';
import LocationCreateDialog from './LocationCreateDialog';
import { useApiError } from '@/hooks/useApiError';
import * as api from '@/api/endpoints/sites';
import type { LocationTreeNode } from '@/api/types';

const ICON_MAP: Record<string, React.ReactElement> = {
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

  useEffect(() => { load(); }, [load]);

  const handleAddSublocation = (parentKey: string) => (e: React.MouseEvent) => {
    e.stopPropagation();
    setCreateParentKey(parentKey);
    setCreateOpen(true);
  };

  const handleAddTopLevel = () => {
    setCreateParentKey(undefined);
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
              gap: 1,
              py: 0.5,
              minHeight: 36,
            }}
          >
            {icon}
            <Typography
              variant="body2"
              sx={{ cursor: 'pointer', '&:hover': { textDecoration: 'underline' } }}
              onClick={(e) => {
                e.stopPropagation();
                navigate(`/standorte/locations/${node.key}`);
              }}
            >
              {node.name}
            </Typography>
            {node.slot_count > 0 && (
              <Chip label={`${node.slot_count} ${t('entities.slots')}`} size="small" variant="outlined" />
            )}
            <IconButton
              size="small"
              onClick={handleAddSublocation(node.key)}
              title={t('pages.locations.addSublocation')}
            >
              <AddIcon fontSize="small" />
            </IconButton>
          </Box>
        }
      >
        {node.children.map(renderNode)}
      </TreeItem>
    );
  };

  return (
    <Box sx={{ mt: 4 }}>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
        <Typography variant="h6">{t('pages.locations.title')}</Typography>
        <Button startIcon={<AddIcon />} onClick={handleAddTopLevel}>
          {t('pages.locations.create')}
        </Button>
      </Box>

      {loading ? (
        <Typography variant="body2" color="text.secondary">{t('common.loading')}</Typography>
      ) : tree.length === 0 ? (
        <Typography variant="body2" color="text.secondary">{t('pages.locations.noSublocations')}</Typography>
      ) : (
        <SimpleTreeView defaultExpandedItems={tree.map((n) => n.key)}>
          {tree.map(renderNode)}
        </SimpleTreeView>
      )}

      <LocationCreateDialog
        siteKey={siteKey}
        parentLocationKey={createParentKey}
        open={createOpen}
        onClose={() => setCreateOpen(false)}
        onCreated={() => { setCreateOpen(false); load(); }}
      />
    </Box>
  );
}
