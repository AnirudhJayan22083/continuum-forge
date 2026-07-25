from pydantic import BaseModel
from typing import List

class Heuristic(BaseModel):
    machine: str
    component: str
    failure: str
    trigger: str
    conditions: List[str]
    symptoms: List[str]
    recommended_action: str
    expert_confidence: float
