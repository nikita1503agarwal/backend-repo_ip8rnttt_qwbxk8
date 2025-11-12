"""
Database Schemas for the DevEx Dashboard

Each Pydantic model below corresponds to a MongoDB collection (collection name is the lowercase of the class name).
"""
from __future__ import annotations
from pydantic import BaseModel, Field
from typing import List, Optional, Literal
from datetime import datetime

# Core entities

class Team(BaseModel):
    name: str = Field(..., description="Team name")
    lead: Optional[str] = Field(None, description="Engineering manager / lead")
    org_unit: Optional[str] = Field(None, description="Org unit or tribe")
    size: Optional[int] = Field(None, ge=1)

class Friction(BaseModel):
    title: str = Field(..., description="Short friction label")
    description: Optional[str] = Field(None, description="Detailed description of the friction")
    category: Literal[
        "build_pipeline","tooling","process","tech_debt","environment","collaboration","onboarding","testing","release"
    ] = "process"
    severity: int = Field(3, ge=1, le=5, description="1=low, 5=critical")
    impact_areas: List[str] = Field(default_factory=list)
    status: Literal["open","active","resolved"] = "open"

class MetricSnapshot(BaseModel):
    level: Literal["org","team"]
    team_id: Optional[str] = Field(None, description="Required when level=team")
    date: datetime = Field(default_factory=datetime.utcnow)
    devex_score: float = Field(..., ge=0, le=100)
    motivation: float = Field(..., ge=0, le=100)
    wasted_time_hours: float = Field(..., ge=0)
    trend: float = Field(0.0, description="Delta vs previous period for DevEx Score")
    sample_size: Optional[int] = Field(None, ge=0)
    notes: Optional[str] = None

class Benchmark(BaseModel):
    metric: Literal["devex_score","motivation","wasted_time_hours"]
    value: float
    segment: str = Field("industry", description="Comparison segment")
    percentile: Optional[float] = Field(None, ge=0, le=100)

class Initiative(BaseModel):
    title: str
    friction_id: str
    scope: Literal["org","team"] = "team"
    team_id: Optional[str] = None
    owner: Optional[str] = None
    start_date: datetime = Field(default_factory=datetime.utcnow)
    target_date: Optional[datetime] = None
    goals: List[str] = Field(default_factory=list)
    success_metrics: List[str] = Field(default_factory=list)
    status: Literal["planned","in_progress","completed","paused"] = "planned"
    progress: float = Field(0.0, ge=0, le=100)

class Action(BaseModel):
    initiative_id: str
    description: str
    assignee: Optional[str] = None
    due_date: Optional[datetime] = None
    status: Literal["todo","in_progress","done"] = "todo"
    progress: int = Field(0, ge=0, le=100)
