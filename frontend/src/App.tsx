import { CssBaseline, ThemeProvider, createTheme } from '@mui/material';
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
          primary: { main: '#1f7a8c' },
          secondary: { main: '#bf5f45' },
          background: {
            default: darkMode ? '#111517' : '#f6f7f8',
            paper: darkMode ? '#181d20' : '#ffffff',
          },
        },
        shape: { borderRadius: 8 },
        typography: {
          fontFamily:
            'Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif',
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
