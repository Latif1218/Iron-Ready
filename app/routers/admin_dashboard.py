from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import func, select, or_
from typing import Annotated, List
from ..database import get_db
from ..models import user_model, subs_model, transaction_model, activity_log
from ..schemas.admin_schema import DashboardStats, RecentActivityItem, UserListItem, UserPage, SubscriptionInfo, OnboardingInfo
from ..authentication.user_auth import get_current_admin_user
from ..schemas.user_schema import UserBase
from datetime import datetime, timedelta
from fastapi_pagination import Params
from fastapi_pagination.ext.sqlalchemy import paginate


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



@router.get("/", response_model=UserPage)
def list_users(
    db: Annotated[Session, Depends(get_db)],
    admin: Annotated[user_model.User, Depends(get_current_admin_user)],
    search: Annotated[str | None, Query(description="Search by name or email (partial match)")] = None,
    params: Params = Depends()  
):
    stmt = (
        select(user_model.User)
        .outerjoin(subs_model.Subscription, user_model.User.subscription)
        .order_by(user_model.User.created_at.desc())
    )

    if search:
        search_pattern = f"%{search}%"
        stmt = stmt.where(
            or_(
                user_model.User.name.ilike(search_pattern),
                user_model.User.email.ilike(search_pattern)
            )
        )

    page = paginate(db, stmt, params)

    items = []
    for user in page.items:
        onboarding_info = None
        if user.onboarding:
            onboarding_info = OnboardingInfo(
                age=user.onboarding.age,
                gender=user.onboarding.gender,
                height_cm=user.onboarding.height_cm,
                weight_kg=user.onboarding.weight_kg
            )

        sub_info = None
        if user.subscription:
            sub_info = SubscriptionInfo(
                status=user.subscription.status.value if user.subscription.status else "unknown",
                plan_name=None, 
                price=None,      
                current_period_end=user.subscription.current_period_end,
                cancel_at_period_end=user.subscription.cancel_at_period_end
            )

        items.append(
            UserListItem(
                id=user.id,
                name=user.name,
                email=user.email,
                is_active=user.is_active,
                role=user.role,
                created_at=user.created_at,
                onboarding=onboarding_info,
                subscription=sub_info
            )
        )

    return UserPage(
        items=items,
        total=page.total,
        page=page.page,
        size=page.size,
        pages=page.pages
    )


@router.put("/users/{user_id}", status_code=status.HTTP_200_OK)
def edit_user(
    user_id: int,
    data: UserBase,
    db: Annotated[Session, Depends(get_db)],
    current_admin: Annotated[user_model.User, Depends(get_current_admin_user)]
):
    user = db.query(user_model.User).filter(user_model.User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    user.name = data.name
    user.email = data.email
    user.avatar_url = data.avatar_url
    db.commit()
    return {
        "message": "User updated"
    }


@router.put("/users/{user_id}/ban", status_code=status.HTTP_200_OK)
def ban_user(
    user_id: int,
    db: Annotated[Session, Depends(get_db)],
    current_admin: Annotated[user_model.User, Depends(get_current_admin_user)]
):
    user = db.query(user_model.User).filter(
        user_model.User.id == user_id
    ).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    user.is_active = False
    db.commit()
    return {
        "message": "User banned" 
    }