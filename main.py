import os
from datetime import datetime
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional

from database import db, create_document, get_documents

app = FastAPI(title="DevEx Dashboard API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    return {"message": "DevEx Backend is running"}

@app.get("/test")
def test_database():
    response = {
        "backend": "✅ Running",
        "database": "❌ Not Available",
        "database_url": None,
        "database_name": None,
        "connection_status": "Not Connected",
        "collections": []
    }
    try:
        if db is not None:
            response["database"] = "✅ Connected & Working"
            response["database_url"] = "✅ Set" if os.getenv("DATABASE_URL") else "❌ Not Set"
            response["database_name"] = "✅ Set" if os.getenv("DATABASE_NAME") else "❌ Not Set"
            response["connection_status"] = "Connected"
            try:
                response["collections"] = db.list_collection_names()[:10]
            except Exception as e:
                response["database"] = f"⚠️ Connected but Error: {str(e)[:80]}"
        else:
            response["database"] = "❌ Not initialized"
    except Exception as e:
        response["database"] = f"❌ Error: {str(e)[:80]}"
    return response

# ---------------------- Schemas endpoint ----------------------
from schemas import Team, Friction, MetricSnapshot, Benchmark, Initiative, Action

@app.get("/schema")
def get_schema():
    return {
        "team": Team.model_json_schema(),
        "friction": Friction.model_json_schema(),
        "metricsnapshot": MetricSnapshot.model_json_schema(),
        "benchmark": Benchmark.model_json_schema(),
        "initiative": Initiative.model_json_schema(),
        "action": Action.model_json_schema(),
    }

# ---------------------- DevEx data endpoints ----------------------

class CreateMetric(BaseModel):
    level: str
    team_id: Optional[str] = None
    devex_score: float
    motivation: float
    wasted_time_hours: float
    trend: float = 0.0
    sample_size: Optional[int] = None
    notes: Optional[str] = None

@app.post("/metrics")
def create_metric(payload: CreateMetric):
    from schemas import MetricSnapshot
    metric = MetricSnapshot(**payload.model_dump())
    inserted_id = create_document("metricsnapshot", metric)
    return {"id": inserted_id}

@app.get("/metrics")
def list_metrics(level: Optional[str] = Query(None), team_id: Optional[str] = Query(None), limit: int = 50):
    filter_dict = {}
    if level:
        filter_dict["level"] = level
    if team_id:
        filter_dict["team_id"] = team_id
    docs = get_documents("metricsnapshot", filter_dict, limit)
    # Convert ObjectId and datetime to serializable forms
    for d in docs:
        d["_id"] = str(d.get("_id"))
        for k, v in list(d.items()):
            if isinstance(v, datetime):
                d[k] = v.isoformat()
    return docs

class CreateTeam(BaseModel):
    name: str
    lead: Optional[str] = None
    org_unit: Optional[str] = None
    size: Optional[int] = None

@app.post("/teams")
def create_team(payload: CreateTeam):
    from schemas import Team
    team = Team(**payload.model_dump())
    inserted_id = create_document("team", team)
    return {"id": inserted_id}

@app.get("/teams")
def list_teams(limit: int = 100):
    docs = get_documents("team", {}, limit)
    for d in docs:
        d["_id"] = str(d.get("_id"))
    return docs

class CreateFriction(BaseModel):
    title: str
    description: Optional[str] = None
    category: str = "process"
    severity: int = 3
    impact_areas: List[str] = []
    status: str = "open"

@app.post("/frictions")
def create_friction(payload: CreateFriction):
    from schemas import Friction
    friction = Friction(**payload.model_dump())
    inserted_id = create_document("friction", friction)
    return {"id": inserted_id}

@app.get("/frictions")
def list_frictions(limit: int = 100):
    docs = get_documents("friction", {}, limit)
    for d in docs:
        d["_id"] = str(d.get("_id"))
    return docs

class CreateInitiative(BaseModel):
    title: str
    friction_id: str
    scope: str = "team"
    team_id: Optional[str] = None
    owner: Optional[str] = None
    target_date: Optional[datetime] = None
    goals: List[str] = []
    success_metrics: List[str] = []
    status: str = "planned"
    progress: float = 0.0

@app.post("/initiatives")
def create_initiative(payload: CreateInitiative):
    from schemas import Initiative
    data = Initiative(**payload.model_dump())
    inserted_id = create_document("initiative", data)
    return {"id": inserted_id}

@app.get("/initiatives")
def list_initiatives(limit: int = 100, team_id: Optional[str] = None, status: Optional[str] = None):
    filter_dict = {}
    if team_id:
        filter_dict["team_id"] = team_id
    if status:
        filter_dict["status"] = status
    docs = get_documents("initiative", filter_dict, limit)
    for d in docs:
        d["_id"] = str(d.get("_id"))
        for k, v in list(d.items()):
            if isinstance(v, datetime):
                d[k] = v.isoformat()
    return docs

class CreateAction(BaseModel):
    initiative_id: str
    description: str
    assignee: Optional[str] = None
    due_date: Optional[datetime] = None
    status: str = "todo"
    progress: int = 0

@app.post("/actions")
def create_action(payload: CreateAction):
    from schemas import Action
    data = Action(**payload.model_dump())
    inserted_id = create_document("action", data)
    return {"id": inserted_id}

@app.get("/actions")
def list_actions(initiative_id: Optional[str] = None, limit: int = 200):
    filter_dict = {"initiative_id": initiative_id} if initiative_id else {}
    docs = get_documents("action", filter_dict, limit)
    for d in docs:
        d["_id"] = str(d.get("_id"))
        for k, v in list(d.items()):
            if isinstance(v, datetime):
                d[k] = v.isoformat()
    return docs

# Benchmarks
class CreateBenchmark(BaseModel):
    metric: str
    value: float
    segment: str = "industry"
    percentile: Optional[float] = None

@app.post("/benchmarks")
def create_benchmark(payload: CreateBenchmark):
    from schemas import Benchmark
    data = Benchmark(**payload.model_dump())
    inserted_id = create_document("benchmark", data)
    return {"id": inserted_id}

@app.get("/benchmarks")
def list_benchmarks(metric: Optional[str] = None, segment: Optional[str] = None, limit: int = 50):
    filter_dict = {}
    if metric:
        filter_dict["metric"] = metric
    if segment:
        filter_dict["segment"] = segment
    docs = get_documents("benchmark", filter_dict, limit)
    for d in docs:
        d["_id"] = str(d.get("_id"))
    return docs

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
