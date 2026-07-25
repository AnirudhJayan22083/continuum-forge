from pydantic import BaseModel
from typing import Optional

class ValidationResult(BaseModel):
    accepted: bool
    support_count: int
    conditional_probability: float
    pearson_correlation: float
    chi_square_stat: float
    p_value: float
    explanation: str
