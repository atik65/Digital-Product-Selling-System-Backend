from datetime import datetime, timezone
from sqlalchemy import Column, DateTime, Boolean
from sqlalchemy.sql import func
from app.core.database import Base


class BaseAuditModel(Base):
    """
    Abstract base model that equips entities with audit timestamps
    (created_at, updated_at) and soft-delete capabilities (is_deleted, deleted_at).
    """

    __abstract__ = True

    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        server_default=func.now(),
        nullable=False,
    )
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        server_default=func.now(),
        nullable=False,
    )
    is_deleted = Column(
        Boolean,
        default=False,
        server_default=func.false(),
        nullable=False,
        index=True,
    )
    deleted_at = Column(DateTime(timezone=True), nullable=True)

    def soft_delete(self) -> None:
        """Marks the record as deleted and timestamps the action without removing the row."""
        self.is_deleted = True
        self.deleted_at = datetime.now(timezone.utc)

    def restore(self) -> None:
        """Restores a soft-deleted record back to active state."""
        self.is_deleted = False
        self.deleted_at = None
