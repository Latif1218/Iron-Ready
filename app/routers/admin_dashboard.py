from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func, select
from typing import Annotated, List
from ..database import get_db
from ..models import user_model, subs_model, transaction_model, activity_log
from ..schemas.admin_schema import DashboardStats, RecentActivityItem
from ..authentication.user_auth import get_current_admin_user
from datetime import datetime, timedelta


router = APIRouter(
    prefix="/admin_dashboard",
    tags=["Admin_dashboard"]
)

@router.get("/status", response_model=DashboardStats)
def get_dashboard_stats(
    db: Annotated[Session, Depends(get_db)],
    current_admin: Annotated[user_model.User, Depends(get_current_admin_user)]
):
    now = datetime.utcnow()

    total_users = db.query(func.count(user_model.User.id.distinct())).scalar() or 0

    premium_users = (
        db.query(func.count(user_model.User.id.distinct()))
        .join(subs_model.Subscription)
        .filter(
            subs_model.Subscription.status.in_([
                subs_model.SubscriptionStatus.ACTIVE.value,
                subs_model.SubscriptionStatus.PAST_DUE.value
            ]),
            subs_model.Subscription.cancel_at_period_end.is_(False)
        )
        .scalar() or 0
    )

    free_users = total_users - premium_users

    def get_revenue(start_date=None, end_date=None):
        q = db.query(func.coalesce(func.sum(transaction_model.Transaction.amount), 0.0)).filter(
            transaction_model.Transaction.amount > 0,
            transaction_model.Transaction.status == transaction_model.TransactionStatus.COMPLETED.value,
            transaction_model.Transaction.type.in_([
                transaction_model.TransactionType.SUBSCRIPTION_PAYMENT.value,
                transaction_model.TransactionType.SUBSCRIPTION_RENEWAL.value
            ])
        )
        if start_date:
            q = q.filter(transaction_model.Transaction.created_at >= start_date)
        if end_date:
            q = q.filter(transaction_model.Transaction.created_at < end_date)
        return q.scalar() or 0.0
    
    total_revenue = get_revenue()
    monthly_revenue = get_revenue(now - timedelta(days=30))
    last_month_revenue = get_revenue(now - timedelta(days=60), now - timedelta(days=30))

    recent_activities: List[RecentActivityItem] = []

    if hasattr(activity_log, "ActivityLog"):
        stmt = (
            select(
                activity_log.ActivityLog.description,
                activity_log.ActivityLog.created_at,
                user_model.User.name.label("user_name")
            )
            .join(user_model.User)
            .order_by(activity_log.ActivityLog.created_at.desc())
            .limit(8)
        )
        for row in db.execute(stmt).all():
            delta = now - row.created_at
            if delta.total_seconds() < 3600:
                time_ago = f"{int(delta.total_seconds()//60)}m ago"
            elif delta.total_seconds() < 86400:
                time_ago = f"{int(delta.total_seconds()//3600)}h ago"
            else:
                time_ago = f"{delta.days}d ago"

            recent_activities.append(
                RecentActivityItem(
                    user_name=row.user_name or "User",
                    action=row.description,
                    time_ago=time_ago,
                    timestamp=row.created_at
                )
            )
    return DashboardStats(
        total_users=total_users,
        premium_users=premium_users,
        free_users=free_users,
        total_revenue=round(total_revenue, 2),
        monthly_revenue=round(monthly_revenue, 2),
        last_month_revenue=round(last_month_revenue, 2),
        recent_activities=recent_activities,
        updated_at=now
    )