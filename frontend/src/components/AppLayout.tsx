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
    <Box sx={{ display: 'flex', minHeight: '100vh' }}>
      <Box
        component="aside"
        sx={{
          width: 260,
          borderRight: 1,
          borderColor: 'divider',
          display: { xs: 'none', md: 'block' },
          flexShrink: 0,
        }}
      >
        <Toolbar>
          <Typography variant="h6" noWrap>
            Job Search Agent
          </Typography>
        </Toolbar>
        <Divider />
        <List dense>
          {navItems.map((item) => (
            <ListItemButton
              key={item.path}
              component={Link}
              to={item.path}
              selected={location.pathname === item.path}
              sx={{ minHeight: 44 }}
            >
              <ListItemIcon sx={{ minWidth: 40 }}>{item.icon}</ListItemIcon>
              <ListItemText primary={item.label} />
            </ListItemButton>
          ))}
        </List>
      </Box>

      <Box sx={{ flex: 1, minWidth: 0 }}>
        <AppBar position="sticky" color="default" elevation={0} sx={{ borderBottom: 1, borderColor: 'divider' }}>
          <Toolbar sx={{ gap: 2 }}>
            <TextField
              size="small"
              placeholder="Search"
              sx={{ maxWidth: 420, flex: 1 }}
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
            <Switch checked={darkMode} onChange={onToggleDarkMode} inputProps={{ 'aria-label': 'Dark mode' }} />
            <IconButton component={Link} to="/settings" aria-label="Settings">
              <SettingsIcon />
            </IconButton>
          </Toolbar>
        </AppBar>
        <Box component="main" sx={{ px: { xs: 2, md: 4 }, py: 3 }}>
          {children}
        </Box>
      </Box>
    </Box>
  );
}
