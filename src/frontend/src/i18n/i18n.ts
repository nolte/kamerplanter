import i18n from 'i18next';
import { initReactI18next } from 'react-i18next';
import LanguageDetector from 'i18next-browser-languagedetector';
import de from './locales/de/translation.json';
import en from './locales/en/translation.json';

i18n
  .use(LanguageDetector)
  .use(initReactI18next)
  .init({
    resources: {
      de: { translation: de },
      en: { translation: en },
    },
    fallbackLng: 'de',
    interpolation: {
      escapeValue: false,
    },
    detection: {
      order: ['localStorage', 'navigator'],
      caches: ['localStorage'],
      lookupLocalStorage: 'kamerplanter-lang',
    },
  });

if (import.meta.hot) {
  import.meta.hot.accept(
    ['./locales/de/translation.json', './locales/en/translation.json'],
    ([deModule, enModule]) => {
      if (deModule) i18n.addResourceBundle('de', 'translation', deModule.default, true, true);
      if (enModule) i18n.addResourceBundle('en', 'translation', enModule.default, true, true);
    },
  );
}

export default i18n;
