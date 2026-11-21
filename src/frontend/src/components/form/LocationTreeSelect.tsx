import { useEffect, useState, useCallback } from 'react';
import TextField from '@mui/material/TextField';
import MenuItem from '@mui/material/MenuItem';
import ListItemText from '@mui/material/ListItemText';
import { Controller, type Control, type FieldValues, type Path } from 'react-hook-form';
import { useTranslation } from 'react-i18next';
import * as sitesApi from '@/api/endpoints/sites';
import OptionsLoadError from '@/components/common/OptionsLoadError';
import { captureHandledError } from '@/observability/errorTracking';
import type { LocationTreeNode } from '@/api/types';

interface FlatOption {
  key: string;
  label: string;
  depth: number;
}

function flattenTree(nodes: LocationTreeNode[], depth = 0): FlatOption[] {
  const result: FlatOption[] = [];
  for (const node of nodes) {
    result.push({ key: node.key, label: node.name, depth });
    if (node.children.length > 0) {
      result.push(...flattenTree(node.children, depth + 1));
    }
  }
  return result;
}

interface LocationTreeSelectProps<T extends FieldValues> {
  name: Path<T>;
  control: Control<T>;
  siteKey: string | null | undefined;
  label?: string;
  disabled?: boolean;
  required?: boolean;
  /**
   * Helper text shown below the field when there is no validation error and no
   * empty-state message applies. Use it to explain what a "Bereich" is.
   */
  helperText?: string;
  /**
   * Helper text shown when a site is selected but it has no areas yet. Surfaces
   * the reason an otherwise-usable field renders as empty instead of leaving
   * the user guessing (issue #543).
   */
  emptyHelperText?: string;
  /** Called after the tree finished loading, with the number of flat options. */
  onTreeLoaded?: (optionCount: number) => void;
}

export default function LocationTreeSelect<T extends FieldValues>({
  name,
  control,
  siteKey,
  label,
  disabled,
  required,
  helperText,
  emptyHelperText,
  onTreeLoaded,
}: LocationTreeSelectProps<T>) {
  const { t } = useTranslation();
  const [options, setOptions] = useState<FlatOption[]>([]);
  const [loading, setLoading] = useState(false);
  // A failed read is shown with a retry, never as "this site has no areas" (#3037).
  const [loadError, setLoadError] = useState(false);

  const loadTree = useCallback(async () => {
    setLoadError(false);
    if (!siteKey) {
      setOptions([]);
      return;
    }
    setLoading(true);
    try {
      const tree = await sitesApi.getLocationTree(siteKey);
      const flat = flattenTree(tree);
      setOptions(flat);
      onTreeLoaded?.(flat.length);
    } catch (err) {
      // Not reported through `onTreeLoaded`: a failed read is no count of areas.
      captureHandledError(err, { source: 'LocationTreeSelect.tree' });
      setOptions([]);
      setLoadError(true);
    } finally {
      setLoading(false);
    }
  }, [siteKey, onTreeLoaded]);

  useEffect(() => {
    loadTree();
  }, [loadTree]);

  const isEmptyForSite = !!siteKey && !loading && !loadError && options.length === 0;

  return (
    <>
      <Controller
        name={name}
        control={control}
        render={({ field, fieldState: { error } }) => {
          const nonErrorHelper = isEmptyForSite ? (emptyHelperText ?? helperText) : helperText;
          return (
            <TextField
              {...field}
              value={field.value ?? ''}
              select
              label={label ?? t('entities.location')}
              required={required}
              disabled={disabled || loading || !siteKey}
              error={!!error}
              helperText={error?.message ?? nonErrorHelper}
              fullWidth
              sx={{ mb: 2 }}
              data-testid={`form-field-${name}`}
            >
              <MenuItem value="" data-testid={`form-option-${name}-empty`}>
                {'—'}
              </MenuItem>
              {options.map((opt) => (
                <MenuItem key={opt.key} value={opt.key} data-testid={`form-option-${name}-${opt.key}`}>
                  <ListItemText
                    primary={opt.label}
                    sx={{ pl: opt.depth * 2 }}
                  />
                </MenuItem>
              ))}
            </TextField>
          );
        }}
      />
      {loadError && (
        <OptionsLoadError onRetry={() => void loadTree()} data-testid={`form-field-${name}-load-error`} />
      )}
    </>
  );
}
