import { useTranslation } from 'react-i18next';
import Box from '@mui/material/Box';
import TextField from '@mui/material/TextField';
import FormControl from '@mui/material/FormControl';
import InputLabel from '@mui/material/InputLabel';
import Select from '@mui/material/Select';
import MenuItem from '@mui/material/MenuItem';
import Switch from '@mui/material/Switch';
import FormControlLabel from '@mui/material/FormControlLabel';
import Divider from '@mui/material/Divider';
import Typography from '@mui/material/Typography';
import InputAdornment from '@mui/material/InputAdornment';
import Card from '@mui/material/Card';
import CardActionArea from '@mui/material/CardActionArea';
import CardContent from '@mui/material/CardContent';
import Chip from '@mui/material/Chip';
import Skeleton from '@mui/material/Skeleton';
import CheckCircleIcon from '@mui/icons-material/CheckCircle';
import AddCircleOutlineIcon from '@mui/icons-material/AddCircleOutlined';
import PlaceIcon from '@mui/icons-material/Place';
import AutoAwesomeIcon from '@mui/icons-material/AutoAwesome';
import type { ExperienceLevel, Site, SiteType } from '@/api/types';

const SITE_TYPES: SiteType[] = [
  'indoor',
  'outdoor',
  'greenhouse',
  'windowsill',
  'balcony',
  'grow_tent',
];

interface SiteSetupStepProps {
  siteName: string;
  onSiteNameChange: (name: string) => void;
  siteType: SiteType;
  onSiteTypeChange: (type: SiteType) => void;
  experienceLevel: ExperienceLevel;
  tapWaterEc: string;
  onTapWaterEcChange: (val: string) => void;
  tapWaterPh: string;
  onTapWaterPhChange: (val: string) => void;
  hasRoSystem: boolean;
  onHasRoSystemChange: (val: boolean) => void;
  existingSites: Site[];
  existingSitesLoading: boolean;
  selectedSiteKey: string | null;
  onSelectedSiteKeyChange: (key: string | null) => void;
}

export default function SiteSetupStep({
  siteName,
  onSiteNameChange,
  siteType,
  onSiteTypeChange,
  experienceLevel,
  tapWaterEc,
  onTapWaterEcChange,
  tapWaterPh,
  onTapWaterPhChange,
  hasRoSystem,
  onHasRoSystemChange,
  existingSites,
  existingSitesLoading,
  selectedSiteKey,
  onSelectedSiteKeyChange,
}: SiteSetupStepProps) {
  const { t } = useTranslation();

  const isNewSite = selectedSiteKey === null;

  const handleSelectExistingSite = (siteKey: string) => {
    if (selectedSiteKey === siteKey) {
      // Deselect → back to new site
      onSelectedSiteKeyChange(null);
    } else {
      onSelectedSiteKeyChange(siteKey);
    }
  };

  const handleSelectNewSite = () => {
    onSelectedSiteKeyChange(null);
  };

  return (
    <Box
      data-testid="onboarding-step-site"
      sx={{ maxWidth: 560, display: 'flex', flexDirection: 'column', gap: 2.5 }}
    >
      <Typography variant="subtitle1" sx={{ fontWeight: 600 }}>
        {t('pages.onboarding.site.title')}
      </Typography>
      <Typography variant="body2" color="text.secondary">
        {t('pages.onboarding.site.subtitle')}
      </Typography>

      {/* Prepared new site card */}
      <Card
        variant="outlined"
        sx={{
          borderColor: isNewSite ? 'primary.main' : 'divider',
          borderWidth: isNewSite ? 2 : 1,
          bgcolor: isNewSite ? 'action.selected' : 'background.paper',
          transition: 'border-color 0.2s, background-color 0.2s',
        }}
      >
        <CardActionArea
          onClick={handleSelectNewSite}
          data-testid="site-option-new"
        >
          <CardContent sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
            <AddCircleOutlineIcon
              color={isNewSite ? 'primary' : 'action'}
              sx={{ fontSize: '2rem' }}
            />
            <Box sx={{ flex: 1, minWidth: 0 }}>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 0.25 }}>
                <Typography variant="subtitle2" noWrap>
                  {siteName || t('pages.onboarding.site.newSitePlaceholder')}
                </Typography>
                <Chip
                  icon={<AutoAwesomeIcon />}
                  label={t('pages.onboarding.site.preparedBadge')}
                  size="small"
                  color="primary"
                  variant="outlined"
                />
              </Box>
              <Typography variant="body2" color="text.secondary" noWrap>
                {t(`enums.siteType.${siteType}`)}
              </Typography>
            </Box>
            {isNewSite && (
              <CheckCircleIcon color="primary" />
            )}
          </CardContent>
        </CardActionArea>
      </Card>

      {/* New site configuration — only shown when new site is selected */}
      {isNewSite && (
        <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2.5, pl: { sm: 1 } }}>
          <TextField
            label={t('pages.onboarding.siteName')}
            value={siteName}
            onChange={(e) => onSiteNameChange(e.target.value)}
            fullWidth
            helperText={t('pages.onboarding.siteNameHelper')}
            autoFocus
            data-testid="site-name-field"
          />
          <FormControl fullWidth>
            <InputLabel id="site-type-label">
              {t('pages.onboarding.siteType')}
            </InputLabel>
            <Select
              labelId="site-type-label"
              value={siteType}
              label={t('pages.onboarding.siteType')}
              onChange={(e) => onSiteTypeChange(e.target.value as SiteType)}
              data-testid="site-type-select"
            >
              {SITE_TYPES.map((type) => (
                <MenuItem key={type} value={type}>
                  {t(`enums.siteType.${type}`)}
                </MenuItem>
              ))}
            </Select>
          </FormControl>
          {experienceLevel !== 'beginner' && (
            <>
              <Divider sx={{ my: 0.5 }} />
              <Typography variant="subtitle2">
                {t('pages.onboarding.waterSection')}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                {t('pages.onboarding.waterSectionHelper')}
              </Typography>
              <Box
                sx={{
                  display: 'grid',
                  gridTemplateColumns: { xs: '1fr', sm: '1fr 1fr' },
                  gap: 2,
                }}
              >
                <TextField
                  label={t('pages.onboarding.tapWaterEc')}
                  type="number"
                  value={tapWaterEc}
                  onChange={(e) => onTapWaterEcChange(e.target.value)}
                  slotProps={{
                    htmlInput: { step: 0.01, min: 0, max: 2.0, inputMode: 'decimal' },
                    input: { endAdornment: <InputAdornment position="end">mS/cm</InputAdornment> },
                  }}
                  helperText={t('pages.onboarding.tapWaterEcHelper')}
                  data-testid="onboarding-tap-ec"
                />
                <TextField
                  label={t('pages.onboarding.tapWaterPh')}
                  type="number"
                  value={tapWaterPh}
                  onChange={(e) => onTapWaterPhChange(e.target.value)}
                  slotProps={{ htmlInput: { step: 0.1, min: 3.0, max: 10.0, inputMode: 'decimal' } }}
                  helperText={t('pages.onboarding.tapWaterPhHelper')}
                  data-testid="onboarding-tap-ph"
                />
              </Box>
              <FormControlLabel
                control={
                  <Switch
                    checked={hasRoSystem}
                    onChange={(e) => onHasRoSystemChange(e.target.checked)}
                    data-testid="onboarding-ro-toggle"
                  />
                }
                label={t('pages.onboarding.hasRoSystemToggle')}
              />
            </>
          )}
        </Box>
      )}

      {/* Existing sites section */}
      {existingSitesLoading ? (
        <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1.5 }}>
          <Skeleton variant="rounded" height={72} />
          <Skeleton variant="rounded" height={72} />
        </Box>
      ) : existingSites.length > 0 && (
        <>
          <Divider sx={{ my: 0.5 }} />
          <Typography variant="subtitle2" color="text.secondary">
            {t('pages.onboarding.site.existingTitle')}
          </Typography>

          <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1.5 }}>
            {existingSites.map((site) => {
              const isSelected = selectedSiteKey === site.key;
              return (
                <Card
                  key={site.key}
                  variant="outlined"
                  sx={{
                    borderColor: isSelected ? 'primary.main' : 'divider',
                    borderWidth: isSelected ? 2 : 1,
                    bgcolor: isSelected ? 'action.selected' : 'background.paper',
                    transition: 'border-color 0.2s, background-color 0.2s',
                  }}
                >
                  <CardActionArea
                    onClick={() => handleSelectExistingSite(site.key)}
                    data-testid={`site-option-${site.key}`}
                  >
                    <CardContent sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
                      <PlaceIcon
                        color={isSelected ? 'primary' : 'action'}
                        sx={{ fontSize: '2rem' }}
                      />
                      <Box sx={{ flex: 1, minWidth: 0 }}>
                        <Typography variant="subtitle2" noWrap>
                          {site.name}
                        </Typography>
                        <Typography variant="body2" color="text.secondary" noWrap>
                          {t(`enums.siteType.${site.type}`)}
                        </Typography>
                      </Box>
                      {isSelected && (
                        <CheckCircleIcon color="primary" />
                      )}
                    </CardContent>
                  </CardActionArea>
                </Card>
              );
            })}
          </Box>
        </>
      )}
    </Box>
  );
}
