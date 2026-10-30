from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.auth import get_current_user, require_roles
from app.models.entities import User
from app.seed_data import seed_database
from app.services.sla_engine import SLAEngine

router = APIRouter()

@router.post("/reset-demo")
def reset_demo_data(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(["SYSTEM_ADMIN"]))
):
    """
    Safely resets the demonstration dataset back to deterministic state.
    """
    seed_database(db, reset=True)
    # Run initial SLA check to populate baseline alerts
    SLAEngine.evaluate_all(db)
    return {"message": "Demonstration database successfully reset and re-seeded to initial state."}
