from pydantic import BaseModel


class FunnelPoint(BaseModel):
    name: str
    value: int


class DashboardSummary(BaseModel):
    jobs_found: int
    saved: int
    applied: int
    interviews: int
    offers: int
    rejected: int
    funnel: list[FunnelPoint]
