import React from 'react';
import ReactDOM from 'react-dom/client';
import App from './App';
import { initI18n } from './i18n';
import './styles/print.css';
import { registerServiceWorker } from './serviceWorkerRegistration';

function mount() {
  ReactDOM.createRoot(document.getElementById('root')!).render(
    <React.StrictMode>
      <App />
    </React.StrictMode>,
  );

  // Register the service worker for Web Push (PWA notifications). Guarded and
  // non-fatal: a registration failure must never break app startup.
  registerServiceWorker();
}

// #612 — the feature translation namespaces are code-split and dynamically
// imported. Await the active locale (+ German fallback) before mounting so the
// first render already has every translation: a graceful load boundary that
// prevents a flash of untranslated content. A failure here must never block
// startup — mount anyway; the core namespace still resolves the shell and the
// languageChanged listener retries the feature bundles.
initI18n()
  .catch(() => undefined)
  .finally(mount);
