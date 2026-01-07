"""
Reports and dashboard endpoints
"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.core.deps import get_current_user
from app.models.user import User

router = APIRouter(tags=["Reports"])


@router.get("/reports/dashboard")
def get_dashboard_kpis(
    vestiging_id: int = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get dashboard KPIs
    
    TODO: Implement actual database queries
    """
    return {
        "success": True,
        "data": {
            "actieve_projecten": 8,
            "budget_totaal": 3200000,
            "budget_besteed": 2400000,
            "budget_percentage": 75,
            "deadlines_deze_week": 3,
            "openstaande_taken": 12,
            "projecten_on_time": {
                "count": 7,
                "percentage": 88
            },
            "projecten_on_budget": {
                "count": 6,
                "percentage": 75
            }
        }
    }
