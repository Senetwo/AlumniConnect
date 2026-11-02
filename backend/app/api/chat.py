
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user, get_db
from app.models.chat import Conversation, Message
from app.models.mentorship import Mentorship
from app.models.user import User
from app.models.network import UserBlock
from app.models.profile import Profile
from app.services.notification_service import create_notification

router = APIRouter(prefix="/api/chat", tags=["Chat"])


class MessageCreate(BaseModel):
    body: str = Field(min_length=1, max_length=5000)


class MessageResponse(BaseModel):
    id: int
    conversation_id: int
    sender_id: int
    body: str
    created_at: datetime
    read_at: datetime | None = None

    model_config = {"from_attributes": True}


class ConversationResponse(BaseModel):
    id: int
    mentorship_id: int
    mentor_id: int
    mentee_id: int
    created_at: datetime
    mentor_name: str = "Mentor"
    mentee_name: str = "Mentee"
    mentor_profile_picture_url: str | None = None
    mentee_profile_picture_url: str | None = None
    latest_message: str | None = None
    latest_message_at: datetime | None = None
    unread_count: int = 0

    model_config = {"from_attributes": True}


def require_participant(
    conversation_id: int,
    current_user: User,
    db: Session,
) -> Conversation:
    conversation = (
        db.query(Conversation)
        .filter(Conversation.id == conversation_id)
        .first()
    )

    if not conversation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found.",
        )

    if current_user.id not in (
        conversation.mentor_id,
        conversation.mentee_id,
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You cannot access this conversation.",
        )

    blocked = db.query(UserBlock.id).filter(
        ((UserBlock.blocker_id == conversation.mentor_id) & (UserBlock.blocked_id == conversation.mentee_id))
        | ((UserBlock.blocker_id == conversation.mentee_id) & (UserBlock.blocked_id == conversation.mentor_id))
    ).first()
    if blocked:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Messaging is unavailable between these members.")

    return conversation


@router.get("/unread-count")
def get_unread_message_count(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    count = (
        db.query(Message)
        .join(
            Conversation,
            Message.conversation_id == Conversation.id,
        )
        .filter(
            Message.sender_id != current_user.id,
            Message.read_at.is_(None),
            (
                (Conversation.mentor_id == current_user.id)
                | (Conversation.mentee_id == current_user.id)
            ),
        )
        .count()
    )

    return {"count": count}


@router.post(
    "/conversations/{mentorship_id}",
    response_model=ConversationResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_or_get_conversation(
    mentorship_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    mentorship = (
        db.query(Mentorship)
        .filter(
            Mentorship.id == mentorship_id,
            Mentorship.status == "accepted",
        )
        .first()
    )

    if not mentorship:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Accepted mentorship not found.",
        )

    if current_user.id not in (
        mentorship.mentor_id,
        mentorship.mentee_id,
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You cannot create a conversation for this mentorship.",
        )

    conversation = (
        db.query(Conversation)
        .filter(Conversation.mentorship_id == mentorship.id)
        .first()
    )

    if conversation:
        return conversation

    conversation = Conversation(
        mentorship_id=mentorship.id,
        mentor_id=mentorship.mentor_id,
        mentee_id=mentorship.mentee_id,
    )

    db.add(conversation)
    db.commit()
    db.refresh(conversation)

    return conversation


@router.get(
    "/conversations",
    response_model=list[ConversationResponse],
)
def list_conversations(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    accepted_mentorships = (
        db.query(Mentorship)
        .filter(
            Mentorship.status == "accepted",
            (Mentorship.mentor_id == current_user.id)
            | (Mentorship.mentee_id == current_user.id),
        )
        .order_by(Mentorship.responded_at.desc(), Mentorship.created_at.desc())
        .all()
    )

    needs_commit = False
    for mentorship in accepted_mentorships:
        conversation = db.query(Conversation).filter(
            Conversation.mentorship_id == mentorship.id
        ).first()
        if conversation is None:
            db.add(Conversation(
                mentorship_id=mentorship.id,
                mentor_id=mentorship.mentor_id,
                mentee_id=mentorship.mentee_id,
            ))
            needs_commit = True

    if needs_commit:
        try:
            db.commit()
        except IntegrityError:
            # Another participant may have opened the same accepted chat
            # simultaneously. The unique mentorship key keeps it singular.
            db.rollback()

    conversations = []
    for mentorship in accepted_mentorships:
        conversation = db.query(Conversation).filter(
            Conversation.mentorship_id == mentorship.id
        ).first()
        if conversation is None:
            continue
        if db.query(UserBlock.id).filter(
            ((UserBlock.blocker_id == mentorship.mentor_id) & (UserBlock.blocked_id == mentorship.mentee_id))
            | ((UserBlock.blocker_id == mentorship.mentee_id) & (UserBlock.blocked_id == mentorship.mentor_id))
        ).first():
            continue
        conversations.append((conversation, mentorship))

    response = []
    for conversation, mentorship in conversations:
        mentor = db.query(User).filter(User.id == mentorship.mentor_id).first()
        mentee = db.query(User).filter(User.id == mentorship.mentee_id).first()
        mentor_profile = db.query(Profile).filter(Profile.user_id == mentorship.mentor_id).first()
        mentee_profile = db.query(Profile).filter(Profile.user_id == mentorship.mentee_id).first()
        latest = db.query(Message).filter(
            Message.conversation_id == conversation.id
        ).order_by(Message.created_at.desc(), Message.id.desc()).first()
        unread_count = db.query(Message.id).filter(
            Message.conversation_id == conversation.id,
            Message.sender_id != current_user.id,
            Message.read_at.is_(None),
        ).count()
        response.append({
            "id": conversation.id,
            "mentorship_id": conversation.mentorship_id,
            "mentor_id": conversation.mentor_id,
            "mentee_id": conversation.mentee_id,
            "created_at": conversation.created_at,
            "mentor_name": mentor.full_name if mentor else "Mentor",
            "mentee_name": mentee.full_name if mentee else "Mentee",
            "mentor_profile_picture_url": mentor_profile.profile_picture_url if mentor_profile else None,
            "mentee_profile_picture_url": mentee_profile.profile_picture_url if mentee_profile else None,
            "latest_message": latest.body if latest else None,
            "latest_message_at": latest.created_at if latest else None,
            "unread_count": unread_count,
        })

    return response


@router.get(
    "/conversations/{conversation_id}/messages",
    response_model=list[MessageResponse],
)
def list_messages(
    conversation_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    require_participant(conversation_id, current_user, db)

    messages = (
        db.query(Message)
        .filter(Message.conversation_id == conversation_id)
        .order_by(Message.created_at.asc(), Message.id.asc())
        .all()
    )

    now = datetime.now(timezone.utc)
    for message in messages:
        if message.sender_id != current_user.id and message.read_at is None:
            message.read_at = now

    db.commit()

    return messages


@router.post(
    "/conversations/{conversation_id}/messages",
    response_model=MessageResponse,
    status_code=status.HTTP_201_CREATED,
)
def send_message(
    conversation_id: int,
    data: MessageCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    conversation = require_participant(
        conversation_id,
        current_user,
        db,
    )

    mentorship = (
        db.query(Mentorship)
        .filter(
            Mentorship.id == conversation.mentorship_id,
            Mentorship.status == "accepted",
        )
        .first()
    )

    if not mentorship:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Messaging is unavailable for this mentorship.",
        )

    body = data.body.strip()

    if not body:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Message cannot be empty.",
        )

    recent_messages = db.query(Message.id).filter(
        Message.sender_id == current_user.id,
        Message.created_at >= datetime.now(timezone.utc) - timedelta(hours=1),
    ).count()
    if recent_messages >= 60:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="You have sent many messages recently. Please try again later.",
        )

    message = Message(
        conversation_id=conversation_id,
        sender_id=current_user.id,
        body=body,
    )

    
    db.add(message)
    db.flush()

    recipient_id = (
        conversation.mentee_id
        if current_user.id == conversation.mentor_id
        else conversation.mentor_id
    )

    create_notification(
        db,
        user_id=recipient_id,
        notification_type="new_message",
        title="New chat message",
        message="You have received a new mentorship chat message.",
        resource_type="conversation",
        resource_id=conversation.id,
    )

    db.commit()
    db.refresh(message)

    return message

