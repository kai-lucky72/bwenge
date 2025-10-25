from fastapi import FastAPI, HTTPException, Depends, Request
from sqlalchemy.orm import Session
import sys
import os
import stripe
from datetime import datetime
import json

# Add libs to path
sys.path.append('/app')
from libs.common.database import get_db, init_db
from libs.common.models import Subscription, Organization, UsageQuota
from libs.common.schemas import SubscriptionCreate, SubscriptionResponse, WebhookEvent
from libs.common.auth import get_current_user

app = FastAPI(
    title="Bwenge OS Payments Service",
    description="Payment and subscription management service",
    version="1.0.0"
)

# Configure Stripe
stripe.api_key = os.getenv("STRIPE_SECRET_KEY")
STRIPE_WEBHOOK_SECRET = os.getenv("STRIPE_WEBHOOK_SECRET")

# Subscription plans
SUBSCRIPTION_PLANS = {
    "free": {
        "name": "Free Plan",
        "price": 0,
        "stripe_price_id": None,
        "quotas": {
            "messages": 100,
            "storage": 100 * 1024 * 1024,  # 100MB
            "users": 5
        }
    },
    "basic": {
        "name": "Basic Plan",
        "price": 29,
        "stripe_price_id": os.getenv("STRIPE_BASIC_PRICE_ID"),
        "quotas": {
            "messages": 1000,
            "storage": 1024 * 1024 * 1024,  # 1GB
            "users": 25
        }
    },
    "pro": {
        "name": "Pro Plan",
        "price": 99,
        "stripe_price_id": os.getenv("STRIPE_PRO_PRICE_ID"),
        "quotas": {
            "messages": 10000,
            "storage": 10 * 1024 * 1024 * 1024,  # 10GB
            "users": 100
        }
    },
    "enterprise": {
        "name": "Enterprise Plan",
        "price": 299,
        "stripe_price_id": os.getenv("STRIPE_ENTERPRISE_PRICE_ID"),
        "quotas": {
            "messages": -1,  # Unlimited
            "storage": -1,   # Unlimited
            "users": -1      # Unlimited
        }
    }
}

# Initialize database on startup
@app.on_event("startup")
async def startup_event():
    init_db()

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "payments-service"}

@app.post("/payments/subscribe", response_model=SubscriptionResponse)
async def create_subscription(
    subscription_data: SubscriptionCreate,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create subscription checkout session"""
    
    # Validate plan
    if subscription_data.plan_name not in SUBSCRIPTION_PLANS:
        raise HTTPException(status_code=400, detail="Invalid subscription plan")
    
    plan = SUBSCRIPTION_PLANS[subscription_data.plan_name]
    
    # Free plan doesn't require Stripe
    if subscription_data.plan_name == "free":
        return await create_free_subscription(current_user["org_id"], db)
    
    if not plan["stripe_price_id"]:
        raise HTTPException(status_code=400, detail="Plan not configured")
    
    try:
        # Get organization
        org = db.query(Organization).filter(
            Organization.org_id == current_user["org_id"]
        ).first()
        
        if not org:
            raise HTTPException(status_code=404, detail="Organization not found")
        
        # Create Stripe checkout session
        checkout_session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            line_items=[{
                'price': plan["stripe_price_id"],
                'quantity': 1,
            }],
            mode='subscription',
            success_url=subscription_data.success_url,
            cancel_url=subscription_data.cancel_url,
            client_reference_id=str(current_user["org_id"]),
            metadata={
                'org_id': str(current_user["org_id"]),
                'plan_name': subscription_data.plan_name
            }
        )
        
        # Create pending subscription record
        subscription = Subscription(
            org_id=current_user["org_id"],
            status="pending",
            plan_name=subscription_data.plan_name
        )
        
        db.add(subscription)
        db.commit()
        db.refresh(subscription)
        
        return SubscriptionResponse(
            checkout_url=checkout_session.url,
            subscription_id=subscription.subscription_id
        )
        
    except stripe.error.StripeError as e:
        raise HTTPException(status_code=400, detail=f"Stripe error: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Subscription creation failed: {str(e)}")

async def create_free_subscription(org_id: str, db: Session) -> SubscriptionResponse:
    """Create free subscription"""
    
    # Check if organization already has a subscription
    existing_sub = db.query(Subscription).filter(
        Subscription.org_id == org_id
    ).first()
    
    if existing_sub:
        raise HTTPException(status_code=400, detail="Organization already has a subscription")
    
    # Create free subscription
    subscription = Subscription(
        org_id=org_id,
        status="active",
        plan_name="free",
        current_period_start=datetime.utcnow(),
        current_period_end=datetime.utcnow().replace(year=datetime.utcnow().year + 1)
    )
    
    db.add(subscription)
    
    # Create usage quotas
    plan = SUBSCRIPTION_PLANS["free"]
    for quota_type, limit_value in plan["quotas"].items():
        quota = UsageQuota(
            org_id=org_id,
            quota_type=quota_type,
            limit_value=limit_value,
            used_value=0
        )
        db.add(quota)
    
    db.commit()
    db.refresh(subscription)
    
    return SubscriptionResponse(
        checkout_url="",  # No checkout needed for free plan
        subscription_id=subscription.subscription_id
    )

@app.post("/webhooks/payment")
async def handle_stripe_webhook(request: Request, db: Session = Depends(get_db)):
    """Handle Stripe webhooks"""
    
    payload = await request.body()
    sig_header = request.headers.get('stripe-signature')
    
    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, STRIPE_WEBHOOK_SECRET
        )
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid payload")
    except stripe.error.SignatureVerificationError:
        raise HTTPException(status_code=400, detail="Invalid signature")
    
    # Handle the event
    if event['type'] == 'checkout.session.completed':
        await handle_checkout_completed(event['data']['object'], db)
    elif event['type'] == 'invoice.payment_succeeded':
        await handle_payment_succeeded(event['data']['object'], db)
    elif event['type'] == 'customer.subscription.updated':
        await handle_subscription_updated(event['data']['object'], db)
    elif event['type'] == 'customer.subscription.deleted':
        await handle_subscription_cancelled(event['data']['object'], db)
    
    return {"status": "success"}

async def handle_checkout_completed(session, db: Session):
    """Handle successful checkout"""
    
    org_id = session.get('client_reference_id')
    if not org_id:
        return
    
    # Get the subscription from Stripe
    stripe_subscription = stripe.Subscription.retrieve(session['subscription'])
    
    # Update our subscription record
    subscription = db.query(Subscription).filter(
        Subscription.org_id == org_id,
        Subscription.status == "pending"
    ).first()
    
    if subscription:
        subscription.stripe_subscription_id = stripe_subscription.id
        subscription.status = "active"
        subscription.current_period_start = datetime.fromtimestamp(
            stripe_subscription.current_period_start
        )
        subscription.current_period_end = datetime.fromtimestamp(
            stripe_subscription.current_period_end
        )
        
        # Update organization plan
        org = db.query(Organization).filter(Organization.org_id == org_id).first()
        if org:
            org.plan = subscription.plan_name
        
        # Create/update usage quotas
        await update_usage_quotas(org_id, subscription.plan_name, db)
        
        db.commit()

async def handle_payment_succeeded(invoice, db: Session):
    """Handle successful payment"""
    
    subscription_id = invoice.get('subscription')
    if not subscription_id:
        return
    
    # Update subscription period
    subscription = db.query(Subscription).filter(
        Subscription.stripe_subscription_id == subscription_id
    ).first()
    
    if subscription:
        stripe_subscription = stripe.Subscription.retrieve(subscription_id)
        subscription.current_period_start = datetime.fromtimestamp(
            stripe_subscription.current_period_start
        )
        subscription.current_period_end = datetime.fromtimestamp(
            stripe_subscription.current_period_end
        )
        subscription.status = "active"
        
        # Reset usage quotas for new period
        await reset_usage_quotas(str(subscription.org_id), db)
        
        db.commit()

async def handle_subscription_updated(stripe_subscription, db: Session):
    """Handle subscription updates"""
    
    subscription = db.query(Subscription).filter(
        Subscription.stripe_subscription_id == stripe_subscription['id']
    ).first()
    
    if subscription:
        subscription.status = stripe_subscription['status']
        subscription.current_period_start = datetime.fromtimestamp(
            stripe_subscription['current_period_start']
        )
        subscription.current_period_end = datetime.fromtimestamp(
            stripe_subscription['current_period_end']
        )
        
        db.commit()

async def handle_subscription_cancelled(stripe_subscription, db: Session):
    """Handle subscription cancellation"""
    
    subscription = db.query(Subscription).filter(
        Subscription.stripe_subscription_id == stripe_subscription['id']
    ).first()
    
    if subscription:
        subscription.status = "cancelled"
        
        # Downgrade to free plan
        org = db.query(Organization).filter(
            Organization.org_id == subscription.org_id
        ).first()
        if org:
            org.plan = "free"
        
        # Update quotas to free plan limits
        await update_usage_quotas(str(subscription.org_id), "free", db)
        
        db.commit()

async def update_usage_quotas(org_id: str, plan_name: str, db: Session):
    """Update usage quotas for organization"""
    
    plan = SUBSCRIPTION_PLANS.get(plan_name, SUBSCRIPTION_PLANS["free"])
    
    for quota_type, limit_value in plan["quotas"].items():
        quota = db.query(UsageQuota).filter(
            UsageQuota.org_id == org_id,
            UsageQuota.quota_type == quota_type
        ).first()
        
        if quota:
            quota.limit_value = limit_value
        else:
            quota = UsageQuota(
                org_id=org_id,
                quota_type=quota_type,
                limit_value=limit_value,
                used_value=0
            )
            db.add(quota)

async def reset_usage_quotas(org_id: str, db: Session):
    """Reset usage quotas for new billing period"""
    
    quotas = db.query(UsageQuota).filter(
        UsageQuota.org_id == org_id,
        UsageQuota.reset_period == "monthly"
    ).all()
    
    for quota in quotas:
        quota.used_value = 0
        quota.last_reset = datetime.utcnow()

@app.get("/subscriptions/current")
async def get_current_subscription(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get current subscription for organization"""
    
    subscription = db.query(Subscription).filter(
        Subscription.org_id == current_user["org_id"]
    ).first()
    
    if not subscription:
        return {"plan": "none", "status": "inactive"}
    
    # Get usage quotas
    quotas = db.query(UsageQuota).filter(
        UsageQuota.org_id == current_user["org_id"]
    ).all()
    
    quota_info = {}
    for quota in quotas:
        quota_info[quota.quota_type] = {
            "limit": quota.limit_value,
            "used": quota.used_value,
            "percentage": (quota.used_value / max(quota.limit_value, 1)) * 100 if quota.limit_value > 0 else 0
        }
    
    return {
        "subscription_id": subscription.subscription_id,
        "plan": subscription.plan_name,
        "status": subscription.status,
        "current_period_start": subscription.current_period_start,
        "current_period_end": subscription.current_period_end,
        "quotas": quota_info
    }

@app.get("/plans")
async def list_subscription_plans():
    """List available subscription plans"""
    
    plans = []
    for plan_id, plan_info in SUBSCRIPTION_PLANS.items():
        plans.append({
            "id": plan_id,
            "name": plan_info["name"],
            "price": plan_info["price"],
            "quotas": plan_info["quotas"]
        })
    
    return {"plans": plans}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)