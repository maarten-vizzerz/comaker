"""
Schemas for Mijn Taken (My Tasks) feature
"""
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime


class TaakItem(BaseModel):
    """Individual task item"""
    fase_id: str
    project_id: str
    project_naam: str
    project_nummer: str
    fase_naam: str
    fase_nummer: int
    deadline: Optional[datetime] = None
    status: str
    prioriteit: str  # "hoog", "middel", "laag"
    type: str  # "open_fase", "wacht_op_acceptatie", "missend_document"
    beschrijving: Optional[str] = None

    class Config:
        from_attributes = True


class MijnTakenResponse(BaseModel):
    """Response for GET /api/v1/me/taken"""
    open_fases: List[TaakItem] = Field(default_factory=list, description="Fases waar gebruiker verantwoordelijke is EN status != AFGEROND")
    wacht_op_acceptatie: List[TaakItem] = Field(default_factory=list, description="Fases die wachten op acceptatie van gebruiker")
    binnenkort_verlopen: List[TaakItem] = Field(default_factory=list, description="Deadlines binnen 7 dagen")
    missende_documenten: List[TaakItem] = Field(default_factory=list, description="Fases zonder verplichte documenten")
    totaal_aantal: int = Field(description="Total number of tasks")

    class Config:
        from_attributes = True
