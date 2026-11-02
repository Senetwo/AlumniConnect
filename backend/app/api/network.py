from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy import or_, and_
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user, get_db, require_role
from app.models.network import ConnectionRequest, UserBlock, UserReport, NetworkMessage, Announcement
from app.models.profile import Profile
from app.models.user import User
from app.models.notifications import Notification
from app.services.notification_service import create_notification

router = APIRouter(tags=["Community"])


class ConnectionCreate(BaseModel):
    user_id: int


class ReportCreate(BaseModel):
    user_id: int
    reason: str = Field(min_length=3, max_length=60)
    details: str | None = Field(default=None, max_length=2000)


class MessageCreate(BaseModel):
    body: str = Field(min_length=1, max_length=5000)


class AnnouncementCreate(BaseModel):
    title: str = Field(min_length=3, max_length=160)
    body: str = Field(min_length=10, max_length=4000)


def _blocked(db: Session, a: int, b: int) -> bool:
    return db.query(UserBlock.id).filter(or_(
        and_(UserBlock.blocker_id == a, UserBlock.blocked_id == b),
        and_(UserBlock.blocker_id == b, UserBlock.blocked_id == a),
    )).first() is not None


def _connection(db: Session, connection_id: int, user_id: int) -> ConnectionRequest:
    row = db.query(ConnectionRequest).filter(ConnectionRequest.id == connection_id).first()
    if not row:
        raise HTTPException(404, "Connection not found")
    if user_id not in (row.requester_id, row.recipient_id):
        raise HTTPException(403, "You cannot access this connection")
    return row


@router.get("/api/directory")
def list_directory(
    career_domain: str | None = Query(default=None, max_length=100),
    skill: str | None = Query(default=None, max_length=100),
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=20, ge=1, le=50),
    current: User = Depends(get_current_user), db: Session = Depends(get_db),
):
    query = db.query(Profile, User).join(User, User.id == Profile.user_id).filter(
        Profile.directory_visible.is_(True), User.is_active.is_(True), User.id != current.id,
        or_(User.role.in_(["mentor", "mentee", "admin"]), User.community_role.in_(["mentor", "mentee"])),
    )
    if career_domain and career_domain.strip():
        query = query.filter(Profile.career_domain.ilike(f"%{career_domain.strip()}%"))
    if skill and skill.strip():
        query = query.filter(Profile.skills.ilike(f"%{skill.strip()}%"))
    blocked_ids = db.query(UserBlock.blocked_id).filter(UserBlock.blocker_id == current.id).union(
        db.query(UserBlock.blocker_id).filter(UserBlock.blocked_id == current.id)
    )
    query = query.filter(~User.id.in_(blocked_ids))
    rows = query.order_by(User.full_name.asc(), User.id.asc()).offset(offset).limit(limit + 1).all()
    connections = db.query(ConnectionRequest).filter(
        or_(ConnectionRequest.requester_id == current.id, ConnectionRequest.recipient_id == current.id)
    ).order_by(ConnectionRequest.updated_at.desc()).all()
    connection_items = []
    for connection in connections:
        other_id = connection.recipient_id if connection.requester_id == current.id else connection.requester_id
        if _blocked(db, current.id, other_id):
            continue
        other = db.query(User).filter(User.id == other_id).first()
        connection_items.append({
            "id": connection.id,
            "status": connection.status,
            "requester_id": connection.requester_id,
            "recipient_id": connection.recipient_id,
            "other_user": {"id": other.id, "full_name": other.full_name, "role": other.community_role or other.role} if other else None,
        })
    return {
        "items": [{
            "user_id": user.id, "full_name": user.full_name, "role": user.community_role or user.role,
            "career_domain": profile.career_domain, "career_path": profile.career_path,
            "experience": profile.experience,
            "skills": [item.strip() for item in (profile.skills or "").split(",") if item.strip()],
            "bio": profile.bio, "profile_picture_url": profile.profile_picture_url,
        } for profile, user in rows[:limit]],
        "has_more": len(rows) > limit,
        "offset": offset,
        "limit": limit,
        "connections": connection_items,
    }


@router.patch("/api/profiles/me/directory-visibility")
def set_directory_visibility(enabled: bool, current: User = Depends(get_current_user), db: Session = Depends(get_db)):
    profile = db.query(Profile).filter(Profile.user_id == current.id).first()
    if not profile:
        raise HTTPException(404, "Profile not found")
    was_visible = profile.directory_visible
    profile.directory_visible = enabled
    if enabled and not was_visible:
        members = db.query(User).filter(User.is_active.is_(True), or_(User.role.in_(["mentor", "mentee", "admin"]), User.community_role.in_(["mentor", "mentee"])), User.id != current.id).all()
        for member in members:
            create_notification(
                db,
                user_id=member.id,
                notification_type="new_directory_member",
                title="New profile in the Community Directory",
                message=f"{current.full_name} added a profile to the member directory.",
                resource_type="profile",
                resource_id=profile.id,
            )
    db.commit()
    return {"directory_visible": profile.directory_visible}


@router.post("/api/connections", status_code=201)
def request_connection(data: ConnectionCreate, current: User = Depends(get_current_user), db: Session = Depends(get_db)):
    target = db.query(User).filter(User.id == data.user_id, User.is_active.is_(True), or_(User.role.in_(["mentor", "mentee", "admin"]), User.community_role.in_(["mentor", "mentee"]))).first()
    if not target or target.id == current.id:
        raise HTTPException(404, "Member not found")
    visible_profile = db.query(Profile.id).filter(Profile.user_id == target.id, Profile.directory_visible.is_(True)).first()
    if not visible_profile:
        raise HTTPException(404, "Member not found")
    if _blocked(db, current.id, target.id):
        raise HTTPException(403, "This member is unavailable")
    pair_low, pair_high = sorted((current.id, target.id))
    row = db.query(ConnectionRequest).filter(ConnectionRequest.pair_low_id == pair_low, ConnectionRequest.pair_high_id == pair_high).first()
    now = datetime.now(timezone.utc)
    recent_requests = db.query(ConnectionRequest.id).filter(ConnectionRequest.requester_id == current.id, ConnectionRequest.created_at >= now - timedelta(days=1)).count()
    if not row and recent_requests >= 30:
        raise HTTPException(429, "Daily connection request limit reached. Try again tomorrow.")
    if row:
        if row.status == "accepted":
            raise HTTPException(409, "You are already connected")
        if row.status == "pending":
            if row.requester_id == target.id:
                row.status = "accepted"
                row.updated_at = now
                db.commit()
                db.refresh(row)
                return {"id": row.id, "status": row.status, "requester_id": row.requester_id, "recipient_id": row.recipient_id}
            raise HTTPException(409, "A request is already pending")
        row.requester_id, row.recipient_id, row.status, row.created_at, row.updated_at = current.id, target.id, "pending", now, now
    else:
        row = ConnectionRequest(pair_low_id=pair_low, pair_high_id=pair_high, requester_id=current.id, recipient_id=target.id, status="pending")
        db.add(row)
    db.commit()
    db.refresh(row)
    db.add(Notification(user_id=target.id, type="connection_request", title="New connection request", message=f"{current.full_name} would like to connect.", resource_type="connection", resource_id=row.id))
    db.commit()
    return {"id": row.id, "status": row.status, "requester_id": row.requester_id, "recipient_id": row.recipient_id}


@router.get("/api/connections")
def list_connections(current: User = Depends(get_current_user), db: Session = Depends(get_db)):
    rows = db.query(ConnectionRequest).filter(or_(ConnectionRequest.requester_id == current.id, ConnectionRequest.recipient_id == current.id)).order_by(ConnectionRequest.updated_at.desc()).all()
    result = []
    for row in rows:
        other_id = row.recipient_id if row.requester_id == current.id else row.requester_id
        if _blocked(db, current.id, other_id):
            continue
        other = db.query(User).filter(User.id == other_id).first()
        result.append({"id": row.id, "status": row.status, "requester_id": row.requester_id, "recipient_id": row.recipient_id, "other_user": {"id": other.id, "full_name": other.full_name, "role": other.community_role or other.role} if other else None})
    return result


@router.patch("/api/connections/{connection_id}/{action}")
def update_connection(connection_id: int, action: str, current: User = Depends(get_current_user), db: Session = Depends(get_db)):
    row = _connection(db, connection_id, current.id)
    now = datetime.now(timezone.utc)
    if action in ("accept", "decline"):
        if row.recipient_id != current.id or row.status != "pending":
            raise HTTPException(409, "Only the recipient may act on a pending request")
        row.status = "accepted" if action == "accept" else "declined"
        if action == "accept":
            db.add(Notification(user_id=row.requester_id, type="connection_accepted", title="Connection accepted", message=f"{current.full_name} accepted your connection request.", resource_type="connection", resource_id=row.id))
    elif action == "cancel":
        if row.requester_id != current.id or row.status != "pending":
            raise HTTPException(409, "Only the requester may cancel a pending request")
        row.status = "cancelled"
    elif action == "disconnect":
        if row.status != "accepted":
            raise HTTPException(409, "Only an accepted connection can be removed")
        row.status = "disconnected"
    else:
        raise HTTPException(404, "Unknown connection action")
    row.updated_at = now
    db.commit()
    return {"id": row.id, "status": row.status}


@router.post("/api/connections/{connection_id}/messages", status_code=201)
def send_network_message(connection_id: int, data: MessageCreate, current: User = Depends(get_current_user), db: Session = Depends(get_db)):
    row = _connection(db, connection_id, current.id)
    other_id = row.recipient_id if row.requester_id == current.id else row.requester_id
    if row.status != "accepted" or _blocked(db, current.id, other_id):
        raise HTTPException(403, "Messaging requires an active connection")
    body = data.body.strip()
    if not body:
        raise HTTPException(422, "Message cannot be empty")
    if db.query(NetworkMessage.id).filter(NetworkMessage.sender_id == current.id, NetworkMessage.created_at >= datetime.now(timezone.utc) - timedelta(hours=1)).count() >= 60:
        raise HTTPException(429, "Hourly message limit reached. Please try again later.")
    message = NetworkMessage(connection_id=row.id, sender_id=current.id, body=body)
    db.add(message)
    db.add(Notification(user_id=other_id, type="new_message", title="New community message", message=f"{current.full_name} sent you a message.", resource_type="connection", resource_id=row.id))
    db.commit()
    db.refresh(message)
    return {"id": message.id, "connection_id": message.connection_id, "sender_id": message.sender_id, "body": message.body, "created_at": message.created_at}


@router.get("/api/connections/{connection_id}/messages")
def list_network_messages(connection_id: int, before_id: int | None = Query(default=None, gt=0), limit: int = Query(default=50, ge=1, le=100), current: User = Depends(get_current_user), db: Session = Depends(get_db)):
    row = _connection(db, connection_id, current.id)
    other_id = row.recipient_id if row.requester_id == current.id else row.requester_id
    if row.status != "accepted" or _blocked(db, current.id, other_id):
        raise HTTPException(403, "Messaging requires an active connection")
    query = db.query(NetworkMessage).filter(NetworkMessage.connection_id == row.id)
    if before_id:
        query = query.filter(NetworkMessage.id < before_id)
    rows = query.order_by(NetworkMessage.id.desc()).limit(limit).all()
    return [{"id": m.id, "connection_id": m.connection_id, "sender_id": m.sender_id, "body": m.body, "created_at": m.created_at} for m in reversed(rows)]


@router.post("/api/members/{user_id}/block", status_code=201)
def block_member(user_id: int, current: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if user_id == current.id or not db.query(User.id).filter(User.id == user_id).first():
        raise HTTPException(404, "Member not found")
    existing = db.query(UserBlock).filter(UserBlock.blocker_id == current.id, UserBlock.blocked_id == user_id).first()
    if not existing:
        db.add(UserBlock(blocker_id=current.id, blocked_id=user_id))
    pair_low, pair_high = sorted((current.id, user_id))
    connection = db.query(ConnectionRequest).filter(ConnectionRequest.pair_low_id == pair_low, ConnectionRequest.pair_high_id == pair_high).first()
    if connection:
        connection.status = "disconnected"
        connection.updated_at = datetime.now(timezone.utc)
    db.commit()
    return {"blocked": True}


@router.post("/api/members/report", status_code=201)
def report_member(data: ReportCreate, current: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if data.user_id == current.id or not db.query(User.id).filter(User.id == data.user_id).first():
        raise HTTPException(404, "Member not found")
    if db.query(UserReport.id).filter(UserReport.reporter_id == current.id, UserReport.created_at >= datetime.now(timezone.utc) - timedelta(days=1)).count() >= 5:
        raise HTTPException(429, "Daily report limit reached. Contact an administrator if this is urgent.")
    db.add(UserReport(reporter_id=current.id, reported_id=data.user_id, reason=data.reason.strip(), details=data.details.strip() if data.details else None))
    db.commit()
    return {"message": "Report sent to the moderation team."}


@router.get("/api/admin/reports")
def list_reports(current: User = Depends(require_role("admin")), db: Session = Depends(get_db)):
    rows = db.query(UserReport).order_by(UserReport.created_at.desc()).limit(200).all()
    return [{"id": r.id, "reporter_id": r.reporter_id, "reported_id": r.reported_id, "reason": r.reason, "details": r.details, "status": r.status, "created_at": r.created_at} for r in rows]


@router.post("/api/admin/announcements", status_code=201)
def create_announcement(data: AnnouncementCreate, current: User = Depends(require_role("admin")), db: Session = Depends(get_db)):
    title, body = data.title.strip(), data.body.strip()
    if len(title) < 3 or len(body) < 10:
        raise HTTPException(422, "Announcement title and message cannot be blank")
    announcement = Announcement(author_id=current.id, title=title, body=body)
    db.add(announcement)
    db.flush()
    members = db.query(User.id).filter(User.id != current.id).all()
    db.bulk_save_objects([Notification(user_id=member.id, type="announcement", title=announcement.title, message=announcement.body, resource_type="announcement", resource_id=announcement.id) for member in members])
    db.commit()
    db.refresh(announcement)
    return {"id": announcement.id, "title": announcement.title, "body": announcement.body, "created_at": announcement.created_at, "recipient_count": len(members)}


@router.get("/api/announcements")
def list_announcements(offset: int = Query(default=0, ge=0), limit: int = Query(default=20, ge=1, le=50), current: User = Depends(get_current_user), db: Session = Depends(get_db)):
    rows = db.query(Announcement).order_by(Announcement.created_at.desc()).offset(offset).limit(limit).all()
    return [{"id": a.id, "title": a.title, "body": a.body, "created_at": a.created_at} for a in rows]

