
from app.models.notifications import Notification


def create_notification(
    db,
    *,
    user_id: int,
    notification_type: str,
    title: str,
    message: str,
    resource_type: str | None = None,
    resource_id: int | None = None,
) -> Notification:
    notification = Notification(
        user_id=user_id,
        type=notification_type,
        title=title,
        message=message,
        resource_type=resource_type,
        resource_id=resource_id,
    )
    db.add(notification)
    return notification
