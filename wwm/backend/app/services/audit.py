from sqlalchemy.orm import Session

from app.models import AuditLog


def write_audit(db: Session, actor: str, action: str, entity_type: str, entity_id: str, detail: dict | None = None) -> None:
    db.add(
        AuditLog(
            actor=actor,
            action=action,
            entity_type=entity_type,
            entity_id=entity_id,
            detail=detail,
        )
    )
