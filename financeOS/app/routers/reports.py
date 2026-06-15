from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import List
from datetime import date
from app.database import get_db
from app.services import report_service
from app.dependencies import get_current_user
from app.models.user import User

router = APIRouter(prefix="/api/reports", tags=["Reports"])


@router.get("/trend")
def get_spending_trend(
    start_date: date = Query(...),
    end_date: date = Query(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    return report_service.get_spending_trend(
        db, current_user.id, start_date, end_date
    )


@router.get("/net-worth")
def get_net_worth(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    return report_service.get_net_worth(db, current_user.id)


@router.get("/weekly")
def get_weekly_report(
    reference_date: date = Query(default=None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if reference_date is None:
        reference_date = date.today()
    return report_service.get_weekly_report(
        db, current_user.id, reference_date
    )


@router.get("/monthly-trends")
def get_monthly_trends(
    months: int = Query(default=6, ge=1, le=24),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    return report_service.get_monthly_trends(
        db, current_user.id, months
    )