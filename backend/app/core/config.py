from functools import lru_cache
from pathlib import Path
from typing import Any

from pydantic import AnyHttpUrl, Field, SecretStr
from pydantic_settings import BaseSettings, EnvSettingsSource, PydanticBaseSettingsSource, SettingsConfigDict


class CommaSeparatedEnvSource(EnvSettingsSource):
    list_fields = {
        "cors_origins",
        "target_job_titles",
        "target_job_locations",
        "target_keywords",
        "lever_boards",
        "greenhouse_boards",
        "ashby_boards",
    }

    def prepare_field_value(self, field_name: str, field: Any, value: Any, value_is_complex: bool) -> Any:
        if field_name in self.list_fields and isinstance(value, str):
            return [item.strip() for item in value.split(",") if item.strip()]
        return super().prepare_field_value(field_name, field, value, value_is_complex)


class Settings(BaseSettings):
    app_env: str = "local"
    app_name: str = "AI Job Search Agent"
    log_level: str = "INFO"
    cors_origins: list[str] = Field(default_factory=lambda: ["http://localhost:5173"])

    database_url: str = "postgresql+asyncpg://jobagent:jobagent@postgres:5432/jobagent"
    redis_url: str = "redis://redis:6379/0"
    celery_broker_url: str = "redis://redis:6379/1"
    celery_result_backend: str = "redis://redis:6379/2"
    elasticsearch_url: str | None = None
    elasticsearch_index: str = "jobs"

    jwt_secret_key: SecretStr = SecretStr("change-me-in-production")
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 60

    openai_api_key: SecretStr | None = None
    openai_model: str = "gpt-5.5"

    resume_storage_path: Path = Path("/app/storage/resumes")
    profile_resume_path: Path = Path("/app/storage/rahul_mathur_resume.pdf")
    target_job_titles: list[str] = Field(
        default_factory=lambda: ["Lead Software Engineer", "Staff Software Engineer"]
    )
    target_job_locations: list[str] = Field(default_factory=lambda: ["Bengaluru", "Remote"])
    target_job_remote_only: bool = False
    target_years_experience: int = 10
    target_keywords: list[str] = Field(
        default_factory=lambda: [
            "Java",
            "Spring Boot",
            "microservices",
            "Kubernetes",
            "cloud",
        ]
    )
    lever_boards: list[str] = Field(default_factory=list)
    greenhouse_boards: list[str] = Field(default_factory=list)
    ashby_boards: list[str] = Field(default_factory=list)
    browser_storage_path: Path = Path("/app/storage/browser")
    screenshot_storage_path: Path = Path("/app/storage/screenshots")
    public_base_url: AnyHttpUrl | None = None

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    @classmethod
    def settings_customise_sources(
        cls,
        settings_cls: type[BaseSettings],
        init_settings: PydanticBaseSettingsSource,
        env_settings: PydanticBaseSettingsSource,
        dotenv_settings: PydanticBaseSettingsSource,
        file_secret_settings: PydanticBaseSettingsSource,
    ) -> tuple[PydanticBaseSettingsSource, ...]:
        return (
            init_settings,
            CommaSeparatedEnvSource(settings_cls),
            dotenv_settings,
            file_secret_settings,
        )


@lru_cache
def get_settings() -> Settings:
    return Settings()
