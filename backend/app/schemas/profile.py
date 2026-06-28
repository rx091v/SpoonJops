from pydantic import BaseModel, ConfigDict


class JobSearchProfile(BaseModel):
    full_name: str
    resume_path: str
    target_job_titles: list[str]
    target_job_locations: list[str]
    target_job_remote_only: bool
    target_years_experience: int
    target_keywords: list[str]

    model_config = ConfigDict(frozen=True)
