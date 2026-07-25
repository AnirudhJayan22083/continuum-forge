from pydantic import BaseModel
from datetime import date

class Employee(BaseModel):
    id: str
    name: str
    role: str
    experience_years: int
    retirement_date: date
