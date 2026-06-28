import AnalyticsIcon from '@mui/icons-material/Analytics';
import ApartmentIcon from '@mui/icons-material/Apartment';
import AssignmentTurnedInIcon from '@mui/icons-material/AssignmentTurnedIn';
import DashboardIcon from '@mui/icons-material/Dashboard';
import DescriptionIcon from '@mui/icons-material/Description';
import GroupIcon from '@mui/icons-material/Group';
import SearchIcon from '@mui/icons-material/Search';
import SettingsIcon from '@mui/icons-material/Settings';
import WorkIcon from '@mui/icons-material/Work';
import {
  AppBar,
  Avatar,
  Box,
  Divider,
  IconButton,
  InputAdornment,
  List,
  ListItemButton,
  ListItemIcon,
  ListItemText,
  Switch,
  TextField,
  Toolbar,
  Typography,
  Chip,
  Stack,
} from '@mui/material';
import type { ReactNode } from 'react';
import { Link, useLocation } from 'react-router';

type NavItem = {
  label: string;
  path: string;
  icon: ReactNode;
};

const navItems: NavItem[] = [
  { label: 'Dashboard', path: '/', icon: <DashboardIcon /> },
  { label: 'Jobs', path: '/jobs', icon: <WorkIcon /> },
  { label: 'Applications', path: '/applications', icon: <AssignmentTurnedInIcon /> },
  { label: 'Recruiters', path: '/recruiters', icon: <GroupIcon /> },
  { label: 'Companies', path: '/companies', icon: <ApartmentIcon /> },
  { label: 'Resume Versions', path: '/resumes', icon: <DescriptionIcon /> },
  { label: 'Analytics', path: '/analytics', icon: <AnalyticsIcon /> },
  { label: 'Settings', path: '/settings', icon: <SettingsIcon /> },
];

type AppLayoutProps = {
  children: ReactNode;
  darkMode: boolean;
  onToggleDarkMode: () => void;
};

export function AppLayout({ children, darkMode, onToggleDarkMode }: AppLayoutProps) {
  const location = useLocation();

  return (
    <Box sx={{ display: 'flex', minHeight: '100vh', bgcolor: 'background.default' }}>
      <Box
        component="aside"
        sx={{
          width: 288,
          borderRight: 1,
          borderColor: 'divider',
          display: { xs: 'none', md: 'block' },
          flexShrink: 0,
          bgcolor: 'background.paper',
          position: 'sticky',
          top: 0,
          height: '100vh',
        }}
      >
        <Toolbar sx={{ minHeight: 72, px: 2 }}>
          <Stack direction="row" spacing={1.5} alignItems="center" width="100%">
            <Avatar
              sx={{
                width: 36,
                height: 36,
                bgcolor: 'primary.main',
                fontSize: 16,
                fontWeight: 800,
              }}
            >
              JS
            </Avatar>
            <Box sx={{ minWidth: 0 }}>
              <Typography variant="h6" noWrap>
                Spoon Jops
              </Typography>
              <Typography variant="caption" color="text.secondary" noWrap>
                Bengaluru-first discovery workspace
              </Typography>
            </Box>
          </Stack>
        </Toolbar>
        <Divider />
        <Box sx={{ px: 1.5, py: 1.5 }}>
          <Chip label="Live discovery" size="small" color="primary" sx={{ mb: 1.5 }} />
        </Box>
        <List dense sx={{ px: 1 }}>
          {navItems.map((item) => (
            <ListItemButton
              key={item.path}
              component={Link}
              to={item.path}
              selected={location.pathname === item.path}
              sx={{
                minHeight: 44,
                borderRadius: 2,
                mb: 0.5,
                '&.Mui-selected': {
                  bgcolor: 'action.selected',
                  '&:hover': { bgcolor: 'action.selected' },
                },
              }}
            >
              <ListItemIcon sx={{ minWidth: 40 }}>{item.icon}</ListItemIcon>
              <ListItemText primary={item.label} />
            </ListItemButton>
          ))}
        </List>
      </Box>

      <Box sx={{ flex: 1, minWidth: 0 }}>
        <AppBar position="sticky" color="default" elevation={0} sx={{ borderBottom: 1, borderColor: 'divider' }}>
          <Toolbar sx={{ gap: 2, minHeight: 72 }}>
            <TextField
              size="small"
              placeholder="Search"
              sx={{ maxWidth: 520, flex: 1 }}
              variant="outlined"
              slotProps={{
                input: {
                  startAdornment: (
                    <InputAdornment position="start">
                      <SearchIcon fontSize="small" />
                    </InputAdornment>
                  ),
                },
              }}
            />
            <Chip label={darkMode ? 'Dark' : 'Light'} variant="outlined" />
            <Switch checked={darkMode} onChange={onToggleDarkMode} inputProps={{ 'aria-label': 'Dark mode' }} />
            <IconButton component={Link} to="/settings" aria-label="Settings">
              <SettingsIcon />
            </IconButton>
          </Toolbar>
        </AppBar>
        <Box component="main" sx={{ px: { xs: 2, md: 4 }, py: 3, maxWidth: 1600 }}>
          {children}
        </Box>
      </Box>
    </Box>
  );
}
