from fastapi import APIRouter
from app.api.endpoints import (
    auth, dashboard, applications, evc, compliance, documents, alerts, config, admin, ai
)

api_router = APIRouter()

api_router.include_router(auth.router, prefix="/auth", tags=["Authentication"])
api_router.include_router(dashboard.router, prefix="/dashboard", tags=["Control Tower Dashboard"])
api_router.include_router(applications.router, prefix="/applications", tags=["Applications & Case Workbench"])
api_router.include_router(evc.router, prefix="/evc", tags=["EVC Inspection Management"])
api_router.include_router(compliance.router, prefix="/compliance", tags=["Compliance Radar & Undertakings"])
api_router.include_router(documents.router, prefix="/documents", tags=["Document Vault & Validity"])
api_router.include_router(alerts.router, prefix="/alerts", tags=["Alerts & Escalations"])
api_router.include_router(config.router, prefix="/config", tags=["Workflow Configuration"])
api_router.include_router(admin.router, prefix="/admin", tags=["System Administration"])
api_router.include_router(ai.router, prefix="/ai", tags=["AI Document Review & Regulatory RAG"])
