import {
  Alert,
  Box,
  Button,
  Chip,
  CircularProgress,
  MenuItem,
  Pagination,
  Paper,
  Stack,
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableRow,
  TextField,
  Typography,
} from '@mui/material';
import OpenInNewIcon from '@mui/icons-material/OpenInNew';
import RefreshIcon from '@mui/icons-material/Refresh';
import { useQuery } from '@tanstack/react-query';
import { useEffect, useState } from 'react';
import { Link } from 'react-router';

import { getRecruiters } from '../api';

function parsePageSize(value: string): number {
  const parsed = Number.parseInt(value, 10);
  return Number.isFinite(parsed) ? parsed : 25;
}

export function RecruitersPage() {
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(25);
  const [search, setSearch] = useState('');
  const [company, setCompany] = useState('');
  const [location, setLocation] = useState('Bengaluru');

  useEffect(() => {
    setPage(1);
  }, [pageSize, search, company, location]);

  const recruitersQuery = useQuery({
    queryKey: ['recruiters', page, pageSize, search, company, location],
    queryFn: () =>
      getRecruiters({
        page,
        pageSize,
        search: search || undefined,
        company: company || undefined,
        location: location || undefined,
      }),
    retry: 1,
  });

  const recruiters = Array.isArray(recruitersQuery.data?.items) ? recruitersQuery.data.items : [];

  return (
    <Stack spacing={3}>
      <Box>
        <Typography variant="h4" sx={{ fontWeight: 700 }}>
          Recruiters
        </Typography>
        <Typography color="text.secondary">
          Recruiters and HR contacts with the jobs they map to
        </Typography>
      </Box>

      <Paper variant="outlined" sx={{ p: 2 }}>
        <Stack spacing={2}>
          <Stack direction={{ xs: 'column', md: 'row' }} spacing={2}>
            <TextField label="Search" value={search} onChange={(event) => setSearch(event.target.value)} fullWidth />
            <TextField label="Company" value={company} onChange={(event) => setCompany(event.target.value)} fullWidth />
            <TextField label="Location" value={location} onChange={(event) => setLocation(event.target.value)} fullWidth />
            <TextField
              label="Page size"
              value={pageSize}
              onChange={(event) => setPageSize(parsePageSize(event.target.value))}
              select
            >
              {[10, 25, 50, 100].map((option) => (
                <MenuItem key={option} value={option}>
                  {option}
                </MenuItem>
              ))}
            </TextField>
          </Stack>
          <Stack direction="row" spacing={1} alignItems="center">
            <Button
              variant="outlined"
              startIcon={<RefreshIcon />}
              onClick={() => recruitersQuery.refetch()}
              disabled={recruitersQuery.isFetching}
            >
              Refresh
            </Button>
            <Typography variant="body2" color="text.secondary">
              {recruitersQuery.data?.total ?? 0} recruiters total
            </Typography>
            <Typography variant="body2" color="text.secondary">
              Page {recruitersQuery.data?.page ?? 1} of {recruitersQuery.data?.total_pages ?? 0}
            </Typography>
          </Stack>
        </Stack>
      </Paper>

      {recruitersQuery.isLoading && <CircularProgress size={24} />}
      {recruitersQuery.isError && <Alert severity="error">Unable to load recruiters.</Alert>}

      {!recruitersQuery.isLoading && !recruitersQuery.isError && recruiters.length === 0 && (
        <Alert severity="info">No recruiters matched the selected filters.</Alert>
      )}

      {recruiters.length > 0 && (
        <Paper variant="outlined" sx={{ overflow: 'hidden' }}>
          <Table size="small">
            <TableHead>
              <TableRow>
                <TableCell>Recruiter</TableCell>
                <TableCell width={170}>Company</TableCell>
                <TableCell width={220}>Contact</TableCell>
                <TableCell>Jobs</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {recruiters.map((recruiter) => (
                <TableRow key={recruiter.id} hover sx={{ verticalAlign: 'top' }}>
                  <TableCell>
                    <Typography variant="subtitle2" sx={{ fontWeight: 700 }}>
                      {recruiter.full_name}
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                      {recruiter.title ?? 'Recruiter / HR'}
                    </Typography>
                    {recruiter.notes && (
                      <Typography variant="body2" color="text.secondary" sx={{ mt: 0.5 }}>
                        {recruiter.notes}
                      </Typography>
                    )}
                  </TableCell>
                  <TableCell>{recruiter.company ?? 'Unknown company'}</TableCell>
                  <TableCell>
                    <Stack spacing={0.5}>
                      {recruiter.email && <Typography variant="body2">{recruiter.email}</Typography>}
                      {recruiter.linkedin_url && (
                        <Button
                          component="a"
                          href={recruiter.linkedin_url}
                          target="_blank"
                          rel="noreferrer"
                          size="small"
                          startIcon={<OpenInNewIcon />}
                        >
                          LinkedIn
                        </Button>
                      )}
                    </Stack>
                  </TableCell>
                  <TableCell>
                    <Stack direction="row" spacing={1} useFlexGap flexWrap="wrap">
                      {recruiter.jobs.length > 0 ? (
                        recruiter.jobs.map((job) => (
                          <Chip
                            key={job.id}
                            label={`${job.title} | ${job.source}`}
                            component={Link}
                            to={`/jobs?jobId=${job.id}`}
                            clickable
                            variant="outlined"
                            sx={{ maxWidth: '100%' }}
                          />
                        ))
                      ) : (
                        <Chip label="No mapped jobs" variant="outlined" />
                      )}
                    </Stack>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </Paper>
      )}

      {recruitersQuery.data && recruitersQuery.data.total_pages > 1 && (
        <Stack direction="row" justifyContent="center">
          <Pagination
            count={recruitersQuery.data.total_pages}
            page={page}
            onChange={(_, nextPage) => setPage(nextPage)}
            color="primary"
          />
        </Stack>
      )}
    </Stack>
  );
}
