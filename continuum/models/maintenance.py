from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class MaintenanceLog(BaseModel):
    log_id: str
    machine_id: str
    component: str
    failure_mode: str
    timestamp: datetime
    action_taken: str
