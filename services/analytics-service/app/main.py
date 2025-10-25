from fastapi import FastAPI, HTTPException, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, desc
import sys
import os
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
import pandas as pd

# Add libs to path
sys.path.append('/app')
from libs.common.database import get_db, init_db
from libs.common.models import AnalyticsEvent, User, Persona, Conversation, Organization
from libs.common.schemas import AnalyticsEventCreate, WeeklyReportResponse
from libs.common.auth import get_current_user

app = FastAPI(
    title="Bwenge OS Analytics Service",
    description="Analytics and reporting service",
    version="1.0.0"
)

# Initialize database on startup
@app.on_event("startup")
async def startup_event():
    init_db()

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "analytics-service"}

@app.post("/events")
async def track_event(
    event: AnalyticsEventCreate,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Track analytics event"""
    
    analytics_event = AnalyticsEvent(
        org_id=current_user["org_id"],
        user_id=current_user.get("sub"),
        event_type=event.event_type,
        payload=event.payload
    )
    
    db.add(analytics_event)
    db.commit()
    
    return {"message": "Event tracked successfully"}

@app.get("/orgs/{org_id}/reports/weekly", response_model=WeeklyReportResponse)
async def get_weekly_report(
    org_id: str,
    week_offset: int = Query(0, description="Weeks ago (0 = current week)"),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get weekly analytics report"""
    
    # Verify user belongs to organization
    if current_user["org_id"] != org_id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    # Calculate week boundaries
    today = datetime.utcnow().date()
    week_start = today - timedelta(days=today.weekday() + (7 * week_offset))
    week_end = week_start + timedelta(days=6)
    
    week_start_dt = datetime.combine(week_start, datetime.min.time())
    week_end_dt = datetime.combine(week_end, datetime.max.time())
    
    # Get message count
    message_events = db.query(AnalyticsEvent).filter(
        and_(
            AnalyticsEvent.org_id == org_id,
            AnalyticsEvent.event_type == "message_sent",
            AnalyticsEvent.timestamp >= week_start_dt,
            AnalyticsEvent.timestamp <= week_end_dt
        )
    ).count()
    
    # Get active users
    active_users = db.query(AnalyticsEvent.user_id).filter(
        and_(
            AnalyticsEvent.org_id == org_id,
            AnalyticsEvent.timestamp >= week_start_dt,
            AnalyticsEvent.timestamp <= week_end_dt
        )
    ).distinct().count()
    
    # Get top personas
    top_personas_query = db.query(
        AnalyticsEvent.persona_id,
        func.count(AnalyticsEvent.event_id).label('event_count')
    ).filter(
        and_(
            AnalyticsEvent.org_id == org_id,
            AnalyticsEvent.persona_id.isnot(None),
            AnalyticsEvent.timestamp >= week_start_dt,
            AnalyticsEvent.timestamp <= week_end_dt
        )
    ).group_by(AnalyticsEvent.persona_id).order_by(desc('event_count')).limit(5)
    
    top_personas = []
    for persona_id, count in top_personas_query:
        persona = db.query(Persona).filter(Persona.persona_id == persona_id).first()
        if persona:
            top_personas.append({
                "persona_id": str(persona_id),
                "name": persona.name,
                "interaction_count": count
            })
    
    # Get usage stats
    usage_stats = {
        "total_conversations": db.query(Conversation).filter(
            and_(
                Conversation.created_at >= week_start_dt,
                Conversation.created_at <= week_end_dt
            )
        ).count(),
        "avg_messages_per_conversation": 0,
        "peak_usage_day": None
    }
    
    # Calculate average messages per conversation
    conversations = db.query(Conversation).filter(
        and_(
            Conversation.created_at >= week_start_dt,
            Conversation.created_at <= week_end_dt
        )
    ).all()
    
    if conversations:
        total_messages = sum(len(conv.messages) for conv in conversations)
        usage_stats["avg_messages_per_conversation"] = total_messages / len(conversations)
    
    return WeeklyReportResponse(
        org_id=org_id,
        week_start=week_start_dt,
        week_end=week_end_dt,
        total_messages=message_events,
        active_users=active_users,
        top_personas=top_personas,
        usage_stats=usage_stats
    )

@app.get("/orgs/{org_id}/students/{student_id}/progress")
async def get_student_progress(
    org_id: str,
    student_id: str,
    days: int = Query(30, description="Number of days to analyze"),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get student progress analytics"""
    
    # Verify user belongs to organization
    if current_user["org_id"] != org_id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    # Calculate date range
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=days)
    
    # Get student events
    student_events = db.query(AnalyticsEvent).filter(
        and_(
            AnalyticsEvent.org_id == org_id,
            AnalyticsEvent.user_id == student_id,
            AnalyticsEvent.timestamp >= start_date,
            AnalyticsEvent.timestamp <= end_date
        )
    ).all()
    
    # Analyze engagement patterns
    daily_activity = {}
    persona_interactions = {}
    
    for event in student_events:
        day = event.timestamp.date().isoformat()
        if day not in daily_activity:
            daily_activity[day] = 0
        daily_activity[day] += 1
        
        if event.persona_id:
            persona_id = str(event.persona_id)
            if persona_id not in persona_interactions:
                persona_interactions[persona_id] = 0
            persona_interactions[persona_id] += 1
    
    # Get conversation data
    conversations = db.query(Conversation).filter(
        and_(
            Conversation.user_id == student_id,
            Conversation.created_at >= start_date,
            Conversation.created_at <= end_date
        )
    ).all()
    
    total_messages = sum(len(conv.messages) for conv in conversations)
    avg_conversation_length = total_messages / max(len(conversations), 1)
    
    # Calculate learning metrics (placeholder - customize based on your needs)
    learning_metrics = {
        "total_interactions": len(student_events),
        "total_conversations": len(conversations),
        "total_messages": total_messages,
        "avg_conversation_length": avg_conversation_length,
        "active_days": len(daily_activity),
        "engagement_score": min(100, (len(student_events) / days) * 10)  # Simple scoring
    }
    
    return {
        "student_id": student_id,
        "period": {
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
            "days": days
        },
        "learning_metrics": learning_metrics,
        "daily_activity": daily_activity,
        "persona_interactions": persona_interactions,
        "progress_trend": calculate_progress_trend(daily_activity)
    }

@app.get("/orgs/{org_id}/dashboard")
async def get_dashboard_data(
    org_id: str,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get dashboard analytics data"""
    
    # Verify user belongs to organization
    if current_user["org_id"] != org_id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    # Get current month data
    now = datetime.utcnow()
    month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    
    # Basic metrics
    total_users = db.query(User).filter(User.org_id == org_id).count()
    total_personas = db.query(Persona).filter(
        and_(Persona.org_id == org_id, Persona.is_active == True)
    ).count()
    
    monthly_messages = db.query(AnalyticsEvent).filter(
        and_(
            AnalyticsEvent.org_id == org_id,
            AnalyticsEvent.event_type == "message_sent",
            AnalyticsEvent.timestamp >= month_start
        )
    ).count()
    
    monthly_active_users = db.query(AnalyticsEvent.user_id).filter(
        and_(
            AnalyticsEvent.org_id == org_id,
            AnalyticsEvent.timestamp >= month_start
        )
    ).distinct().count()
    
    return {
        "overview": {
            "total_users": total_users,
            "total_personas": total_personas,
            "monthly_messages": monthly_messages,
            "monthly_active_users": monthly_active_users,
            "engagement_rate": (monthly_active_users / max(total_users, 1)) * 100
        },
        "recent_activity": get_recent_activity(org_id, db),
        "top_personas": get_top_personas(org_id, db, month_start)
    }

def calculate_progress_trend(daily_activity: Dict[str, int]) -> str:
    """Calculate progress trend from daily activity"""
    if len(daily_activity) < 2:
        return "insufficient_data"
    
    # Simple trend calculation
    dates = sorted(daily_activity.keys())
    first_half = dates[:len(dates)//2]
    second_half = dates[len(dates)//2:]
    
    first_half_avg = sum(daily_activity[d] for d in first_half) / len(first_half)
    second_half_avg = sum(daily_activity[d] for d in second_half) / len(second_half)
    
    if second_half_avg > first_half_avg * 1.1:
        return "improving"
    elif second_half_avg < first_half_avg * 0.9:
        return "declining"
    else:
        return "stable"

def get_recent_activity(org_id: str, db: Session, limit: int = 10) -> List[Dict]:
    """Get recent activity for organization"""
    recent_events = db.query(AnalyticsEvent).filter(
        AnalyticsEvent.org_id == org_id
    ).order_by(desc(AnalyticsEvent.timestamp)).limit(limit).all()
    
    return [
        {
            "event_type": event.event_type,
            "timestamp": event.timestamp.isoformat(),
            "user_id": str(event.user_id) if event.user_id else None,
            "persona_id": str(event.persona_id) if event.persona_id else None
        }
        for event in recent_events
    ]

def get_top_personas(org_id: str, db: Session, since: datetime, limit: int = 5) -> List[Dict]:
    """Get top personas by interaction count"""
    top_personas_query = db.query(
        AnalyticsEvent.persona_id,
        func.count(AnalyticsEvent.event_id).label('interaction_count')
    ).filter(
        and_(
            AnalyticsEvent.org_id == org_id,
            AnalyticsEvent.persona_id.isnot(None),
            AnalyticsEvent.timestamp >= since
        )
    ).group_by(AnalyticsEvent.persona_id).order_by(desc('interaction_count')).limit(limit)
    
    result = []
    for persona_id, count in top_personas_query:
        persona = db.query(Persona).filter(Persona.persona_id == persona_id).first()
        if persona:
            result.append({
                "persona_id": str(persona_id),
                "name": persona.name,
                "interaction_count": count
            })
    
    return result

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)