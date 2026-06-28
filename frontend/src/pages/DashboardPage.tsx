import { Alert, Box, Button, Grid, LinearProgress, Paper, Stack, Typography } from '@mui/material';
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
      <Box>
        <Typography variant="h4" sx={{ fontWeight: 700 }}>
          Dashboard
        </Typography>
        <Typography color="text.secondary">
          Pipeline overview and system status
        </Typography>
      </Box>

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
      <Box>
        <Button
          variant="contained"
          onClick={() => discoveryMutation.mutate()}
          disabled={discoveryMutation.isPending}
        >
          {discoveryMutation.isPending ? 'Queueing discovery...' : 'Run discovery'}
        </Button>
        <Button variant="text" sx={{ ml: 1 }} component={RouterLink} to="/jobs">
          View jobs
        </Button>
        {discoveryMutation.data && (
          <Typography variant="body2" sx={{ mt: 1 }} color="text.secondary">
            Discovery queued: {discoveryMutation.data.task_id}
          </Typography>
        )}
      </Box>

      {profile && (
        <Paper variant="outlined" sx={{ p: 2 }}>
          <Typography variant="overline" color="text.secondary">
            Active profile
          </Typography>
          <Typography variant="h6" sx={{ fontWeight: 700 }}>
            {profile.full_name}
          </Typography>
          <Typography color="text.secondary" sx={{ mt: 0.5 }}>
            {profile.target_years_experience}+ YOE | {profile.target_job_titles.join(' / ')} |{' '}
            {profile.target_job_locations.join(' / ')}
          </Typography>
          <Typography variant="body2" sx={{ mt: 1 }}>
            Resume: {profile.resume_path}
          </Typography>
        </Paper>
      )}

      <Grid container spacing={2}>
        {statCards.map((card) => (
          <Grid key={card.label} size={{ xs: 12, sm: 6, lg: 3 }}>
            <Paper variant="outlined" sx={{ p: 2 }}>
              <Typography variant="body2" color="text.secondary">
                {card.label}
              </Typography>
              <Typography variant="h4" sx={{ mt: 1, fontWeight: 700 }}>
                {card.value}
              </Typography>
            </Paper>
          </Grid>
        ))}
      </Grid>

      <Paper variant="outlined" sx={{ p: 2, height: 360 }}>
        <Typography variant="h6" sx={{ mb: 2 }}>
          Application Funnel
        </Typography>
        <ResponsiveContainer width="100%" height="85%">
          <BarChart data={funnelData}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="name" />
            <YAxis allowDecimals={false} />
            <Tooltip />
            <Bar dataKey="value" fill="#1f7a8c" radius={[4, 4, 0, 0]} />
          </BarChart>
        </ResponsiveContainer>
      </Paper>
    </Stack>
  );
}
