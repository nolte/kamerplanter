import React from 'react';
import ReactDOM from 'react-dom/client';
import App from './App';
import './i18n';
import './styles/print.css';
import { registerServiceWorker } from './serviceWorkerRegistration';

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
);

// Register the service worker for Web Push (PWA notifications). Guarded and
// non-fatal: a registration failure must never break app startup.
registerServiceWorker();
