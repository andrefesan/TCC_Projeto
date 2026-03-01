from pydantic import BaseModel
from datetime import datetime


class HealthResponse(BaseModel):
    status: str
    database: str
    timestamp: datetime
    version: str = "1.0.0"
