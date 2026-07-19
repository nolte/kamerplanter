import { useTranslation } from 'react-i18next';
import IconButton from '@mui/material/IconButton';
import Menu from '@mui/material/Menu';
import MenuItem from '@mui/material/MenuItem';
import TranslateIcon from '@mui/icons-material/Translate';
import { useState } from 'react';
import { loadFeatureNamespaces, SUPPORTED_LOCALES, type SupportedLocale } from '@/i18n';

const languages = [
  { code: 'de', label: 'Deutsch' },
  { code: 'en', label: 'English' },
];

export default function LanguageSelector() {
  const { i18n } = useTranslation();
  const [anchorEl, setAnchorEl] = useState<null | HTMLElement>(null);

  // #612 — feature namespaces are code-split. Preload every locale's bundles the
  // moment the menu opens so the language switch itself is instant and never
  // flashes untranslated content.
  const handleOpen = (event: React.MouseEvent<HTMLElement>) => {
    setAnchorEl(event.currentTarget);
    for (const locale of SUPPORTED_LOCALES) {
      void loadFeatureNamespaces(locale as SupportedLocale).catch(() => undefined);
    }
  };

  return (
    <>
      <IconButton color="inherit" onClick={handleOpen} aria-label="change language">
        <TranslateIcon />
      </IconButton>
      <Menu anchorEl={anchorEl} open={Boolean(anchorEl)} onClose={() => setAnchorEl(null)}>
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
