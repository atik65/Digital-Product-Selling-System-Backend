from typing import Optional
from sqlalchemy.orm import Session
from sqlalchemy import or_
from app.models.user import User
from app.core.exceptions import DatabaseException


class UserRepository:
    """Repository handling all database queries for User entity."""

    def get_by_id(
        self, db: Session, user_id: int, include_deleted: bool = False
    ) -> Optional[User]:
        query = db.query(User).filter(User.id == user_id)
        if not include_deleted:
            query = query.filter(User.is_deleted.is_(False))
        return query.first()

    def get_by_email(
        self, db: Session, email: str, include_deleted: bool = False
    ) -> Optional[User]:
        query = db.query(User).filter(User.email == email)
        if not include_deleted:
            query = query.filter(User.is_deleted.is_(False))
        return query.first()

    def get_by_username(
        self, db: Session, username: str, include_deleted: bool = False
    ) -> Optional[User]:
        query = db.query(User).filter(User.username == username)
        if not include_deleted:
            query = query.filter(User.is_deleted.is_(False))
        return query.first()

    def get_by_email_or_username(
        self, db: Session, identifier: str, include_deleted: bool = False
    ) -> Optional[User]:
        """Finds an active user matching either their email or username."""
        query = db.query(User).filter(
            or_(User.email == identifier, User.username == identifier)
        )
        if not include_deleted:
            query = query.filter(User.is_deleted.is_(False))
        return query.first()

    def create(self, db: Session, user_dict: dict) -> User:
        db_user = User(**user_dict)
        try:
            db.add(db_user)
            db.commit()
            db.refresh(db_user)
            return db_user
        except Exception as e:
            db.rollback()
            raise DatabaseException(
                f"Database error during user creation: {str(e)}",
                original_exception=e,
            )

    def delete(
        self, db: Session, user_id: int, hard_delete: bool = False
    ) -> Optional[User]:
        user = self.get_by_id(db, user_id)
        if user:
            try:
                if hard_delete:
                    db.delete(user)
                else:
                    user.soft_delete()
                db.commit()
            except Exception as e:
                db.rollback()
                raise DatabaseException(
                    f"Database error during user deletion: {str(e)}",
                    original_exception=e,
                )
        return user
