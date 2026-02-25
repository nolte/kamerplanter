import { useTranslation } from 'react-i18next';
import IconButton from '@mui/material/IconButton';
import Menu from '@mui/material/Menu';
import MenuItem from '@mui/material/MenuItem';
import TranslateIcon from '@mui/icons-material/Translate';
import { useState } from 'react';

const languages = [
  { code: 'de', label: 'Deutsch' },
  { code: 'en', label: 'English' },
];

export default function LanguageSelector() {
  const { i18n } = useTranslation();
  const [anchorEl, setAnchorEl] = useState<null | HTMLElement>(null);

  return (
    <>
      <IconButton
        color="inherit"
        onClick={(e) => setAnchorEl(e.currentTarget)}
        aria-label="change language"
      >
        <TranslateIcon />
      </IconButton>
      <Menu
        anchorEl={anchorEl}
        open={Boolean(anchorEl)}
        onClose={() => setAnchorEl(null)}
      >
        {languages.map((lang) => (
          <MenuItem
            key={lang.code}
            selected={i18n.language === lang.code}
            onClick={() => {
              i18n.changeLanguage(lang.code);
              setAnchorEl(null);
            }}
          >
            {lang.label}
          </MenuItem>
        ))}
      </Menu>
    </>
  );
}
