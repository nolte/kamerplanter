import React from 'react';
import ReactDOM from 'react-dom/client';
import App from './App';
import i18n, { initI18n } from './i18n';
import ErrorBoundary from '@/components/common/ErrorBoundary';
import { initErrorTracking } from '@/observability/errorTracking';
import './styles/print.css';
import { registerServiceWorker } from './serviceWorkerRegistration';

function mount() {
  ReactDOM.createRoot(document.getElementById('root')!).render(
    <React.StrictMode>
      {/* #777 — the outermost boundary. Without one, a render error anywhere in
          the tree unmounts the whole app and leaves a blank page: React's
          documented behaviour when nothing catches. The MUI fallback keeps a
          retry within reach and reports the failure to the error tracker. */}
      <ErrorBoundary
        title={i18n.t('common.appError.title')}
        hint={i18n.t('common.appError.hint')}
        retryLabel={i18n.t('common.retry')}
        // Retry alone re-mounts <App> with whatever state caused the crash —
        // for a genuinely broken build/state that's the same failure again
        // immediately. "page" variant + reloadLabel adds a real
        // window.location.reload() as an explicit second way out, and
        // centers/fills the viewport instead of the widget-tile layout this
        // component otherwise renders (there's no page chrome around it here
        // to react to).
        variant="page"
        reloadLabel={i18n.t('common.appError.reloadPage')}
        testId="app-error"
        boundaryName="app-root"
      >
        <App />
      </ErrorBoundary>
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
//
// #777 — error tracking is awaited alongside it rather than after mount, so the
// SDK's global handlers are installed before the first component renders. It
// resolves immediately, loading nothing, when no DSN is configured — which is
// the default everywhere except a deployment that opts in.
Promise.all([initI18n().catch(() => undefined), initErrorTracking().catch(() => false)]).finally(
  mount,
);
