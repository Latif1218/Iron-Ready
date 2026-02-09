from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Annotated

from app.models.user_model import User
from ..database import get_db
from ..authentication.user_auth import get_current_user
from ..models.subs_model import Subscription, SubscriptionStatus
from ..schemas.subs_schema import CreateSubscriptionRequest, SubscriptionResponse
import stripe
from datetime import datetime
from ..config import STRIPE_SECRET_KEY, STRIPE_MONTHLY_PRICE_ID, STRIPE_YEARLY_PRICE_ID
import logging

router = APIRouter(
    prefix="/subscription",
    tags=["Subscription"]
)

stripe.api_key = STRIPE_SECRET_KEY

logger = logging.getLogger(__name__)

if not STRIPE_SECRET_KEY:
    logger.error("STRIPE_SECRET_KEY is missing!")
    raise ValueError("STRIPE_SECRET_KEY is not configured.")

if not STRIPE_MONTHLY_PRICE_ID or not STRIPE_YEARLY_PRICE_ID:
    logger.error("Stripe price IDs are not configured properly.")
    raise ValueError("Stripe price IDs are not configured properly.")


@router.post("/", status_code=status.HTTP_201_CREATED, response_model=SubscriptionResponse)
def create_subscription(
    subs_data: CreateSubscriptionRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Session = Depends(get_db)
):
    logger.info(f"Starting subscription creation for user {current_user.id} | plan: {subs_data.plan_type}")
    logger.info(f"Payment method: {subs_data.payment_method_id or 'None (trial only)'}")

    if current_user.subscription:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User already has an active subscription."
        )

    price_id = STRIPE_MONTHLY_PRICE_ID if subs_data.plan_type == "monthly" else STRIPE_YEARLY_PRICE_ID
    logger.info(f"Selected price_id: {price_id}")

    try:
        customer = None

        if hasattr(current_user, 'stripe_customer_id') and current_user.stripe_customer_id:
            logger.info(f"Retrieving existing customer: {current_user.stripe_customer_id}")
            customer = stripe.Customer.retrieve(current_user.stripe_customer_id)
        else:
            logger.info("Creating new Stripe customer")
            customer = stripe.Customer.create(
                email=current_user.email,
                name=current_user.name,
                metadata={"user_id": str(current_user.id)}
            )
            logger.info(f"New customer created: {customer.id}")
            current_user.stripe_customer_id = customer.id
            db.commit()
            logger.info("Customer ID saved to DB")

        # Payment method handling (optional)
        if subs_data.payment_method_id:
            logger.info(f"Validating payment method: {subs_data.payment_method_id}")
            try:
                payment_method = stripe.PaymentMethod.retrieve(subs_data.payment_method_id)
                if payment_method.customer:
                    if payment_method.customer == customer.id:
                        logger.info("Payment method already attached to this customer - skipping attach")
                    else:
                        logger.error(f"Payment method attached to different customer: {payment_method.customer}")
                        raise HTTPException(400, "Payment method already attached to another customer")
                else:
                    logger.info("Attaching payment method")
                    stripe.PaymentMethod.attach(
                        subs_data.payment_method_id,
                        customer=customer.id,
                    )
                    stripe.Customer.modify(
                        customer.id,
                        invoice_settings={"default_payment_method": subs_data.payment_method_id}
                    )
                    logger.info("Payment method attached and set as default")
            except stripe.error.InvalidRequestError as e:
                logger.error(f"Invalid payment method ID: {str(e)}")
                raise HTTPException(400, "Invalid or non-existent payment method ID")
            except stripe.error.StripeError as e:
                logger.error(f"Payment method error: {str(e)} | User message: {e.user_message or 'No message'}")
                raise HTTPException(400, f"Payment method error: {e.user_message or str(e)}")

        # Create subscription
        logger.info("Creating Stripe subscription")
        sub = stripe.Subscription.create(
            customer=customer.id,
            items=[{"price": price_id}],
            trial_period_days=14,
            expand=["latest_invoice.payment_intent"],
        )
        logger.info(f"Subscription created: ID={sub.id} | status={sub.status}")

        db_sub = Subscription(
            id=sub.id,
            user_id=current_user.id,
            stripe_customer_id=customer.id,
            price_id=price_id,
            status=SubscriptionStatus(sub.status),
            current_period_start=datetime.fromtimestamp(sub.current_period_start) if sub.current_period_start else None,
            current_period_end=datetime.fromtimestamp(sub.current_period_end) if sub.current_period_end else None,
            trial_start=datetime.fromtimestamp(sub.trial_start) if sub.trial_start else None,
            trial_end=datetime.fromtimestamp(sub.trial_end) if sub.trial_end else None,
        )

        logger.info("Saving subscription to database")
        db.add(db_sub)
        db.commit()
        db.refresh(db_sub)
        logger.info(f"Subscription saved successfully for user {current_user.id}")

        return SubscriptionResponse(
            id=sub.id,
            status=sub.status,
            plan_type=subs_data.plan_type,
            trial_end=db_sub.trial_end,
            current_period_end=db_sub.current_period_end,
            cancel_at_period_end=db_sub.cancel_at_period_end
        )

    except stripe.error.InvalidRequestError as e:
        db.rollback()
        logger.error(f"Stripe InvalidRequestError: {str(e)} | User message: {e.user_message}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Stripe invalid request: {e.user_message or str(e)}"
        )

    except stripe.error.StripeError as e:
        db.rollback()
        error_type = getattr(e, 'type', 'unknown')
        error_code = getattr(e, 'code', 'unknown')
        logger.error(
            f"Stripe error: {str(e)} | "
            f"User message: {e.user_message or 'No message'} | "
            f"Code: {error_code} | "
            f"Type: {error_type}"
        )
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Stripe error: {e.user_message or str(e)}"
        )

    except Exception as e:
        db.rollback()
        logger.exception(f"Unexpected error during subscription creation for user {current_user.id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )


@router.get("/me", response_model=SubscriptionResponse | dict)
def get_my_subscription(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Session = Depends(get_db)
):
    sub = db.query(Subscription).filter(Subscription.user_id == current_user.id).first()

    if not sub:
        return {"has_subscription": False, "message": "No active subscription found."}

    return SubscriptionResponse.from_orm(sub)


@router.post("/cancel", status_code=status.HTTP_200_OK)
def cancel_subscription(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Session = Depends(get_db)
):
    sub = db.query(Subscription).filter(Subscription.user_id == current_user.id).first()
    if not sub:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No subscription found")

    try:
        logger.info(f"Cancelling subscription {sub.id} for user {current_user.id}")
        stripe.Subscription.modify(sub.id, cancel_at_period_end=True)
        sub.cancel_at_period_end = True
        db.commit()
        return {"message": "Subscription will cancel at end of period"}
    except stripe.error.StripeError as e:
        logger.error(f"Stripe cancel error: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
    except Exception as e:
        logger.exception(f"Cancel error: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))