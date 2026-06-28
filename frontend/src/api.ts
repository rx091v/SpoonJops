export type ServiceInfo = {
  name: string;
  environment: string;
  version: string;
};

export type FunnelPoint = {
  name: string;
  value: number;
};

export type DashboardSummary = {
  jobs_found: number;
  saved: number;
  applied: number;
  interviews: number;
  offers: number;
  rejected: number;
  funnel: FunnelPoint[];
};

export type JobDetail = {
  id: string;
  rank?: number | null;
  score?: number | null;
  skill_match_score?: number | null;
  recency_score?: number | null;
  applicant_count?: number | null;
  company_type?: string | null;
  company_score?: number | null;
  applicant_score?: number | null;
  source: string;
  company?: string | null;
  title: string;
  location?: string | null;
  remote?: string | null;
  source_url: string;
  matched_keywords: string[];
  reasons: string[];
  tailored_resume?: string | null;
  description?: string | null;
  discovered_at?: string | null;
  contacts: {
    full_name: string;
    title?: string | null;
    email?: string | null;
    linkedin_url?: string | null;
    notes?: string | null;
  }[];
};

export type JobLink = {
  id: string;
  title: string;
  source: string;
  source_url: string;
};

export type RecruiterDetail = {
  id: string;
  full_name: string;
  title?: string | null;
  email?: string | null;
  linkedin_url?: string | null;
  notes?: string | null;
  company?: string | null;
  company_id?: string | null;
  job_count: number;
  jobs: JobLink[];
};

export type JobPagination = {
  items: JobDetail[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
};

export type CompanySummary = {
  company: string;
  company_type?: string | null;
  job_count: number;
  score?: number | null;
  latest_job_at?: string | null;
  avg_applicants?: number | null;
  source_count?: number | null;
};

export type CompanyPagination = {
  items: CompanySummary[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
};

export type JobSearchProfile = {
  full_name: string;
  resume_path: string;
  target_job_titles: string[];
  target_job_locations: string[];
  target_job_remote_only: boolean;
  target_years_experience: number;
  target_keywords: string[];
};

const apiBaseUrl = import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000/api/v1';

function appendParams(
  params: URLSearchParams,
  key: string,
  value: string | number | boolean | null | undefined,
): void {
  if (value === undefined || value === null || value === '') {
    return;
  }
  params.set(key, String(value));
}

function appendRepeatedParams(params: URLSearchParams, key: string, values: string[] | undefined): void {
  if (!values) {
    return;
  }
  values.forEach((value) => {
    if (value) {
      params.append(key, value);
    }
  });
}

export type JobQuery = {
  page?: number;
  pageSize?: number;
  sortBy?: string;
  sortDir?: string;
  search?: string;
  location?: string;
  source?: string[];
  companyType?: string[];
  company?: string;
  remoteOnly?: boolean | null;
  minApplicants?: number | null;
  maxApplicants?: number | null;
  skillWeight?: number;
  recencyWeight?: number;
  applicantWeight?: number;
};

export type CompanyQuery = {
  page?: number;
  pageSize?: number;
  sortBy?: string;
  sortDir?: string;
  search?: string;
  source?: string[];
  companyType?: string[];
  location?: string;
};

export type RecruiterQuery = {
  page?: number;
  pageSize?: number;
  search?: string;
  location?: string;
  source?: string[];
  companyType?: string[];
  company?: string;
};

export type RecruiterPagination = {
  items: RecruiterDetail[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
};

export async function getServiceInfo(): Promise<ServiceInfo> {
  const response = await fetch(`${apiBaseUrl}/system/info`);
  if (!response.ok) {
    throw new Error(`Service info request failed with ${response.status}`);
  }
  return response.json() as Promise<ServiceInfo>;
}

export async function getDashboardSummary(): Promise<DashboardSummary> {
  const response = await fetch(`${apiBaseUrl}/dashboard/summary`);
  if (!response.ok) {
    throw new Error(`Dashboard summary request failed with ${response.status}`);
  }
  return response.json() as Promise<DashboardSummary>;
}

export async function getJobs(query: JobQuery = {}): Promise<JobPagination> {
  const params = new URLSearchParams();
  appendParams(params, 'page', query.page ?? 1);
  appendParams(params, 'page_size', query.pageSize ?? 25);
  appendParams(params, 'sort_by', query.sortBy ?? 'score');
  appendParams(params, 'sort_dir', query.sortDir ?? 'desc');
  appendParams(params, 'search', query.search);
  appendParams(params, 'location', query.location);
  appendRepeatedParams(params, 'source', query.source);
  appendRepeatedParams(params, 'company_type', query.companyType);
  appendParams(params, 'company', query.company);
  appendParams(params, 'remote_only', query.remoteOnly);
  appendParams(params, 'min_applicants', query.minApplicants);
  appendParams(params, 'max_applicants', query.maxApplicants);
  appendParams(params, 'skill_weight', query.skillWeight ?? 50);
  appendParams(params, 'recency_weight', query.recencyWeight ?? 30);
  appendParams(params, 'applicant_weight', query.applicantWeight ?? 20);
  const response = await fetch(`${apiBaseUrl}/dashboard/jobs?${params.toString()}`);
  if (!response.ok) {
    throw new Error(`Jobs request failed with ${response.status}`);
  }
  return response.json() as Promise<JobPagination>;
}

export async function getCompanies(query: CompanyQuery = {}): Promise<CompanyPagination> {
  const params = new URLSearchParams();
  appendParams(params, 'page', query.page ?? 1);
  appendParams(params, 'page_size', query.pageSize ?? 25);
  appendParams(params, 'sort_by', query.sortBy ?? 'job_count');
  appendParams(params, 'sort_dir', query.sortDir ?? 'desc');
  appendParams(params, 'search', query.search);
  appendParams(params, 'location', query.location);
  appendRepeatedParams(params, 'source', query.source);
  appendRepeatedParams(params, 'company_type', query.companyType);
  const response = await fetch(`${apiBaseUrl}/dashboard/companies?${params.toString()}`);
  if (!response.ok) {
    throw new Error(`Companies request failed with ${response.status}`);
  }
  return response.json() as Promise<CompanyPagination>;
}

export async function getRecruiters(query: RecruiterQuery = {}): Promise<RecruiterPagination> {
  const params = new URLSearchParams();
  appendParams(params, 'page', query.page ?? 1);
  appendParams(params, 'page_size', query.pageSize ?? 25);
  appendParams(params, 'search', query.search);
  appendParams(params, 'location', query.location);
  appendRepeatedParams(params, 'source', query.source);
  appendRepeatedParams(params, 'company_type', query.companyType);
  appendParams(params, 'company', query.company);
  const response = await fetch(`${apiBaseUrl}/dashboard/recruiters?${params.toString()}`);
  if (!response.ok) {
    throw new Error(`Recruiters request failed with ${response.status}`);
  }
  return response.json() as Promise<RecruiterPagination>;
}

export async function getJobSearchProfile(): Promise<JobSearchProfile> {
  const response = await fetch(`${apiBaseUrl}/system/profile`);
  if (!response.ok) {
    throw new Error(`Job search profile request failed with ${response.status}`);
  }
  return response.json() as Promise<JobSearchProfile>;
}

export async function triggerJobDiscovery(): Promise<{ status: string; task_id: string }> {
  const response = await fetch(`${apiBaseUrl}/system/discover`, { method: 'POST' });
  if (!response.ok) {
    throw new Error(`Discovery trigger request failed with ${response.status}`);
  }
  return response.json() as Promise<{ status: string; task_id: string }>;
}
