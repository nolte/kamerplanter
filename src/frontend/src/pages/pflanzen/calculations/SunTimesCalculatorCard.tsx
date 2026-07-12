import { useEffect, useMemo, useState } from 'react';
import { useTranslation } from 'react-i18next';
import Card from '@mui/material/Card';
import CardContent from '@mui/material/CardContent';
import Typography from '@mui/material/Typography';
import TextField from '@mui/material/TextField';
import InputAdornment from '@mui/material/InputAdornment';
import Autocomplete from '@mui/material/Autocomplete';
import Button from '@mui/material/Button';
import Alert from '@mui/material/Alert';
import Box from '@mui/material/Box';
import { useApiError } from '@/hooks/useApiError';
import { useAppDispatch, useAppSelector } from '@/store/hooks';
import { fetchSites } from '@/store/slices/sitesSlice';
import * as calcApi from '@/api/endpoints/calculations';
import type { Site, SunTimesResponse } from '@/api/types';
import { DEFAULT_TIMEZONE, getTimezoneOptions } from './timezones';

const SITE_NONE = '';

/**
 * Sun-times calculator. Timezone is an IANA `Autocomplete` (no more free-text),
 * and coordinates can be prefilled by picking an existing site (GPS + timezone).
 * Manual latitude/longitude entry stays available. Payload unchanged:
 * `{ latitude, longitude, date, timezone }` → `POST /calculations/sun-times`.
 */
export default function SunTimesCalculatorCard() {
  const { t } = useTranslation();
  const { handleError } = useApiError();
  const dispatch = useAppDispatch();
  const sites = useAppSelector((s) => s.sites.sites);

  const [siteKey, setSiteKey] = useState<string>(SITE_NONE);
  const [lat, setLat] = useState(52.52);
  const [lon, setLon] = useState(13.405);
  const [date, setDate] = useState(() => new Date().toISOString().split('T')[0]);
  const [timezone, setTimezone] = useState(DEFAULT_TIMEZONE);
  const [result, setResult] = useState<SunTimesResponse | null>(null);

  useEffect(() => {
    if (sites.length === 0) {
      void dispatch(fetchSites({}));
    }
  }, [dispatch, sites.length]);

  const timezoneOptions = useMemo(() => getTimezoneOptions(), []);

  const geoSites = useMemo(
    () => sites.filter((site) => site.gps_coordinates != null),
    [sites],
  );

  const applySite = (site: Site | null) => {
    if (site == null) {
      setSiteKey(SITE_NONE);
      return;
    }
    setSiteKey(site.key);
    if (site.gps_coordinates) {
      setLat(site.gps_coordinates[0]);
      setLon(site.gps_coordinates[1]);
    }
    if (site.timezone) setTimezone(site.timezone);
  };

  const calculate = async () => {
    try {
      const res = await calcApi.calculateSunTimes({
        latitude: lat,
        longitude: lon,
        date,
        timezone,
      });
      setResult(res);
    } catch (err) {
      handleError(err);
    }
  };

  const selectedSite = useMemo(
    () => geoSites.find((site) => site.key === siteKey) ?? null,
    [geoSites, siteKey],
  );

  return (
    <Card>
      <CardContent>
        <Typography variant="h6" component="h2" sx={{ mb: 1 }}>
          {t('pages.calculations.sunTimes')}
        </Typography>
        <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
          {t('pages.calculations.sunTimesIntro')}
        </Typography>

        {geoSites.length > 0 && (
          <Autocomplete
            options={geoSites}
            value={selectedSite}
            getOptionLabel={(site) => site.name}
            isOptionEqualToValue={(option, val) => option.key === val.key}
            onChange={(_event, site) => applySite(site)}
            renderInput={(params) => (
              <TextField
                {...params}
                label={t('pages.calculations.sunTimesSite')}
                helperText={t('pages.calculations.sunTimesSiteHelp')}
              />
            )}
            sx={{ mb: 2 }}
          />
        )}

        <TextField
          type="number"
          label={t('pages.calculations.latitude')}
          value={lat}
          onChange={(e) => setLat(Number(e.target.value))}
          fullWidth
          sx={{ mb: 2 }}
          slotProps={{
            htmlInput: { min: -90, max: 90, step: 0.0001 },
            input: { endAdornment: <InputAdornment position="end">°</InputAdornment> },
          }}
        />
        <TextField
          type="number"
          label={t('pages.calculations.longitude')}
          value={lon}
          onChange={(e) => setLon(Number(e.target.value))}
          fullWidth
          sx={{ mb: 2 }}
          slotProps={{
            htmlInput: { min: -180, max: 180, step: 0.0001 },
            input: { endAdornment: <InputAdornment position="end">°</InputAdornment> },
          }}
        />
        <TextField
          type="date"
          label={t('pages.calculations.date')}
          value={date}
          onChange={(e) => setDate(e.target.value)}
          fullWidth
          sx={{ mb: 2 }}
          slotProps={{ inputLabel: { shrink: true } }}
        />

        <Autocomplete
          options={timezoneOptions}
          value={timezone}
          disableClearable
          onChange={(_event, value) => {
            if (value) setTimezone(value);
          }}
          renderInput={(params) => (
            <TextField {...params} label={t('pages.calculations.timezone')} />
          )}
          sx={{ mb: 2 }}
        />

        <Button variant="contained" onClick={calculate} fullWidth>
          {t('pages.calculations.calculate')}
        </Button>

        {result && (
          <Box sx={{ mt: 2 }}>
            <Alert severity="info">
              <Box>
                {t('pages.calculations.sunrise')}: {result.sunrise}
                {' · '}
                {t('pages.calculations.sunset')}: {result.sunset}
              </Box>
              <Box sx={{ mt: 0.5 }}>
                {t('pages.calculations.dawn')}: {result.dawn}
                {' · '}
                {t('pages.calculations.dusk')}: {result.dusk}
              </Box>
              <Box sx={{ mt: 0.5, fontWeight: 600 }}>
                {t('pages.calculations.dayLength')}: {result.day_length_hours.toFixed(2)} h
              </Box>
            </Alert>
          </Box>
        )}
      </CardContent>
    </Card>
  );
}
