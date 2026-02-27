import { RouterProvider } from 'react-router-dom';
import { Provider } from 'react-redux';
import { SnackbarProvider } from 'notistack';
import { ThemeContextProvider } from '@/theme';
import { store } from '@/store/store';
import { router } from '@/routes/AppRoutes';
import AuthProvider from '@/auth/AuthProvider';

export default function App() {
  return (
    <Provider store={store}>
      <ThemeContextProvider>
        <SnackbarProvider
          maxSnack={3}
          anchorOrigin={{ vertical: 'bottom', horizontal: 'right' }}
          autoHideDuration={5000}
        >
          <AuthProvider>
            <RouterProvider router={router} />
          </AuthProvider>
        </SnackbarProvider>
      </ThemeContextProvider>
    </Provider>
  );
}
