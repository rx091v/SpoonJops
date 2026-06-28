from pydantic import BaseModel, ConfigDict


class ServiceInfo(BaseModel):
    name: str
    environment: str
    version: str

    model_config = ConfigDict(frozen=True)
