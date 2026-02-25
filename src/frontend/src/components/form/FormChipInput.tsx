import { useState, type KeyboardEvent } from 'react';
import TextField from '@mui/material/TextField';
import Chip from '@mui/material/Chip';
import Box from '@mui/material/Box';
import { Controller, type Control, type FieldValues, type Path } from 'react-hook-form';

interface FormChipInputProps<T extends FieldValues> {
  name: Path<T>;
  control: Control<T>;
  label: string;
  placeholder?: string;
  disabled?: boolean;
  helperText?: string;
}

export default function FormChipInput<T extends FieldValues>({
  name,
  control,
  label,
  placeholder,
  disabled,
  helperText,
}: FormChipInputProps<T>) {
  const [inputValue, setInputValue] = useState('');

  return (
    <Controller
      name={name}
      control={control}
      render={({ field, fieldState: { error } }) => {
        const values: string[] = Array.isArray(field.value) ? field.value : [];

        const handleAdd = () => {
          const trimmed = inputValue.trim();
          if (trimmed && !values.includes(trimmed)) {
            field.onChange([...values, trimmed]);
          }
          setInputValue('');
        };

        const handleKeyDown = (e: KeyboardEvent) => {
          if (e.key === 'Enter') {
            e.preventDefault();
            handleAdd();
          }
        };

        const handleDelete = (item: string) => {
          field.onChange(values.filter((v) => v !== item));
        };

        return (
          <Box sx={{ mb: 2 }}>
            <TextField
              label={label}
              placeholder={placeholder}
              disabled={disabled}
              value={inputValue}
              onChange={(e) => setInputValue(e.target.value)}
              onKeyDown={handleKeyDown}
              onBlur={handleAdd}
              error={!!error}
              helperText={error?.message ?? helperText}
              fullWidth
            />
            {values.length > 0 && (
              <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5, mt: 1 }}>
                {values.map((item) => (
                  <Chip
                    key={item}
                    label={item}
                    onDelete={disabled ? undefined : () => handleDelete(item)}
                    size="small"
                  />
                ))}
              </Box>
            )}
          </Box>
        );
      }}
    />
  );
}
