from pydantic import BaseModel
from datetime import datetime


class RecoveryOut(BaseModel):
    id: int
    muscle_group: str
    status: str
    tip: str | None
    last_updated: datetime

    class Config:
        from_attributes = True