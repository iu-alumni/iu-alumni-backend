from sqlalchemy.orm import Session

from app.models.settings import Setting


def get_event_settings(db: Session):
    """Get event settings from the database"""
    settings = db.query(Setting).filter(Setting.key == "event_settings").first()
    if not settings:
        # Create default settings if they don't exist
        settings = Setting(key="event_settings", value={"auto_approve": True})
        db.add(settings)
        db.commit()
        db.refresh(settings)
    return settings.value


def update_auto_approve_setting(db: Session, auto_approve: bool):
    """Update the auto_approve setting"""
    settings = db.query(Setting).filter(Setting.key == "event_settings").first()
    if not settings:
        settings = Setting(key="event_settings", value={"auto_approve": auto_approve})
        db.add(settings)
    else:
        event_settings = dict(settings.value)
        event_settings["auto_approve"] = auto_approve
        settings.value = event_settings

    db.commit()
    db.refresh(settings)
    return settings.value
