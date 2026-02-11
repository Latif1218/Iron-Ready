import stripe
import logging
from typing import Annotated
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from ..schemas.subs_schema import CreateSubscriptionRequest, SubscriptionResponse
from ..database import get_db
from ..models.user_model import User
from ..authentication.user_auth import get_current_user
from ..models.subs_model import Subscription, SubscriptionStatus
from ..config import (
    DOMAIN,
    STRIPE_SECRET_KEY,
    STRIPE_PUBLISHABLE_KEY,
    STRIPE_MONTHLY_PRICE_ID,
    STRIPE_YEARLY_PRICE_ID,
    STRIPE_WEBHOOK_SECRET
)

router = APIRouter(tags=["Subscription"])

stripe.api_key = STRIPE_SECRET_KEY
stripe.api_version = "2024-06-20"  # keep updated

logger = logging.getLogger(__name__)

# -------------------------------------------------------------------------
# Config for frontend
# -------------------------------------------------------------------------
@router.get("/config")
async def get_config():
    return {
        "publishableKey": STRIPE_PUBLISHABLE_KEY,
        "monthlyPrice": STRIPE_MONTHLY_PRICE_ID,
        "yearlyPrice": STRIPE_YEARLY_PRICE_ID,
    }


# -------------------------------------------------------------------------
# Create checkout session + save pending subscription
# -------------------------------------------------------------------------
@router.post("/checkout")
def create_subscription(
    plan_type: CreateSubscriptionRequest,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    if plan_type not in ["monthly", "yearly"]:
        raise HTTPException(
            status_code=400,
            detail="plan_type must be 'monthly' or 'yearly'"
        )

    price_id = STRIPE_MONTHLY_PRICE_ID if plan_type == "monthly" else STRIPE_YEARLY_PRICE_ID

    try:
        checkout_session = stripe.checkout.Session.create(
            mode="subscription",
            payment_method_types=["card"],
            customer_email=current_user.email,
            line_items=[{"price": price_id, "quantity": 1}],
            metadata={
                "user_id": str(current_user.id),
                "email": current_user.email,
                "plan_type": plan_type,
            },
            subscription_data={
                "metadata": {
                    "user_id": str(current_user.id),
                    "plan_type": plan_type,
                }
            },
            success_url=f"{DOMAIN.rstrip('/')}/static/success.html?session_id={{CHECKOUT_SESSION_ID}}",
            cancel_url=f"{DOMAIN.rstrip('/')}/static/canceled.html",
        )

        # Save INCOMPLETE subscription record
        subscription = Subscription(
            id=checkout_session.subscription,
            user_id=current_user.id,
            stripe_customer_id=checkout_session.customer,
            price_id=price_id,
            status=SubscriptionStatus.INCOMPLETE,
            cancel_at_period_end=False,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )

        db.add(subscription)
        db.commit()
        db.refresh(subscription)

        logger.info(f"Checkout session created → session={checkout_session.id} | sub={checkout_session.subscription} | user={current_user.id}")

        return RedirectResponse(
            url=checkout_session.url,
            status_code=status.HTTP_303_SEE_OTHER
        )

    except stripe.error.StripeError as e:
        raise HTTPException(
            status_code=400,
            detail=f"Payment failed: {str(e)}"
        ) from e
    except Exception:
        logger.exception("Unexpected error during checkout")
        raise HTTPException(
            status_code=500,
            detail="An unexpected error occurred"
        ) from None

# -------------------------------------------------------------------------
# Retrieve session (for success page, optional)
# -------------------------------------------------------------------------
@router.get("/checkout-session")
async def get_checkout_session(sessionId: str):
    try:
        session = stripe.checkout.Session.retrieve(sessionId)
        return {
            "id": session.id,
            "customer": session.customer,
            "subscription": session.subscription,
            "status": session.status,
            "payment_status": session.payment_status,
        }
    except stripe.error.StripeError as e:
        raise HTTPException(
            status_code=400,
            detail=f"Payment error: {e.user_message or str(e)}"
        ) from e

# -------------------------------------------------------------------------
# Customer Portal
# -------------------------------------------------------------------------
@router.post("/customer-portal")
async def customer_portal(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)]
):
    sub = db.query(Subscription).filter(Subscription.user_id == current_user.id).first()
    if not sub or not sub.stripe_customer_id:
        raise HTTPException(400, "No customer ID found. Make a purchase first.")

    try:
        portal_session = stripe.billing_portal.Session.create(
            customer=sub.stripe_customer_id,
            return_url=DOMAIN.rstrip("/") + "/",
        )
        return RedirectResponse(portal_session.url, status_code=status.HTTP_303_SEE_OTHER)
    except stripe.error.StripeError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Payment failed: {e.user_message or str(e)}"
        ) from e


# -------------------------------------------------------------------------
# Webhook – most important part
# -------------------------------------------------------------------------
@router.post("/webhook")
async def stripe_webhook(request: Request, db: Annotated[Session, Depends(get_db)]):
    payload = await request.body()
    sig_header = request.headers.get("stripe-signature")

    if not STRIPE_WEBHOOK_SECRET:
        raise HTTPException(500, "Webhook secret not configured")

    try:
        event = stripe.Webhook.construct_event(
            payload=payload,
            sig_header=sig_header,
            secret=STRIPE_WEBHOOK_SECRET
        )
    except stripe.error.SignatureVerificationError as e:
        logger.error("Webhook signature verification failed: %s", str(e))
        raise HTTPException(status_code=400, detail="Invalid signature") from e

    except ValueError as e:
        logger.error("Invalid webhook payload received: %s", str(e))
        raise HTTPException(status_code=400, detail="Invalid payload") from e

    except Exception:
        logger.exception("Unexpected error during checkout")
        raise HTTPException(
            status_code=500,
            detail="An unexpected error occurred"
        ) from None
    # Handle relevant events
    if event.type == "checkout.session.completed":
        session = event.data.object
        if session.mode != "subscription":
            return {"status": "ignored"}

        sub_id = session.subscription
        user_id = session.metadata.get("user_id") or session.subscription_data.metadata.get("user_id")

        if not user_id:
            logger.warning("No user_id in metadata")
            return {"status": "missing metadata"}

        # Retrieve fresh subscription object (periods are reliable here)
        try:
            stripe_sub = stripe.Subscription.retrieve(sub_id)
        except stripe.error.StripeError:
            stripe_sub = None

        sub = db.query(Subscription).filter(
            Subscription.stripe_subscription_id == sub_id
        ).first()

        if not sub:
            # Edge case: record might not exist → create it
            sub = Subscription(
                user_id=int(user_id),
                stripe_customer_id=session.customer,
                stripe_subscription_id=sub_id,
                price_id=session.subscription_details.plan.id if session.subscription_details else None,
                status=SubscriptionStatus.ACTIVE,
            )
            db.add(sub)

        if sub:
            sub.status = SubscriptionStatus.ACTIVE
            if stripe_sub:
                sub.current_period_start = datetime.fromtimestamp(stripe_sub.current_period_start) if stripe_sub.current_period_start else None
                sub.current_period_end   = datetime.fromtimestamp(stripe_sub.current_period_end)   if stripe_sub.current_period_end   else None
            sub.stripe_customer_id = session.customer or sub.stripe_customer_id
            sub.updated_at = datetime.utcnow()
            db.commit()
            logger.info(f"Subscription activated: {sub_id} | user: {user_id}")

    elif event.type in ("invoice.paid", "invoice.payment_failed", "customer.subscription.updated", "customer.subscription.deleted"):
        # You should handle these too in production
        obj = event.data.object
        sub_id = obj.id if event.type.startswith("customer.subscription") else obj.subscription

        sub = db.query(Subscription).filter(Subscription.stripe_subscription_id == sub_id).first()
        if sub:
            if event.type == "invoice.paid":
                sub.status = SubscriptionStatus.ACTIVE
            elif event.type == "invoice.payment_failed":
                sub.status = SubscriptionStatus.PAST_DUE
            elif event.type == "customer.subscription.updated":
                sub.status = obj.status
                sub.cancel_at_period_end = obj.cancel_at_period_end
            elif event.type == "customer.subscription.deleted":
                sub.status = SubscriptionStatus.CANCELED

            if hasattr(obj, "current_period_start"):
                sub.current_period_start = datetime.fromtimestamp(obj.current_period_start) if obj.current_period_start else None
                sub.current_period_end   = datetime.fromtimestamp(obj.current_period_end)   if obj.current_period_end   else None

            db.commit()
            logger.info(f"Updated sub {sub_id} via {event.type}")

    return {"status": "success"}





@router.get("/me", response_model=SubscriptionResponse | dict)
def get_my_subscription(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)]
):
    sub = db.query(Subscription).filter(Subscription.user_id == current_user.id).first()

    if not sub:
        return {"has_subscription": False, "message": "No active subscription found."}

    return SubscriptionResponse.from_orm(sub)



@router.post("/cancel", status_code=status.HTTP_200_OK)
def cancel_subscription(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)]
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
        logger.error("Stripe cancel error: %s", str(e), exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Stripe cancel failed: {str(e)}"
        ) from e

    except Exception:
        logger.exception("Unexpected error during cancel operation")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred while canceling"
        ) from None