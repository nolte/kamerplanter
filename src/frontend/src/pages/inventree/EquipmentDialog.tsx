import { useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import Dialog from '@mui/material/Dialog';
import DialogTitle from '@mui/material/DialogTitle';
import DialogContent from '@mui/material/DialogContent';
import Typography from '@mui/material/Typography';
import useMediaQuery from '@mui/material/useMediaQuery';
import { useTheme } from '@mui/material/styles';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import FormTextField from '@/components/form/FormTextField';
import FormSelectField from '@/components/form/FormSelectField';
import FormNumberField from '@/components/form/FormNumberField';
import FormRow from '@/components/form/FormRow';
import FormActions from '@/components/form/FormActions';
import UnsavedChangesGuard from '@/components/form/UnsavedChangesGuard';
import HelpTooltip from '@/components/common/HelpTooltip';
import { useNotification } from '@/hooks/useNotification';
import { useApiError } from '@/hooks/useApiError';
import * as api from '@/api/endpoints/inventree';
import type { Equipment, EquipmentStatus, EquipmentType } from '@/api/types';

const equipmentTypes: EquipmentType[] = [
  'tool',
  'consumable',
  'sensor',
  'lighting',
  'pump',
  'filter',
  'container',
  'cleaning_agent',
  'other',
];

const equipmentStatuses: EquipmentStatus[] = [
  'active',
  'maintenance',
  'stored',
  'defective',
  'retired',
];

const schema = z.object({
  name: z.string().min(1),
  equipment_type: z.enum([
    'tool',
    'consumable',
    'sensor',
    'lighting',
    'pump',
    'filter',
    'container',
    'cleaning_agent',
    'other',
  ]),
  status: z.enum(['active', 'maintenance', 'stored', 'defective', 'retired']),
  brand: z.string().nullable(),
  model: z.string().nullable(),
  serial_number: z.string().nullable(),
  inventree_part_id: z.number().int().positive().nullable(),
  notes: z.string().nullable(),
});

type FormData = z.infer<typeof schema>;

interface Props {
  open: boolean;
  /** When set, the dialog edits an existing item; otherwise it creates one. */
  equipment: Equipment | null;
  onClose: () => void;
  onSaved: () => void;
}

export default function EquipmentDialog({ open, equipment, onClose, onSaved }: Props) {
  const { t } = useTranslation();
  const theme = useTheme();
  const fullScreen = useMediaQuery(theme.breakpoints.down('sm'));
  const notification = useNotification();
  const { handleError } = useApiError();

  const defaults: FormData = {
    name: '',
    equipment_type: 'sensor',
    status: 'active',
    brand: null,
    model: null,
    serial_number: null,
    inventree_part_id: null,
    notes: null,
  };

  const {
    control,
    handleSubmit,
    reset,
    formState: { isDirty, isSubmitting },
  } = useForm<FormData>({ resolver: zodResolver(schema), defaultValues: defaults });

  useEffect(() => {
    if (open) {
      reset(
        equipment
          ? {
              name: equipment.name,
              equipment_type: equipment.equipment_type,
              status: equipment.status,
              brand: equipment.brand ?? null,
              model: equipment.model ?? null,
              serial_number: equipment.serial_number ?? null,
              inventree_part_id: equipment.inventree_part_id ?? null,
              notes: equipment.notes ?? null,
            }
          : defaults,
      );
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [open, equipment]);

  const onSubmit = async (data: FormData) => {
    try {
      if (equipment) {
        await api.updateEquipment(equipment.key, data);
      } else {
        await api.createEquipment(data);
      }
      onSaved();
    } catch (error) {
      // No field-level mapping: this dialog has no coded cross-field violation to
      // translate, so the generic toast is the correct floor. The widened
      // useApiError contract (#1015) keeps the backend's English `reason` off the
      // German form; a coded violation, should one arise, is wired via
      // `useFieldViolations` with a `code → i18n key` map.
      handleError(error);
      notification.error(t('errors.generic'));
    }
  };

  const handleClose = () => {
    reset(defaults);
    onClose();
  };

  return (
    <Dialog open={open} onClose={handleClose} fullScreen={fullScreen} fullWidth maxWidth="sm">
      <DialogTitle>
        {equipment
          ? t('pages.inventree.editEquipment')
          : t('pages.inventree.createEquipment')}
      </DialogTitle>
      <DialogContent>
        <UnsavedChangesGuard dirty={isDirty} />
        <form onSubmit={handleSubmit(onSubmit)} noValidate>
          <FormTextField
            name="name"
            control={control}
            label={t('pages.inventree.fields.name')}
            required
            autoFocus
          />
          <FormRow>
            <FormSelectField
              name="equipment_type"
              control={control}
              label={t('pages.inventree.fields.equipmentType')}
              required
              options={equipmentTypes.map((v) => ({
                value: v,
                label: t(`enums.equipmentType.${v}`),
              }))}
            />
            <FormSelectField
              name="status"
              control={control}
              label={t('pages.inventree.fields.status')}
              required
              options={equipmentStatuses.map((v) => ({
                value: v,
                label: t(`enums.equipmentStatus.${v}`),
              }))}
            />
          </FormRow>
          <FormRow>
            <FormTextField
              name="brand"
              control={control}
              label={t('pages.inventree.fields.brand')}
            />
            <FormTextField
              name="model"
              control={control}
              label={t('pages.inventree.fields.model')}
            />
          </FormRow>
          <FormTextField
            name="serial_number"
            control={control}
            label={t('pages.inventree.fields.serialNumber')}
          />

          <HelpTooltip term="inventree">
            <Typography variant="subtitle2" color="text.secondary" sx={{ mt: 2 }}>
              {t('pages.inventree.sectionInventree')}
            </Typography>
          </HelpTooltip>
          <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
            {t('pages.inventree.sectionInventreeHelper')}
          </Typography>
          <FormNumberField
            name="inventree_part_id"
            control={control}
            label={t('pages.inventree.fields.inventreePartId')}
            helperText={t('pages.inventree.fields.inventreePartHelp')}
            step={1}
            min={1}
            inputMode="numeric"
          />

          <FormTextField
            name="notes"
            control={control}
            label={t('pages.inventree.fields.notes')}
            multiline
          />
          <FormActions onCancel={handleClose} loading={isSubmitting} />
        </form>
      </DialogContent>
    </Dialog>
  );
}
