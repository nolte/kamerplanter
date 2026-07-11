import { RouterProvider } from 'react-router-dom';
import { Provider } from 'react-redux';
import { SnackbarProvider } from 'notistack';
import { ThemeContextProvider } from '@/theme';
import { store } from '@/store/store';
import { router } from '@/routes/AppRoutes';
import AuthProvider from '@/auth/AuthProvider';
import { KioskProvider } from '@/kiosk/KioskProvider';

export default function App() {
  return (
    <Provider store={store}>
      {/* UI-NFR-019 — KioskProvider is outside ThemeContextProvider so the kiosk
          flags can select the high-contrast/touch theme without a reload. */}
      <KioskProvider>
        <ThemeContextProvider>
          <SnackbarProvider
            maxSnack={3}
            anchorOrigin={{ vertical: 'bottom', horizontal: 'right' }}
            autoHideDuration={5000}
            style={{ maxWidth: '480px', whiteSpace: 'pre-line' }}
          >
            <AuthProvider>
              <RouterProvider router={router} />
            </AuthProvider>
          </SnackbarProvider>
        </ThemeContextProvider>
      </KioskProvider>
    </Provider>
  );
}
