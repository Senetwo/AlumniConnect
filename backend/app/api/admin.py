from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy import func, or_
from sqlalchemy.orm import Session

from app.core.dependencies import get_db, require_role
from app.models.admin_action import AdminActionAudit
from app.models.knowledge_resource import KnowledgeResource
from app.models.mentorship import Mentorship
from app.models.network import ConnectionRequest, UserReport
from app.models.profile import Profile
from app.models.user import User

router = APIRouter(prefix="/api/admin", tags=["Administration"])


def _community_role(user):
    return user.community_role or (user.role if user.role in ("mentor", "mentee") else None)


@router.get("/dashboard")
def dashboard(_admin: User = Depends(require_role("admin")), db: Session = Depends(get_db)):
    now = datetime.now(timezone.utc)
    start = now - timedelta(days=29)
    member_filter = or_(User.role != "admin", User.community_role.in_(["mentor", "mentee"]))
    total_members = db.query(User.id).filter(member_filter).count()
    new_members = db.query(User.id).filter(User.created_at >= start, member_filter).count()
    registrations = db.query(User.created_at).filter(User.created_at >= start, member_filter).all()
    by_day = {}
    for (created_at,) in registrations:
        by_day[created_at.date().isoformat()] = by_day.get(created_at.date().isoformat(), 0) + 1
    mentorship_counts = {status: count for status, count in db.query(Mentorship.status, func.count(Mentorship.id)).group_by(Mentorship.status).all()}
    published = db.query(KnowledgeResource.id).filter(KnowledgeResource.is_published.is_(True)).count()
    drafts = db.query(KnowledgeResource.id).filter(KnowledgeResource.is_published.is_(False)).count()
    connections_30d = db.query(ConnectionRequest.id).filter(ConnectionRequest.created_at >= start).count()
    reports_open = db.query(UserReport.id).filter(UserReport.status == "open").count()
    return {
        "window": {"start": start.date().isoformat(), "end": now.date().isoformat(), "days": 30},
        "metrics": {
            "total_members": total_members,
            "new_members_30d": new_members,
            "active_members": None,
            "active_mentorships": mentorship_counts.get("accepted", 0),
            "mentorships": {key: mentorship_counts.get(key, 0) for key in ("pending", "accepted", "declined")},
            "published_resources": published,
            "draft_resources": drafts,
            "knowledge_engagement": None,
            "community_connections_30d": connections_30d,
            "open_reports": reports_open,
        },
        "registration_trend": [{"date": (start.date() + timedelta(days=i)).isoformat(), "count": by_day.get((start.date() + timedelta(days=i)).isoformat(), 0)} for i in range(30)],
        "data_notes": {"active_members": "Unavailable: the account model does not record last activity.", "knowledge_engagement": "Unavailable: resource view or engagement events are not tracked."},
    }


@router.get("/users")
def list_users(search: str = Query("", max_length=160), role: str = Query("all"), status: str = Query("all"), offset: int = Query(0, ge=0), limit: int = Query(25, ge=1, le=100), _admin: User = Depends(require_role("admin")), db: Session = Depends(get_db)):
    query = db.query(User).outerjoin(Profile, Profile.user_id == User.id)
    if search.strip():
        term = f"%{search.strip()}%"
        query = query.filter(or_(User.full_name.ilike(term), User.email.ilike(term)))
    if role in ("admin", "mentor", "mentee"):
        query = query.filter(or_(User.role == role, User.community_role == role))
    if status == "active":
        query = query.filter(User.is_active.is_(True))
    elif status == "suspended":
        query = query.filter(User.is_active.is_(False))
    total = query.count()
    users = query.order_by(User.created_at.desc()).offset(offset).limit(limit).all()
    return {"items": [{"id": u.id, "full_name": u.full_name, "email": u.email, "role": u.role, "community_role": _community_role(u), "is_active": u.is_active, "is_email_verified": u.is_email_verified, "created_at": u.created_at, "directory_visible": bool(u.profile and u.profile.directory_visible), "career_domain": u.profile.career_domain if u.profile else None} for u in users], "total": total, "offset": offset, "limit": limit}


class StatusChange(BaseModel):
    is_active: bool


class RoleChange(BaseModel):
    role: str = Field(pattern="^(mentor|mentee|admin)$")


def _audit(db, actor, target, action, details):
    db.add(AdminActionAudit(actor_id=actor.id, target_user_id=target.id if target else None, action=action, details=details))


@router.patch("/users/{user_id}/status")
def set_user_status(user_id: int, body: StatusChange, admin: User = Depends(require_role("admin")), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(404, "Member not found")
    if user.id == admin.id and not body.is_active:
        raise HTTPException(409, "You cannot suspend your own administrator account")
    if user.role == "admin" and not body.is_active:
        active_admins = db.query(User.id).filter(User.role == "admin", User.is_active.is_(True)).count()
        if active_admins <= 1:
            raise HTTPException(409, "The last active administrator cannot be suspended")
    old = user.is_active
    user.is_active = body.is_active
    _audit(db, admin, user, "account_status_changed", f"is_active: {old} -> {body.is_active}")
    db.commit()
    return {"id": user.id, "is_active": user.is_active}


@router.patch("/users/{user_id}/role")
def set_user_role(user_id: int, body: RoleChange, admin: User = Depends(require_role("admin")), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(404, "Member not found")
    if user.id == admin.id:
        raise HTTPException(409, "You cannot change your own administrator role")
    if user.role == "admin" and body.role != "admin" and db.query(User.id).filter(User.role == "admin", User.is_active.is_(True)).count() <= 1:
        raise HTTPException(409, "The last administrator cannot be demoted")
    old = user.role
    if old in ("mentor", "mentee") and body.role == "admin":
        user.community_role = old
    user.role = body.role
    _audit(db, admin, user, "role_changed", f"role: {old} -> {body.role}; community_role: {_community_role(user) or 'none'}")
    db.commit()
    return {"id": user.id, "role": user.role, "community_role": _community_role(user)}


@router.get("/mentorships")
def list_mentorships(status: str = Query("all"), offset: int = Query(0, ge=0), limit: int = Query(50, ge=1, le=100), _admin: User = Depends(require_role("admin")), db: Session = Depends(get_db)):
    query = db.query(Mentorship)
    if status in ("pending", "accepted", "declined"):
        query = query.filter(Mentorship.status == status)
    total = query.count()
    rows = query.order_by(Mentorship.created_at.desc()).offset(offset).limit(limit).all()
    users = {u.id: u.full_name for u in db.query(User).all()}
    return {"items": [{"id": m.id, "mentee": users.get(m.mentee_id, "Unknown member"), "mentor": users.get(m.mentor_id, "Unknown member"), "status": m.status, "created_at": m.created_at, "responded_at": m.responded_at} for m in rows], "total": total}


@router.get("/audit")
def get_audit(offset: int = Query(0, ge=0), limit: int = Query(50, ge=1, le=100), _admin: User = Depends(require_role("admin")), db: Session = Depends(get_db)):
    rows = db.query(AdminActionAudit).order_by(AdminActionAudit.created_at.desc()).offset(offset).limit(limit).all()
    ids = {r.actor_id for r in rows} | {r.target_user_id for r in rows if r.target_user_id}
    names = {u.id: u.full_name for u in db.query(User).filter(User.id.in_(ids)).all()} if ids else {}
    return [{"id": r.id, "action": r.action, "actor": names.get(r.actor_id, "Former member"), "target": names.get(r.target_user_id, "—"), "details": r.details, "created_at": r.created_at} for r in rows]


@router.patch("/reports/{report_id}")
def update_report(report_id: int, status: str = Query(..., pattern="^(open|reviewed|resolved)$"), admin: User = Depends(require_role("admin")), db: Session = Depends(get_db)):
    report = db.query(UserReport).filter(UserReport.id == report_id).first()
    if not report:
        raise HTTPException(404, "Report not found")
    old = report.status
    report.status = status
    _audit(db, admin, None, "report_status_changed", f"report_id={report.id}; {old} -> {status}")
    db.commit()
    return {"id": report.id, "status": report.status}
