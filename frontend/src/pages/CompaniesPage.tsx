import {
  Alert,
  Box,
  Button,
  Chip,
  CircularProgress,
  Collapse,
  Divider,
  FormControl,
  InputLabel,
  MenuItem,
  Pagination,
  Paper,
  Select,
  Stack,
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableRow,
  TextField,
  Typography,
} from '@mui/material';
import RefreshIcon from '@mui/icons-material/Refresh';
import { useQuery } from '@tanstack/react-query';
import { Fragment, useEffect, useMemo, useState } from 'react';
import { Link } from 'react-router';

import { getCompanies, getJobs, getRecruiters } from '../api';

function parsePageSize(value: string): number {
  const parsed = Number.parseInt(value, 10);
  return Number.isFinite(parsed) ? parsed : 25;
}

export function CompaniesPage() {
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(25);
  const [sortBy, setSortBy] = useState('job_count');
  const [sortDir, setSortDir] = useState<'asc' | 'desc'>('desc');
  const [search, setSearch] = useState('');
  const [location, setLocation] = useState('Bengaluru');
  const [companyTypes, setCompanyTypes] = useState<string[]>([]);
  const [selectedCompany, setSelectedCompany] = useState<string | null>(null);
  const [companyJobsPage, setCompanyJobsPage] = useState(1);
  const [companyRecruitersPage, setCompanyRecruitersPage] = useState(1);

  useEffect(() => {
    setPage(1);
  }, [pageSize, sortBy, sortDir, search, location, companyTypes]);

  const companiesQuery = useQuery({
    queryKey: ['companies', page, pageSize, sortBy, sortDir, search, location, companyTypes],
    queryFn: () =>
      getCompanies({
        page,
        pageSize,
        sortBy,
        sortDir,
        search: search || undefined,
        location: location || undefined,
        companyType: companyTypes,
      }),
    retry: 1,
  });

  const companies = Array.isArray(companiesQuery.data?.items) ? companiesQuery.data.items : [];

  useEffect(() => {
    if (companies.length === 0) {
      setSelectedCompany(null);
      return;
    }
    if (!selectedCompany || !companies.some((company) => company.company === selectedCompany)) {
      setSelectedCompany(companies[0].company);
    }
  }, [companies, selectedCompany]);

  useEffect(() => {
    setCompanyJobsPage(1);
    setCompanyRecruitersPage(1);
  }, [selectedCompany]);

  const selectedCompanyName = selectedCompany ?? companies[0]?.company ?? null;

  const companyJobsQuery = useQuery({
    queryKey: ['company-jobs', selectedCompanyName, companyJobsPage, location, search, companyTypes],
    queryFn: () =>
      getJobs({
        page: companyJobsPage,
        pageSize: 10,
        search: search || undefined,
        location: location || undefined,
        company: selectedCompanyName || undefined,
        companyType: companyTypes,
      }),
    enabled: Boolean(selectedCompanyName),
    retry: 1,
  });

  const companyRecruitersQuery = useQuery({
    queryKey: ['company-recruiters', selectedCompanyName, companyRecruitersPage, location, search, companyTypes],
    queryFn: () =>
      getRecruiters({
        page: companyRecruitersPage,
        pageSize: 10,
        search: search || undefined,
        location: location || undefined,
        company: selectedCompanyName || undefined,
        companyType: companyTypes,
      }),
    enabled: Boolean(selectedCompanyName),
    retry: 1,
  });

  const companyJobs = Array.isArray(companyJobsQuery.data?.items) ? companyJobsQuery.data.items : [];
  const companyRecruiters = Array.isArray(companyRecruitersQuery.data?.items)
    ? companyRecruitersQuery.data.items
    : [];

  const selectedCompanySummary = useMemo(
    () => companies.find((company) => company.company === selectedCompanyName) ?? null,
    [companies, selectedCompanyName],
  );

  return (
    <Stack spacing={3}>
      <Box>
        <Typography variant="h4" sx={{ fontWeight: 700 }}>
          Companies
        </Typography>
        <Typography color="text.secondary">
          Grouped company rollups with drill-down jobs and recruiter contacts
        </Typography>
      </Box>

      <Paper variant="outlined" sx={{ p: 2 }}>
        <Stack spacing={2}>
          <Stack direction={{ xs: 'column', md: 'row' }} spacing={2}>
            <TextField label="Search company" value={search} onChange={(event) => setSearch(event.target.value)} fullWidth />
            <TextField label="Location" value={location} onChange={(event) => setLocation(event.target.value)} fullWidth />
            <FormControl fullWidth>
              <InputLabel id="company-type-filter-label">Company type</InputLabel>
              <Select<string[]>
                multiple
                labelId="company-type-filter-label"
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
              <InputLabel id="company-sort-by-label">Sort by</InputLabel>
              <Select
                labelId="company-sort-by-label"
                label="Sort by"
                value={sortBy}
                onChange={(event) => setSortBy(event.target.value)}
              >
                <MenuItem value="job_count">Job count</MenuItem>
                <MenuItem value="score">Score</MenuItem>
                <MenuItem value="latest_job_at">Latest job</MenuItem>
                <MenuItem value="avg_applicants">Avg applicants</MenuItem>
              </Select>
            </FormControl>
            <FormControl fullWidth>
              <InputLabel id="company-sort-dir-label">Direction</InputLabel>
              <Select
                labelId="company-sort-dir-label"
                label="Direction"
                value={sortDir}
                onChange={(event) => setSortDir(event.target.value as 'asc' | 'desc')}
              >
                <MenuItem value="desc">Descending</MenuItem>
                <MenuItem value="asc">Ascending</MenuItem>
              </Select>
            </FormControl>
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
            <Chip label={`${companiesQuery.data?.total ?? 0} companies`} />
            <Chip
              label={`Page ${companiesQuery.data?.page ?? 1} of ${companiesQuery.data?.total_pages ?? 0}`}
              variant="outlined"
            />
            <Button
              variant="outlined"
              startIcon={<RefreshIcon />}
              onClick={() => companiesQuery.refetch()}
              disabled={companiesQuery.isFetching}
            >
              Refresh
            </Button>
          </Stack>
        </Stack>
      </Paper>

      {companiesQuery.isLoading && <CircularProgress size={24} />}
      {companiesQuery.isError && <Alert severity="error">Unable to load company rollups.</Alert>}

      {!companiesQuery.isLoading && !companiesQuery.isError && companies.length === 0 && (
        <Alert severity="info">No companies matched the selected filters.</Alert>
      )}

      {companies.length > 0 && (
        <Paper variant="outlined" sx={{ overflow: 'hidden' }}>
          <Table size="small">
            <TableHead>
              <TableRow>
                <TableCell>Company</TableCell>
                <TableCell width={120}>Type</TableCell>
                <TableCell width={120}>Jobs</TableCell>
                <TableCell width={140}>Score</TableCell>
                <TableCell width={180}>Latest job</TableCell>
                <TableCell width={140}>Avg applicants</TableCell>
                <TableCell width={120}>Sources</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {companies.map((company) => {
                const isSelected = company.company === selectedCompanyName;
                return (
                  <Fragment key={company.company}>
                    <TableRow
                      hover
                      selected={isSelected}
                      onClick={() => setSelectedCompany(company.company)}
                      sx={{ cursor: 'pointer' }}
                    >
                      <TableCell>
                        <Typography variant="subtitle2" sx={{ fontWeight: 700 }}>
                          {company.company}
                        </Typography>
                      </TableCell>
                      <TableCell>{company.company_type ?? 'unknown'}</TableCell>
                      <TableCell>{company.job_count}</TableCell>
                      <TableCell>{company.score ?? '-'}</TableCell>
                      <TableCell>
                        {company.latest_job_at ? new Date(company.latest_job_at).toLocaleDateString() : 'Not listed'}
                      </TableCell>
                      <TableCell>{company.avg_applicants ?? 'N/A'}</TableCell>
                      <TableCell>{company.source_count ?? 0}</TableCell>
                    </TableRow>
                    <TableRow>
                      <TableCell colSpan={7} sx={{ py: 0, borderBottom: isSelected ? 'none' : undefined }}>
                        <Collapse in={isSelected} timeout="auto" unmountOnExit>
                          <Box sx={{ py: 2 }}>
                            <Stack spacing={1}>
                              <Typography variant="subtitle2">Selected company</Typography>
                              <Typography variant="body2" color="text.secondary">
                                {selectedCompanySummary?.company_type ?? 'unknown'} |{' '}
                                {selectedCompanySummary?.job_count ?? 0} jobs |{' '}
                                {selectedCompanySummary?.source_count ?? 0} sources
                              </Typography>
                              <Divider />

                              <Box>
                                <Typography variant="subtitle2" sx={{ mb: 1 }}>
                                  Jobs
                                </Typography>
                                {companyJobsQuery.isLoading ? (
                                  <CircularProgress size={20} />
                                ) : (
                                  <Paper variant="outlined" sx={{ overflow: 'hidden' }}>
                                    <Table size="small">
                                      <TableHead>
                                        <TableRow>
                                          <TableCell>Title</TableCell>
                                          <TableCell width={140}>Source</TableCell>
                                          <TableCell width={140}>Location</TableCell>
                                          <TableCell width={140}>Link</TableCell>
                                        </TableRow>
                                      </TableHead>
                                      <TableBody>
                                        {companyJobs.map((job) => (
                                          <TableRow key={job.id}>
                                            <TableCell>{job.title}</TableCell>
                                            <TableCell>{job.source}</TableCell>
                                            <TableCell>{job.location ?? 'Not listed'}</TableCell>
                                            <TableCell>
                                              <Button
                                                component={Link}
                                                to={`/jobs?jobId=${job.id}`}
                                                size="small"
                                                variant="outlined"
                                              >
                                                Job {job.id.slice(0, 8)}
                                              </Button>
                                            </TableCell>
                                          </TableRow>
                                        ))}
                                      </TableBody>
                                    </Table>
                                  </Paper>
                                )}
                                {companyJobsQuery.data && companyJobsQuery.data.total_pages > 1 && (
                                  <Stack direction="row" justifyContent="center" sx={{ mt: 1 }}>
                                    <Pagination
                                      count={companyJobsQuery.data.total_pages}
                                      page={companyJobsPage}
                                      onChange={(_, nextPage) => setCompanyJobsPage(nextPage)}
                                    />
                                  </Stack>
                                )}
                              </Box>

                              <Box>
                                <Typography variant="subtitle2" sx={{ mb: 1 }}>
                                  Recruiters
                                </Typography>
                                {companyRecruitersQuery.isLoading ? (
                                  <CircularProgress size={20} />
                                ) : (
                                  <Paper variant="outlined" sx={{ overflow: 'hidden' }}>
                                    <Table size="small">
                                      <TableHead>
                                        <TableRow>
                                          <TableCell>Recruiter</TableCell>
                                          <TableCell width={180}>Contact</TableCell>
                                          <TableCell>Jobs</TableCell>
                                        </TableRow>
                                      </TableHead>
                                      <TableBody>
                                        {companyRecruiters.map((recruiter) => (
                                          <TableRow key={recruiter.id}>
                                            <TableCell>
                                              <Typography variant="subtitle2" sx={{ fontWeight: 700 }}>
                                                {recruiter.full_name}
                                              </Typography>
                                              <Typography variant="body2" color="text.secondary">
                                                {recruiter.title ?? 'Recruiter / HR'}
                                              </Typography>
                                            </TableCell>
                                            <TableCell>
                                              <Typography variant="body2">{recruiter.email ?? 'No email'}</Typography>
                                            </TableCell>
                                            <TableCell>
                                              <Stack direction="row" spacing={1} useFlexGap flexWrap="wrap">
                                                {recruiter.jobs.length > 0 ? (
                                                  recruiter.jobs.map((job) => (
                                                    <Chip
                                                      key={job.id}
                                                      label={job.title}
                                                      component={Link}
                                                      to={`/jobs?jobId=${job.id}`}
                                                      clickable
                                                      variant="outlined"
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
                                {companyRecruitersQuery.data && companyRecruitersQuery.data.total_pages > 1 && (
                                  <Stack direction="row" justifyContent="center" sx={{ mt: 1 }}>
                                    <Pagination
                                      count={companyRecruitersQuery.data.total_pages}
                                      page={companyRecruitersPage}
                                      onChange={(_, nextPage) => setCompanyRecruitersPage(nextPage)}
                                    />
                                  </Stack>
                                )}
                              </Box>
                            </Stack>
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

      {companiesQuery.data && companiesQuery.data.total_pages > 1 && (
        <Stack direction="row" justifyContent="center">
          <Pagination
            count={companiesQuery.data.total_pages}
            page={page}
            onChange={(_, nextPage) => setPage(nextPage)}
            color="primary"
          />
        </Stack>
      )}
    </Stack>
  );
}
