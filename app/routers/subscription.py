from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from ..database import get_db
from ..authentication.user_auth import get_current_user
from ..models.subs_model import Subscription, SubscriptionStatus
from ..schemas.subs_schema import CreateSubscriptionRequest, SubscriptionResponse
import stripe
from datetime import datetime
from ..config import STRIPE_SECRET_KEY, STRIPE_MONTHLY_PRICE_ID, STRIPE_YEARLY_PRICE_ID

router = APIRouter(
    prefix="/subscription",
    tags=["Subscription"]
)

stripe.api_key = STRIPE_SECRET_KEY

if not STRIPE_MONTHLY_PRICE_ID or not STRIPE_YEARLY_PRICE_ID:
    raise ValueError("Stripe price IDs are not configured properly.")


@router.post("/", status_code=status.HTTP_201_CREATED, response_model=SubscriptionResponse)
def create_subscription(
    subs_data: CreateSubscriptionRequest,
    current_user: Session = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    
    if current_user.subscription:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User already has an active subscription."
        )
        
    price_id = STRIPE_MONTHLY_PRICE_ID if subs_data.plan_type == "monthly" else STRIPE_YEARLY_PRICE_ID
    
    try:
        if hasattr(current_user, 'stripe_customer_id') and current_user.stripe_customer_id:
            customer = stripe.Customer.create(
                email=current_user.email,
                name = current_user.name,
                metadata={"user_id": current_user.id}
            )
            
        current_user.stripe_customer_id = customer.id
        db.commit()
        
        if subs_data.payment_method_id:
            stripe.PaymentMethod.attach(
                subs_data.payment_method_id,
                customer=current_user.stripe_customer_id,
            )
            stripe.Customer.modify(
                current_user.stripe_customer_id,
                invoice_settings={
                    "default_payment_method": subs_data.payment_method_id
                }
            )
    
        sub = stripe.Subscription.create(
            customer=current_user.stripe_customer_id,
            items=[{"price": price_id}],
            trial_period_days=14,
            expand=["latest_invoice.payment_intent"],
        )
    
        db_sub = Subscription(
            id = sub.id,
            user_id = current_user.id,
            stripe_customer_id = current_user.stripe_customer_id,
            price_id = price_id,
            status = SubscriptionStatus(sub.status),
            current_period_start=datetime.fromtimestamp(sub.current_period_start) if sub.current_period_start else None,
            current_period_end=datetime.fromtimestamp(sub.current_period_end) if sub.current_period_end else None,
            trial_start=datetime.fromtimestamp(sub.trial_start) if sub.trial_start else None,
            trial_end=datetime.fromtimestamp(sub.trial_end) if sub.trial_end else None,
        )
    
        db.add(db_sub)
        db.commit()
        db.refresh(db_sub)
    
        return SubscriptionResponse(
            id=sub.id,
            status=sub.status,
            plan_type=subs_data.plan_type,
            trial_end=db_sub.trial_end,
            current_period_end=db_sub.current_period_end,
            cancel_at_period_end=db_sub.cancel_at_period_end
        )
    
    except stripe.error.StripeError as e:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Stripe error: {e.user_message}"
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )
        
        
        
@router.get("/me", response_model=SubscriptionResponse | dict)
def get_my_subscription(
    current_user: Session = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    sub = db.query(Subscription).filter(
        Subscription.user_id == current_user.id
    ).first()
    
    if not sub:
        return {
            "has_subscription": False,
            "message": "No active subscription found."
        }
    return SubscriptionResponse.from_orm(sub)

