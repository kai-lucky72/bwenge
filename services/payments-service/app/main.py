from fastapi import FastAPI, HTTPException, Depends, Request
from sqlalchemy.orm import Session
from sqlalchemy import Column, String, Integer, Float, DateTime, Boolean, Text
import sys
import os
from datetime import datetime, timedelta
import json
import uuid
from typing import Optional

# Add libs to path
sys.path.append('/app')
from libs.common.database import get_db, init_db, Base
from libs.common.models import Subscription, Organization, UsageQuota
from libs.common.schemas import SubscriptionCreate, SubscriptionResponse
from libs.common.auth import get_current_user

app = FastAPI(
    title="Bwenge OS Payments Service",
    description="Database-based payment and subscription management service for local development",
    version="1.0.0"
)

# Local Payment Transaction Model for Rwanda
class PaymentTransaction(Base):
    __tablename__ = "payment_transactions"
    
    transaction_id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    org_id = Column(String(36), nullable=False)
    amount = Column(Float, nullable=False)
    currency = Column(String(3), default="RWF")  # Rwandan Franc
    payment_method = Column(String(50), nullable=False)  # momo, airtel, bank, cash
    phone_number = Column(String(20), nullable=True)  # For mobile money
    reference_number = Column(String(100), nullable=True)
    status = Column(String(20), default="pending")  # pending, completed, failed, cancelled
    plan_name = Column(String(50), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)
    notes = Column(Text, nullable=True)

# Subscription plans (Rwanda pricing in RWF)
SUBSCRIPTION_PLANS = {
    "free": {
        "name": "Ubwoba (Free)",
        "price": 0,
        "price_usd": 0,
        "quotas": {
            "messages": 100,
            "storage": 100 * 1024 * 1024,  # 100MB
            "users": 5
        }
    },
    "basic": {
        "name": "Ibanze (Basic)",
        "price": 30000,  # 30,000 RWF (~$30)
        "price_usd": 30,
        "quotas": {
            "messages": 1000,
            "storage": 1024 * 1024 * 1024,  # 1GB
            "users": 25
        }
    },
    "pro": {
        "name": "Nyampinga (Pro)",
        "price": 100000,  # 100,000 RWF (~$100)
        "price_usd": 100,
        "quotas": {
            "messages": 10000,
            "storage": 10 * 1024 * 1024 * 1024,  # 10GB
            "users": 100
        }
    },
    "enterprise": {
        "name": "Ikigo (Enterprise)",
        "price": 300000,  # 300,000 RWF (~$300)
        "price_usd": 300,
        "quotas": {
            "messages": -1,  # Unlimited
            "storage": -1,   # Unlimited
            "users": -1      # Unlimited
        }
    }
}

# Rwanda payment methods
PAYMENT_METHODS = {
    "momo": "MTN Mobile Money",
    "airtel": "Airtel Money", 
    "bank": "Bank Transfer",
    "cash": "Cash Payment",
    "tigo": "Tigo Cash"
}

# Initialize database on startup
@app.on_event("startup")
async def startup_event():
    init_db()

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "payments-service"}

@app.post("/payments/subscribe")
async def create_subscription(
    subscription_data: dict,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create subscription with local payment simulation"""
    
    plan_name = subscription_data.get("plan_name")
    payment_method = subscription_data.get("payment_method", "momo")
    phone_number = subscription_data.get("phone_number")
    
    # Validate plan
    if plan_name not in SUBSCRIPTION_PLANS:
        raise HTTPException(status_code=400, detail="Invalid subscription plan")
    
    plan = SUBSCRIPTION_PLANS[plan_name]
    
    # Free plan doesn't require payment
    if plan_name == "free":
        return await create_free_subscription(current_user["org_id"], db)
    
    # Validate payment method
    if payment_method not in PAYMENT_METHODS:
        raise HTTPException(status_code=400, detail="Invalid payment method")
    
    # For mobile money, phone number is required
    if payment_method in ["momo", "airtel", "tigo"] and not phone_number:
        raise HTTPException(status_code=400, detail="Phone number required for mobile money")
    
    try:
        # Get organization
        org = db.query(Organization).filter(
            Organization.org_id == current_user["org_id"]
        ).first()
        
        if not org:
            raise HTTPException(status_code=404, detail="Organization not found")
        
        # Create payment transaction
        transaction = PaymentTransaction(
            org_id=current_user["org_id"],
            amount=plan["price"],
            payment_method=payment_method,
            phone_number=phone_number,
            plan_name=plan_name,
            reference_number=f"BWG-{datetime.now().strftime('%Y%m%d')}-{str(uuid.uuid4())[:8].upper()}",
            status="pending"
        )
        
        db.add(transaction)
        db.commit()
        db.refresh(transaction)
        
        # Create pending subscription record
        subscription = Subscription(
            org_id=current_user["org_id"],
            status="pending",
            plan_name=plan_name
        )
        
        db.add(subscription)
        db.commit()
        db.refresh(subscription)
        
        return {
            "transaction_id": transaction.transaction_id,
            "subscription_id": subscription.subscription_id,
            "amount": transaction.amount,
            "currency": "RWF",
            "payment_method": PAYMENT_METHODS[payment_method],
            "reference_number": transaction.reference_number,
            "status": "pending",
            "instructions": get_payment_instructions(payment_method, transaction.amount, transaction.reference_number, phone_number),
            "message": f"Payment initiated for {plan['name']} plan. Please complete payment using the instructions provided."
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Subscription creation failed: {str(e)}")

def get_payment_instructions(payment_method: str, amount: float, reference: str, phone_number: str = None) -> dict:
    """Get payment instructions for different methods"""
    
    instructions = {
        "momo": {
            "steps": [
                "Dial *182# on your MTN phone",
                "Select option 1 (Send Money)",
                "Enter merchant code: 123456",
                f"Enter amount: {amount:,.0f} RWF",
                f"Enter reference: {reference}",
                "Confirm payment with your PIN"
            ],
            "alternative": f"Or send {amount:,.0f} RWF to 123456 with reference {reference}"
        },
        "airtel": {
            "steps": [
                "Dial *175# on your Airtel phone", 
                "Select Pay Bill",
                "Enter merchant code: 654321",
                f"Enter amount: {amount:,.0f} RWF",
                f"Enter reference: {reference}",
                "Confirm with your PIN"
            ]
        },
        "bank": {
            "steps": [
                "Visit any bank branch or use online banking",
                "Transfer to Account: 1234567890",
                "Account Name: Bwenge OS Ltd",
                "Bank: Bank of Kigali",
                f"Amount: {amount:,.0f} RWF",
                f"Reference: {reference}"
            ]
        },
        "cash": {
            "steps": [
                "Visit our office in Kigali",
                "Address: KG 123 St, Gasabo District",
                f"Pay {amount:,.0f} RWF cash",
                f"Mention reference: {reference}",
                "Get receipt for confirmation"
            ]
        },
        "tigo": {
            "steps": [
                "Dial *505# on your Tigo phone",
                "Select Pay Bill", 
                "Enter merchant code: 789012",
                f"Enter amount: {amount:,.0f} RWF",
                f"Enter reference: {reference}",
                "Confirm payment"
            ]
        }
    }
    
    return instructions.get(payment_method, {})

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

@app.post("/payments/simulate-completion/{transaction_id}")
async def simulate_payment_completion(
    transaction_id: str,
    completion_data: dict,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Simulate payment completion (for development/testing)"""
    
    # Get transaction
    transaction = db.query(PaymentTransaction).filter(
        PaymentTransaction.transaction_id == transaction_id,
        PaymentTransaction.org_id == current_user["org_id"]
    ).first()
    
    if not transaction:
        raise HTTPException(status_code=404, detail="Transaction not found")
    
    if transaction.status != "pending":
        raise HTTPException(status_code=400, detail="Transaction already processed")
    
    # Simulate payment completion
    success = completion_data.get("success", True)
    
    if success:
        transaction.status = "completed"
        transaction.completed_at = datetime.utcnow()
        
        # Activate subscription
        subscription = db.query(Subscription).filter(
            Subscription.org_id == current_user["org_id"],
            Subscription.status == "pending"
        ).first()
        
        if subscription:
            subscription.status = "active"
            subscription.current_period_start = datetime.utcnow()
            subscription.current_period_end = datetime.utcnow() + timedelta(days=30)
            
            # Update organization plan
            org = db.query(Organization).filter(
                Organization.org_id == current_user["org_id"]
            ).first()
            if org:
                org.plan = subscription.plan_name
            
            # Create/update usage quotas
            await update_usage_quotas(current_user["org_id"], subscription.plan_name, db)
        
        db.commit()
        
        return {
            "status": "success",
            "message": "Payment completed successfully",
            "transaction_id": transaction_id,
            "subscription_activated": True
        }
    else:
        transaction.status = "failed"
        transaction.notes = completion_data.get("reason", "Payment failed")
        db.commit()
        
        return {
            "status": "failed", 
            "message": "Payment failed",
            "transaction_id": transaction_id,
            "reason": transaction.notes
        }

@app.get("/payments/transactions")
async def list_transactions(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """List payment transactions for organization"""
    
    transactions = db.query(PaymentTransaction).filter(
        PaymentTransaction.org_id == current_user["org_id"]
    ).order_by(PaymentTransaction.created_at.desc()).all()
    
    return {
        "transactions": [
            {
                "transaction_id": t.transaction_id,
                "amount": t.amount,
                "currency": t.currency,
                "payment_method": PAYMENT_METHODS.get(t.payment_method, t.payment_method),
                "reference_number": t.reference_number,
                "status": t.status,
                "plan_name": t.plan_name,
                "created_at": t.created_at,
                "completed_at": t.completed_at,
                "notes": t.notes
            }
            for t in transactions
        ]
    }

@app.get("/payments/methods")
async def list_payment_methods():
    """List available payment methods in Rwanda"""
    
    return {
        "methods": [
            {
                "id": method_id,
                "name": method_name,
                "type": "mobile_money" if method_id in ["momo", "airtel", "tigo"] else "traditional",
                "available": True
            }
            for method_id, method_name in PAYMENT_METHODS.items()
        ]
    }

@app.post("/payments/cancel-subscription")
async def cancel_subscription(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Cancel current subscription"""
    
    subscription = db.query(Subscription).filter(
        Subscription.org_id == current_user["org_id"],
        Subscription.status == "active"
    ).first()
    
    if not subscription:
        raise HTTPException(status_code=404, detail="No active subscription found")
    
    # Cancel subscription
    subscription.status = "cancelled"
    
    # Downgrade to free plan
    org = db.query(Organization).filter(
        Organization.org_id == current_user["org_id"]
    ).first()
    if org:
        org.plan = "free"
    
    # Update quotas to free plan limits
    await update_usage_quotas(current_user["org_id"], "free", db)
    
    db.commit()
    
    return {
        "status": "success",
        "message": "Subscription cancelled successfully. Downgraded to free plan.",
        "new_plan": "free"
    }

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