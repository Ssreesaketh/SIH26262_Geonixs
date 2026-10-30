from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime, timezone, timedelta
from typing import List
from app.core.database import get_db
from app.core.auth import get_current_user
from app.models.entities import (
    Application, Region, Institution, Document, EVCEvent, Undertaking, User
)
from app.schemas.domain import (
    DashboardSummaryResponse, StagePendencyItem, RegionalWorkloadItem
)

router = APIRouter()

def utc_now() -> datetime:
    return datetime.now(timezone.utc)

@router.get("/summary", response_model=DashboardSummaryResponse)
def get_dashboard_summary(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    now = utc_now()
    app_query = db.query(Application)
    doc_query = db.query(Document)
    evc_query = db.query(EVCEvent).join(Application)
    und_query = db.query(Undertaking)

    # Apply Scope
    if current_user.role == "INSTITUTION_USER":
        app_query = app_query.filter(Application.institution_id == current_user.institution_id)
        doc_query = doc_query.filter(Document.institution_id == current_user.institution_id)
        evc_query = evc_query.filter(Application.institution_id == current_user.institution_id)
        und_query = und_query.filter(Undertaking.institution_id == current_user.institution_id)
    # All officer roles share the same operational application set. Institution
    # users are scoped above to their own institution.

    total_active = app_query.filter(
        Application.current_stage_code != "COMPLETED",
        Application.workflow_status != "STAGE_COMPLETED"
    ).count()

    overdue_stages = app_query.filter(
        Application.current_stage_code != "COMPLETED",
        Application.workflow_status != "STAGE_COMPLETED",
        Application.stage_due_at < now
    ).count()

    upcoming_sla = app_query.filter(
        Application.current_stage_code != "COMPLETED",
        Application.workflow_status != "STAGE_COMPLETED",
        Application.stage_due_at >= now,
        Application.stage_due_at <= now + timedelta(hours=48)
    ).count()

    expired_documents = doc_query.filter(
        Document.status == "EXPIRED"
    ).count()

    pending_evc = evc_query.filter(
        EVCEvent.status == "PENDING_SCHEDULE"
    ).count()

    pending_undertakings = und_query.filter(
        Undertaking.status.in_(["PENDING", "RETURNED_FOR_CORRECTION"])
    ).count()

    return DashboardSummaryResponse(
        total_active=total_active,
        overdue_stages=overdue_stages,
        upcoming_sla=upcoming_sla,
        expired_documents=expired_documents,
        pending_evc=pending_evc,
        pending_undertakings=pending_undertakings
    )

@router.get("/pendency", response_model=List[StagePendencyItem])
def get_stage_pendency(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    query = db.query(
        Application.current_stage_code,
        func.count(Application.id).label("count")
    ).filter(
        Application.current_stage_code != "COMPLETED",
        Application.workflow_status != "STAGE_COMPLETED"
    )

    if current_user.role == "INSTITUTION_USER":
        query = query.filter(Application.institution_id == current_user.institution_id)
    # Officer roles see the common application pendency across the whole demo.
    results = query.group_by(Application.current_stage_code).all()
    
    stage_names = {
        "DRAFT": "Draft Applications",
        "SCRUTINY": "Scrutiny Review",
        "EVC": "EVC Inspection Pipeline",
        "SAC_SHC": "SAC / SHC Hearing Committee",
        "COMPLETED": "Completed"
    }

    return [
        StagePendencyItem(
            stage_code=row[0],
            stage_name=stage_names.get(row[0], row[0]),
            count=row[1]
        )
        for row in results
    ]

@router.get("/regions", response_model=List[RegionalWorkloadItem])
def get_regional_workload(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Regional workload is officer-only; an institution must not infer other
    # institutions' regional activity from aggregate counts.
    if current_user.role == "INSTITUTION_USER":
        return []

    now = utc_now()
    regions = db.query(Region).filter(Region.is_active == True).all()
    workload = []

    for reg in regions:
        active = db.query(Application).join(Institution).filter(
            Institution.region_id == reg.id,
            Application.current_stage_code != "COMPLETED",
            Application.workflow_status != "STAGE_COMPLETED"
        ).count()

        overdue = db.query(Application).join(Institution).filter(
            Institution.region_id == reg.id,
            Application.current_stage_code != "COMPLETED",
            Application.workflow_status != "STAGE_COMPLETED",
            Application.stage_due_at < now
        ).count()

        workload.append(
            RegionalWorkloadItem(
                region_id=reg.id,
                region_code=reg.code,
                region_name=reg.name,
                active_count=active,
                overdue_count=overdue
            )
        )

    return workload
