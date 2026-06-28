import {
  Alert,
  Box,
  Button,
  Chip,
  CircularProgress,
  Collapse,
  Divider,
  FormControl,
  IconButton,
  InputLabel,
  Link,
  MenuItem,
  Paper,
  Pagination,
  Select,
  Slider,
  Stack,
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableRow,
  TextField,
  Typography,
} from '@mui/material';
import LinkIcon from '@mui/icons-material/Link';
import OpenInNewIcon from '@mui/icons-material/OpenInNew';
import RefreshIcon from '@mui/icons-material/Refresh';
import { useQuery } from '@tanstack/react-query';
import { Fragment, useEffect, useMemo, useState } from 'react';
import { Link as RouterLink, useSearchParams } from 'react-router';

import { getJobs } from '../api';

function scoreColor(score?: number | null): 'default' | 'success' | 'warning' {
  if (typeof score !== 'number') {
    return 'default';
  }
  if (score >= 75) {
    return 'success';
  }
  if (score >= 45) {
    return 'warning';
  }
  return 'default';
}

function parseOptionalInt(value: string): number | null {
  if (!value.trim()) {
    return null;
  }
  const parsed = Number.parseInt(value, 10);
  return Number.isFinite(parsed) ? parsed : null;
}

export function JobsPage() {
  const [searchParams, setSearchParams] = useSearchParams();
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(25);
  const [sortBy, setSortBy] = useState('score');
  const [sortDir, setSortDir] = useState<'asc' | 'desc'>('desc');
  const [search, setSearch] = useState('');
  const [location, setLocation] = useState('Bengaluru');
  const [company, setCompany] = useState('');
  const [companyTypes, setCompanyTypes] = useState<string[]>([]);
  const [remoteOnly, setRemoteOnly] = useState<'all' | 'yes' | 'no'>('all');
  const [minApplicants, setMinApplicants] = useState('');
  const [maxApplicants, setMaxApplicants] = useState('');
  const [skillWeight, setSkillWeight] = useState(50);
  const [recencyWeight, setRecencyWeight] = useState(30);
  const [applicantWeight, setApplicantWeight] = useState(20);

  const selectedJobId = searchParams.get('jobId');

  useEffect(() => {
    setPage(1);
  }, [search, location, company, companyTypes, remoteOnly, minApplicants, maxApplicants, sortBy, sortDir, pageSize]);

  const jobsQuery = useQuery({
    queryKey: [
      'jobs',
      page,
      pageSize,
      sortBy,
      sortDir,
      search,
      location,
      company,
      companyTypes,
      remoteOnly,
      minApplicants,
      maxApplicants,
      skillWeight,
      recencyWeight,
      applicantWeight,
    ],
    queryFn: () =>
      getJobs({
        page,
        pageSize,
        sortBy,
        sortDir,
        search: search || undefined,
        location: location || undefined,
        company: company || undefined,
        companyType: companyTypes,
        remoteOnly: remoteOnly === 'all' ? null : remoteOnly === 'yes',
        minApplicants: parseOptionalInt(minApplicants),
        maxApplicants: parseOptionalInt(maxApplicants),
        skillWeight,
        recencyWeight,
        applicantWeight,
      }),
    retry: 1,
  });

  const jobs = Array.isArray(jobsQuery.data?.items) ? jobsQuery.data.items : [];
  const selectedJob = useMemo(
    () => jobs.find((job) => job.id === selectedJobId) ?? jobs[0] ?? null,
    [jobs, selectedJobId],
  );

  useEffect(() => {
    if (jobs.length === 0) {
      return;
    }
    if (selectedJobId && jobs.some((job) => job.id === selectedJobId)) {
      return;
    }
    const next = new URLSearchParams(searchParams);
    next.set('jobId', jobs[0].id);
    setSearchParams(next, { replace: true });
  }, [jobs, selectedJobId, searchParams, setSearchParams]);

  return (
    <Stack spacing={3}>
      <Box>
        <Typography variant="h4" sx={{ fontWeight: 700 }}>
          Jobs
        </Typography>
        <Typography color="text.secondary">
          Filtered, paginated, and ranked discoveries with adjustable score weights
        </Typography>
      </Box>

      <Paper variant="outlined" sx={{ p: 2 }}>
        <Stack spacing={2}>
          <Stack direction={{ xs: 'column', md: 'row' }} spacing={2}>
            <TextField label="Search" value={search} onChange={(event) => setSearch(event.target.value)} fullWidth />
            <TextField label="Location" value={location} onChange={(event) => setLocation(event.target.value)} fullWidth />
            <TextField label="Company" value={company} onChange={(event) => setCompany(event.target.value)} fullWidth />
            <FormControl fullWidth>
              <InputLabel id="sort-by-label">Sort by</InputLabel>
              <Select
                labelId="sort-by-label"
                label="Sort by"
                value={sortBy}
                onChange={(event) => setSortBy(event.target.value)}
              >
                <MenuItem value="score">Score</MenuItem>
                <MenuItem value="recency">Recency</MenuItem>
                <MenuItem value="title">Title</MenuItem>
                <MenuItem value="company">Company</MenuItem>
                <MenuItem value="applicants">Applicants</MenuItem>
              </Select>
            </FormControl>
            <FormControl fullWidth>
              <InputLabel id="sort-dir-label">Direction</InputLabel>
              <Select
                labelId="sort-dir-label"
                label="Direction"
                value={sortDir}
                onChange={(event) => setSortDir(event.target.value as 'asc' | 'desc')}
              >
                <MenuItem value="desc">Descending</MenuItem>
                <MenuItem value="asc">Ascending</MenuItem>
              </Select>
            </FormControl>
          </Stack>

          <Stack direction={{ xs: 'column', md: 'row' }} spacing={2}>
            <FormControl fullWidth>
              <InputLabel id="company-type-label">Company type</InputLabel>
              <Select<string[]>
                multiple
                labelId="company-type-label"
                label="Company type"
                value={companyTypes}
                onChange={(event) => {
                  const value = event.target.value;
                  setCompanyTypes(typeof value === 'string' ? value.split(',') : value);
                }}
                renderValue={(selected: string[]) => (selected.length > 0 ? selected.join(', ') : 'All types')}
              >
                <MenuItem value="mnc">MNC</MenuItem>
                <MenuItem value="startup">Startup</MenuItem>
                <MenuItem value="unknown">Unknown</MenuItem>
              </Select>
            </FormControl>
            <FormControl fullWidth>
              <InputLabel id="remote-only-label">Remote filter</InputLabel>
              <Select
                labelId="remote-only-label"
                label="Remote filter"
                value={remoteOnly}
                onChange={(event) => setRemoteOnly(event.target.value as 'all' | 'yes' | 'no')}
              >
                <MenuItem value="all">All jobs</MenuItem>
                <MenuItem value="yes">Remote only</MenuItem>
                <MenuItem value="no">Non-remote only</MenuItem>
              </Select>
            </FormControl>
            <TextField
              label="Min applicants"
              value={minApplicants}
              onChange={(event) => setMinApplicants(event.target.value)}
              inputMode="numeric"
            />
            <TextField
              label="Max applicants"
              value={maxApplicants}
              onChange={(event) => setMaxApplicants(event.target.value)}
              inputMode="numeric"
            />
            <TextField
              label="Page size"
              value={pageSize}
              onChange={(event) => setPageSize(Number(event.target.value) || 25)}
              select
            >
              {[10, 25, 50, 100].map((option) => (
                <MenuItem key={option} value={option}>
                  {option}
                </MenuItem>
              ))}
            </TextField>
          </Stack>

          <Divider />

          <Stack spacing={2}>
            <Box>
              <Typography variant="subtitle2" sx={{ mb: 1 }}>
                Ranking weights
              </Typography>
              <Stack spacing={2}>
                <Box>
                  <Typography variant="body2">Skill match: {skillWeight}</Typography>
                  <Slider value={skillWeight} onChange={(_, value) => setSkillWeight(value as number)} min={0} max={100} />
                </Box>
                <Box>
                  <Typography variant="body2">Recency: {recencyWeight}</Typography>
                  <Slider value={recencyWeight} onChange={(_, value) => setRecencyWeight(value as number)} min={0} max={100} />
                </Box>
                <Box>
                  <Typography variant="body2">Applicants: {applicantWeight}</Typography>
                  <Slider value={applicantWeight} onChange={(_, value) => setApplicantWeight(value as number)} min={0} max={100} />
                </Box>
              </Stack>
            </Box>
            <Stack direction="row" spacing={1} alignItems="center">
              <Button
                variant="outlined"
                startIcon={<RefreshIcon />}
                onClick={() => jobsQuery.refetch()}
                disabled={jobsQuery.isFetching}
              >
                Refresh
              </Button>
              <Typography variant="body2" color="text.secondary">
                {jobsQuery.data?.total ?? 0} jobs total
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Page {jobsQuery.data?.page ?? 1} of {jobsQuery.data?.total_pages ?? 0}
              </Typography>
            </Stack>
          </Stack>
        </Stack>
      </Paper>

      {jobsQuery.isLoading && <CircularProgress size={24} />}
      {jobsQuery.isError && <Alert severity="error">Unable to load jobs from the API.</Alert>}

      {!jobsQuery.isLoading && !jobsQuery.isError && jobs.length === 0 && (
        <Alert severity="info">No jobs matched the selected filters.</Alert>
      )}

      {jobs.length > 0 && (
        <Paper variant="outlined" sx={{ overflow: 'hidden' }}>
          <Table size="small">
            <TableHead>
              <TableRow>
                <TableCell width={72}>Rank</TableCell>
                <TableCell width={90}>Score</TableCell>
                <TableCell>Role</TableCell>
                <TableCell width={170}>Company</TableCell>
                <TableCell width={170}>Location</TableCell>
                <TableCell width={120}>Applicants</TableCell>
                <TableCell width={110}>Type</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {jobs.map((job) => {
                const isSelected = selectedJob?.id === job.id;
                return (
                  <Fragment key={job.id}>
                    <TableRow
                      hover
                      selected={isSelected}
                      onClick={() => {
                        const next = new URLSearchParams(searchParams);
                        next.set('jobId', job.id);
                        setSearchParams(next, { replace: true });
                      }}
                      sx={{ cursor: 'pointer', verticalAlign: 'top' }}
                    >
                      <TableCell>{job.rank ?? '-'}</TableCell>
                      <TableCell>
                        <Chip label={job.score ?? '-'} color={scoreColor(job.score)} size="small" />
                      </TableCell>
                      <TableCell>
                        <Stack direction="row" spacing={1} alignItems="center">
                          <Box>
                            <Typography variant="subtitle2" sx={{ fontWeight: 700 }}>
                              {job.title}
                            </Typography>
                            <Typography variant="body2" color="text.secondary">
                              {job.reasons.join(' · ') || 'No scoring notes'}
                            </Typography>
                          </Box>
                          <IconButton
                            size="small"
                            component={RouterLink}
                            to={`/jobs?jobId=${job.id}`}
                            onClick={(event) => {
                              event.stopPropagation();
                            }}
                          >
                            <LinkIcon fontSize="small" />
                          </IconButton>
                        </Stack>
                      </TableCell>
                      <TableCell>{job.company ?? 'Unknown'}</TableCell>
                      <TableCell>
                        <Stack spacing={0.5}>
                          <span>{job.location ?? 'Not listed'}</span>
                          {job.remote && (
                            <Chip label={job.remote} size="small" variant="outlined" sx={{ width: 'fit-content' }} />
                          )}
                        </Stack>
                      </TableCell>
                      <TableCell>{job.applicant_count ?? 'N/A'}</TableCell>
                      <TableCell>{job.company_type ?? 'unknown'}</TableCell>
                    </TableRow>
                    <TableRow>
                      <TableCell colSpan={7} sx={{ py: 0, borderBottom: isSelected ? 'none' : undefined }}>
                        <Collapse in={isSelected} timeout="auto" unmountOnExit>
                          <Box sx={{ py: 2 }}>
                            <Stack direction="row" spacing={1} flexWrap="wrap" sx={{ mb: 2 }}>
                              <Chip label={`Job ID ${job.id}`} variant="outlined" />
                              <Chip label={`Rank ${job.rank ?? '-'}`} />
                              <Chip label={`Score ${job.score ?? '-'}`} color={scoreColor(job.score)} />
                              <Button
                                component={Link}
                                href={job.source_url}
                                target="_blank"
                                rel="noreferrer"
                                variant="contained"
                                startIcon={<OpenInNewIcon />}
                              >
                                Apply
                              </Button>
                            </Stack>
                            <Stack direction={{ xs: 'column', md: 'row' }} spacing={2}>
                              <Box flex={1}>
                                <Typography variant="subtitle2" sx={{ mb: 1 }}>
                                  Why it matched
                                </Typography>
                                <Stack direction="row" spacing={1} useFlexGap flexWrap="wrap">
                                  {job.reasons.length > 0 ? (
                                    job.reasons.map((reason) => <Chip key={reason} label={reason} />)
                                  ) : (
                                    <Chip label="No reasons recorded" />
                                  )}
                                </Stack>
                              </Box>
                              <Box flex={1}>
                                <Typography variant="subtitle2" sx={{ mb: 1 }}>
                                  Keywords
                                </Typography>
                                <Stack direction="row" spacing={1} useFlexGap flexWrap="wrap">
                                  {job.matched_keywords.length > 0 ? (
                                    job.matched_keywords.map((keyword) => (
                                      <Chip key={keyword} label={keyword} variant="outlined" />
                                    ))
                                  ) : (
                                    <Chip label="None detected" variant="outlined" />
                                  )}
                                </Stack>
                              </Box>
                            </Stack>
                            <Box sx={{ mt: 2 }}>
                              <Typography variant="subtitle2" sx={{ mb: 1 }}>
                                Details
                              </Typography>
                              <Typography variant="body2" sx={{ whiteSpace: 'pre-wrap' }}>
                                {job.description ?? 'No description captured for this job.'}
                              </Typography>
                            </Box>
                            <Box sx={{ mt: 2 }}>
                              <Typography variant="subtitle2" sx={{ mb: 1 }}>
                                HR contacts
                              </Typography>
                              <Stack spacing={1}>
                                {job.contacts.length > 0 ? (
                                  job.contacts.map((contact) => (
                                    <Paper
                                      key={`${contact.full_name}-${contact.email ?? contact.linkedin_url ?? ''}`}
                                      variant="outlined"
                                      sx={{ p: 1.5 }}
                                    >
                                      <Typography variant="body2" sx={{ fontWeight: 700 }}>
                                        {contact.full_name}
                                      </Typography>
                                      <Typography variant="body2" color="text.secondary">
                                        {contact.title ?? 'Contact'}
                                        {contact.email ? ` | ${contact.email}` : ''}
                                        {contact.linkedin_url ? ` | ${contact.linkedin_url}` : ''}
                                      </Typography>
                                      {contact.notes && (
                                        <Typography variant="body2" color="text.secondary" sx={{ mt: 0.5 }}>
                                          {contact.notes}
                                        </Typography>
                                      )}
                                    </Paper>
                                  ))
                                ) : (
                                  <Typography variant="body2" color="text.secondary">
                                    No contacts captured for this job yet.
                                  </Typography>
                                )}
                              </Stack>
                            </Box>
                          </Box>
                        </Collapse>
                      </TableCell>
                    </TableRow>
                  </Fragment>
                );
              })}
            </TableBody>
          </Table>
        </Paper>
      )}

      {jobsQuery.data && jobsQuery.data.total_pages > 1 && (
        <Stack direction="row" justifyContent="center">
          <Pagination
            count={jobsQuery.data.total_pages}
            page={page}
            onChange={(_, nextPage) => setPage(nextPage)}
            color="primary"
          />
        </Stack>
      )}
    </Stack>
  );
}
