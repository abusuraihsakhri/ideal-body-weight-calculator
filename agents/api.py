"""
FastAPI REST API Server for Ideal Body Weight Calculator.
"""
from dataclasses import asdict
from pathlib import Path
from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from ibw import calculate_patient
from .base import AuditLogger, PHIGuard
from .models import SystemTaskPayload, ConsensusDossier
from .supervisor import SystemSupervisor

supervisor = SystemSupervisor(model_provider="mock")

app = FastAPI(
    title="Ideal Body Weight Calculator API",
    description="Ideal-body-weight formulas and optional experimental audit endpoints",
    version="3.0.0-ENTERPRISE",
)


class ChatRequest(BaseModel):
    query: str


class IBWRequest(BaseModel):
    sex: str
    height_cm: float
    weight_kg: float


@app.post("/api/ibw")
def api_ibw(payload: IBWRequest):
    """Calculate adult reference weights, without requiring an audit secret."""
    result = calculate_patient("anonymous", payload.sex, payload.height_cm, payload.weight_kg)
    if result.ibw_devine is None:
        raise HTTPException(status_code=422, detail=result.warnings)
    return asdict(result)


@app.get("/health")
def health():
    return {"status": "healthy", "service": "ideal-body-weight-calculator"}


@app.get("/metrics")
def metrics():
    return {
        "dossiers_processed_total": len(supervisor.dossier_registry),
        "audit_blocks_total": len(AuditLogger.get_trail()),
        "system_status": "running"
    }


@app.post("/api/audit")
def api_audit(payload: SystemTaskPayload):
    dossier = supervisor.process_task(payload)
    return dossier.to_dict()


@app.post("/api/chat")
def api_chat(req: ChatRequest):
    try:
        ans = supervisor.query_supervisory_chat(req.query)
        return {"response": ans}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/api/audit/logs")
def api_audit_logs():
    return {"audit_trail": AuditLogger.get_trail(), "verified": AuditLogger.verify_integrity()}


# The API and the standalone GitHub Pages site serve the same browser assets.
# Declare static mounting after the API routes so /api/* and /health take precedence.
app.mount("/", StaticFiles(directory=Path(__file__).resolve().parents[1] / "web", html=True), name="browser")
