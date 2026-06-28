import {
  Alert,
  Avatar,
  Box,
  Button,
  Chip,
  Grid,
  LinearProgress,
  Paper,
  Stack,
  Typography,
} from '@mui/material';
import WorkOutlineIcon from '@mui/icons-material/WorkOutline';
import TrendingUpIcon from '@mui/icons-material/TrendingUp';
import HandshakeIcon from '@mui/icons-material/Handshake';
import TaskAltIcon from '@mui/icons-material/TaskAlt';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { Bar, BarChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts';
import { Link as RouterLink } from 'react-router';

import { getDashboardSummary, getJobSearchProfile, getServiceInfo, triggerJobDiscovery } from '../api';

export function DashboardPage() {
  const queryClient = useQueryClient();
  const serviceInfo = useQuery({ queryKey: ['service-info'], queryFn: getServiceInfo, retry: 1 });
  const jobSearchProfile = useQuery({
    queryKey: ['job-search-profile'],
    queryFn: getJobSearchProfile,
    retry: 1,
  });
  const dashboardSummary = useQuery({
    queryKey: ['dashboard-summary'],
    queryFn: getDashboardSummary,
    retry: 1,
  });
  const profile = jobSearchProfile.data;
  const summary = dashboardSummary.data;
  const discoveryMutation = useMutation({
    mutationFn: triggerJobDiscovery,
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ['dashboard-summary'] });
      await queryClient.invalidateQueries({ queryKey: ['jobs'] });
      await queryClient.invalidateQueries({ queryKey: ['companies'] });
    },
  });
  const statCards = [
    { label: 'Jobs Found', value: summary?.jobs_found ?? 0 },
    { label: 'Applied', value: summary?.applied ?? 0 },
    { label: 'Interviews', value: summary?.interviews ?? 0 },
    { label: 'Offers', value: summary?.offers ?? 0 },
  ];
  const funnelData = summary?.funnel ?? [
    { name: 'Found', value: 0 },
    { name: 'Saved', value: 0 },
    { name: 'Applied', value: 0 },
    { name: 'Interview', value: 0 },
    { name: 'Offer', value: 0 },
  ];

  return (
    <Stack spacing={3}>
      <Paper variant="outlined" sx={{ p: 2.5 }}>
        <Stack direction={{ xs: 'column', md: 'row' }} spacing={2} justifyContent="space-between" alignItems="center">
          <Box>
            <Chip label="Live dashboard" size="small" color="primary" sx={{ mb: 1 }} />
            <Typography variant="h4" sx={{ fontWeight: 800 }}>
              Dashboard
            </Typography>
            <Typography color="text.secondary">
              Pipeline overview, search status, and the latest discovery run.
            </Typography>
          </Box>
          <Stack direction="row" spacing={1} flexWrap="wrap">
            <Button variant="contained" onClick={() => discoveryMutation.mutate()} disabled={discoveryMutation.isPending}>
              {discoveryMutation.isPending ? 'Queueing discovery...' : 'Run discovery'}
            </Button>
            <Button variant="outlined" component={RouterLink} to="/jobs">
              View jobs
            </Button>
          </Stack>
        </Stack>
      </Paper>

      {(serviceInfo.isLoading || jobSearchProfile.isLoading || dashboardSummary.isLoading) && <LinearProgress />}
      {serviceInfo.isError && (
        <Alert severity="warning">Backend status is unavailable. Confirm the API container is running.</Alert>
      )}
      {jobSearchProfile.isError && (
        <Alert severity="warning">Target profile is unavailable until the profile endpoint is reachable.</Alert>
      )}
      {dashboardSummary.isError && (
        <Alert severity="warning">Dashboard metrics are unavailable until the API and database are ready.</Alert>
      )}
      {serviceInfo.data && (
        <Alert severity="success">
          {serviceInfo.data.name} API is online in {serviceInfo.data.environment} mode.
        </Alert>
      )}
      {discoveryMutation.data && (
        <Alert severity="success">Discovery queued: {discoveryMutation.data.task_id}</Alert>
      )}

      {profile && (
        <Paper variant="outlined" sx={{ p: 2.5 }}>
          <Stack direction={{ xs: 'column', lg: 'row' }} spacing={3} justifyContent="space-between" alignItems="flex-start">
            <Box flex={1}>
              <Typography variant="overline" color="text.secondary">
                Active profile
              </Typography>
              <Typography variant="h6" sx={{ fontWeight: 800 }}>
                {profile.full_name}
              </Typography>
              <Typography color="text.secondary" sx={{ mt: 0.5 }}>
                {profile.target_years_experience}+ YOE, focused on {profile.target_job_titles.join(', ')}.
              </Typography>
              <Typography variant="body2" sx={{ mt: 1, wordBreak: 'break-all' }} color="text.secondary">
                Resume: {profile.resume_path}
              </Typography>
            </Box>
            <Stack direction="row" spacing={1} flexWrap="wrap">
              {profile.target_job_locations.map((location) => (
                <Chip key={location} label={location} variant="outlined" />
              ))}
            </Stack>
          </Stack>
        </Paper>
      )}

      <Grid container spacing={2}>
        {statCards.map((card) => (
          <Grid key={card.label} size={{ xs: 12, sm: 6, lg: 3 }}>
            <Paper variant="outlined" sx={{ p: 2, minHeight: 108 }}>
              <Stack direction="row" spacing={2} alignItems="center">
                <Avatar sx={{ bgcolor: 'primary.main' }}>
                  {card.label === 'Jobs Found' ? <WorkOutlineIcon /> : card.label === 'Applied' ? <TaskAltIcon /> : card.label === 'Interviews' ? <HandshakeIcon /> : <TrendingUpIcon />}
                </Avatar>
                <Box>
                  <Typography variant="body2" color="text.secondary">
                    {card.label}
                  </Typography>
                  <Typography variant="h4" sx={{ mt: 0.25, fontWeight: 800 }}>
                    {card.value}
                  </Typography>
                </Box>
              </Stack>
            </Paper>
          </Grid>
        ))}
      </Grid>

      <Grid container spacing={2}>
        <Grid size={{ xs: 12, lg: 7 }}>
          <Paper variant="outlined" sx={{ p: 2, height: 360 }}>
            <Typography variant="h6" sx={{ mb: 1.5, fontWeight: 700 }}>
              Application Funnel
            </Typography>
            <ResponsiveContainer width="100%" height="88%">
              <BarChart data={funnelData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="name" />
                <YAxis allowDecimals={false} />
                <Tooltip />
                <Bar dataKey="value" fill="#177e89" radius={[6, 6, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </Paper>
        </Grid>
        <Grid size={{ xs: 12, lg: 5 }}>
          <Paper variant="outlined" sx={{ p: 2, height: 360 }}>
            <Typography variant="h6" sx={{ mb: 1.5, fontWeight: 700 }}>
              Progress
            </Typography>
            <Stack spacing={1.5}>
              {funnelData.map((point) => (
                <Box key={point.name}>
                  <Stack direction="row" justifyContent="space-between" sx={{ mb: 0.5 }}>
                    <Typography variant="body2" color="text.secondary">
                      {point.name}
                    </Typography>
                    <Typography variant="body2" sx={{ fontWeight: 700 }}>
                      {point.value}
                    </Typography>
                  </Stack>
                  <LinearProgress
                    variant="determinate"
                    value={summary?.jobs_found ? (point.value / summary.jobs_found) * 100 : 0}
                    sx={{ height: 8, borderRadius: 999 }}
                  />
                </Box>
              ))}
            </Stack>
          </Paper>
        </Grid>
      </Grid>
    </Stack>
  );
}
