import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { useSnackbar } from 'notistack';
import Box from '@mui/material/Box';
import Card from '@mui/material/Card';
import CardContent from '@mui/material/CardContent';
import TextField from '@mui/material/TextField';
import Button from '@mui/material/Button';
import Typography from '@mui/material/Typography';
import { useAppDispatch } from '@/store/hooks';
import { createOrganization } from '@/store/slices/tenantSlice';
import PageTitle from '@/components/layout/PageTitle';
import { parseApiError } from '@/api/errors';

export default function TenantCreatePage() {
  const { t } = useTranslation();
  const dispatch = useAppDispatch();
  const navigate = useNavigate();
  const { enqueueSnackbar } = useSnackbar();

  const [name, setName] = useState('');
  const [description, setDescription] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    try {
      await dispatch(createOrganization({ name, description: description || undefined })).unwrap();
      enqueueSnackbar(t('pages.tenants.created'), { variant: 'success' });
      navigate('/dashboard');
    } catch (err) {
      setError(parseApiError(err));
    } finally {
      setLoading(false);
    }
  };

  return (
    <Box sx={{ maxWidth: 600, mx: 'auto', mt: 4 }}>
      <PageTitle title={t('pages.tenants.createOrganization')} />
      <Card>
        <CardContent>
          <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
            {t('pages.tenants.createIntro')}
          </Typography>
          <Box component="form" onSubmit={handleSubmit} sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
            <TextField
              label={t('pages.tenants.name')}
              value={name}
              onChange={(e) => setName(e.target.value)}
              required
              autoFocus
              inputProps={{ minLength: 2, maxLength: 200 }}
            />
            <TextField
              label={t('pages.tenants.description')}
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              multiline
              rows={3}
            />
            {error && (
              <Typography color="error" variant="body2">{error}</Typography>
            )}
            <Button type="submit" variant="contained" disabled={loading || name.length < 2}>
              {t('common.create')}
            </Button>
          </Box>
        </CardContent>
      </Card>
    </Box>
  );
}
