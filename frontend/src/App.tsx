import { CssBaseline, ThemeProvider, alpha, createTheme } from '@mui/material';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { useMemo, useState } from 'react';
import { BrowserRouter, Route, Routes } from 'react-router';

import { AppLayout } from './components/AppLayout';
import { CompaniesPage } from './pages/CompaniesPage';
import { DashboardPage } from './pages/DashboardPage';
import { JobsPage } from './pages/JobsPage';
import { RecruitersPage } from './pages/RecruitersPage';
import { PlaceholderPage } from './pages/PlaceholderPage';

const queryClient = new QueryClient();

export function App() {
  const [darkMode, setDarkMode] = useState(true);
  const theme = useMemo(
    () =>
      createTheme({
        palette: {
          mode: darkMode ? 'dark' : 'light',
          primary: { main: '#177e89' },
          secondary: { main: '#d17b0f' },
          background: {
            default: darkMode ? '#0f1315' : '#f4f6f7',
            paper: darkMode ? '#151a1d' : '#ffffff',
          },
          divider: darkMode ? 'rgba(255,255,255,0.08)' : 'rgba(15,23,42,0.12)',
        },
        shape: { borderRadius: 8 },
        typography: {
          fontFamily:
            'Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif',
          h4: { fontWeight: 800, letterSpacing: 0 },
          h6: { fontWeight: 700, letterSpacing: 0 },
          button: { textTransform: 'none', fontWeight: 700 },
        },
        components: {
          MuiCssBaseline: {
            styleOverrides: {
              body: {
                backgroundImage: 'none',
              },
            },
          },
          MuiPaper: {
            styleOverrides: {
              root: {
                backgroundImage: 'none',
                borderColor: darkMode ? 'rgba(255,255,255,0.08)' : 'rgba(15,23,42,0.12)',
              },
            },
          },
          MuiAppBar: {
            styleOverrides: {
              root: {
                backgroundColor: darkMode ? alpha('#0f1315', 0.92) : alpha('#f4f6f7', 0.92),
                backdropFilter: 'blur(10px)',
              },
            },
          },
          MuiButton: {
            styleOverrides: {
              root: {
                borderRadius: 8,
              },
            },
          },
          MuiChip: {
            styleOverrides: {
              root: {
                borderRadius: 8,
              },
            },
          },
        },
      }),
    [darkMode],
  );

  return (
    <QueryClientProvider client={queryClient}>
      <ThemeProvider theme={theme}>
        <CssBaseline />
        <BrowserRouter>
          <AppLayout darkMode={darkMode} onToggleDarkMode={() => setDarkMode((value) => !value)}>
            <Routes>
              <Route path="/" element={<DashboardPage />} />
              <Route path="/jobs" element={<JobsPage />} />
              <Route path="/applications" element={<PlaceholderPage title="Applications" />} />
              <Route path="/recruiters" element={<RecruitersPage />} />
              <Route path="/companies" element={<CompaniesPage />} />
              <Route path="/resumes" element={<PlaceholderPage title="Resume Versions" />} />
              <Route path="/analytics" element={<PlaceholderPage title="Analytics" />} />
              <Route path="/settings" element={<PlaceholderPage title="Settings" />} />
            </Routes>
          </AppLayout>
        </BrowserRouter>
      </ThemeProvider>
    </QueryClientProvider>
  );
}
