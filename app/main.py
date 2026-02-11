from fastapi import FastAPI, status, HTTPException
from .database import Base, engine
from .routers import register_user, user, onboarding, subscription, workout_plan, recoveries, notificatiions
from fastapi import Request
import stripe
from .config import STRIPE_SECRET_KEY, STRIPE_WEBHOOK_SECRET

Base.metadata.create_all(bind=engine)

app = FastAPI()

@app.get('/health', status_code=status.HTTP_200_OK)
def health():
    return HTTPException(
        status_code=status.HTTP_200_OK,
        detail="API is healthy and running correctly.",
        headers={"Iron_Ready Healthcheack": "healthy"}
    )


stripe.api_key = STRIPE_SECRET_KEY

@app.post("/stripe/webhook")
async def stripe_webhook(request: Request):
    payload = await request.body()
    sig = request.headers.get("stripe-signature")

    try:
        event = stripe.Webhook.construct_event(
            payload, sig, STRIPE_WEBHOOK_SECRET
        )
    except Exception as e:
        print("Webhook error:", e)
        return {"error": "invalid signature"}

    print("EVENT:", event["type"])
    return {"ok": True}


    
app.include_router(register_user.router)
app.include_router(user.router)
app.include_router(onboarding.router)
app.include_router(subscription.router)
app.include_router(workout_plan.router)
app.include_router(recoveries.router)
app.include_router(notificatiions.router)