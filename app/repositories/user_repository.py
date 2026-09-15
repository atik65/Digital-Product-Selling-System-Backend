from typing import Optional
from sqlalchemy.orm import Session
from app.models.user import User
from app.schemas.pagination import PaginationParams
from app.utils.pagination import get_paginated_response
from app.core.exceptions import DatabaseException


class UserRepository:
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
        query = db.query(User).filter(
            (User.email == identifier) | (User.username == identifier)
        )
        if not include_deleted:
            query = query.filter(User.is_deleted.is_(False))
        return query.first()

    def get_by_google_id(
        self, db: Session, google_id: str, include_deleted: bool = False
    ) -> Optional[User]:
        query = db.query(User).filter(User.google_id == google_id)
        if not include_deleted:
            query = query.filter(User.is_deleted.is_(False))
        return query.first()

    def create(self, db: Session, user_data: dict) -> User:
        user = User(**user_data)
        try:
            db.add(user)
            db.commit()
            db.refresh(user)
            return user
        except Exception as e:
            db.rollback()
            raise DatabaseException(
                f"Failed to create user: {str(e)}", original_exception=e
            )

    def create_user(
        self,
        db: Session,
        email: str,
        hashed_password: str,
        username: str,
        role: str = "user",
        name: Optional[str] = None,
    ) -> User:
        user = User(
            email=email,
            hashed_password=hashed_password,
            username=username,
            role=role,
            name=name,
            is_active=True,
        )
        try:
            db.add(user)
            db.commit()
            db.refresh(user)
            return user
        except Exception as e:
            db.rollback()
            raise DatabaseException(
                f"Failed to create user: {str(e)}", original_exception=e
            )

    def update(self, db: Session, user: User, update_data: dict) -> User:
        try:
            for key, value in update_data.items():
                if value is not None and hasattr(user, key):
                    setattr(user, key, value)
            db.commit()
            db.refresh(user)
            return user
        except Exception as e:
            db.rollback()
            raise DatabaseException(
                f"Failed to update user: {str(e)}", original_exception=e
            )

    def delete(self, db: Session, user_id: int) -> bool:
        try:
            user = self.get_by_id(db, user_id)
            if not user:
                return False
            user.soft_delete()
            db.commit()
            db.refresh(user)
            return True
        except Exception as e:
            db.rollback()
            raise DatabaseException(
                f"Failed to soft delete user: {str(e)}", original_exception=e
            )

    def restore(self, db: Session, user_id: int) -> Optional[User]:
        try:
            user = self.get_by_id(db, user_id, include_deleted=True)
            if not user:
                return None
            user.restore()
            db.commit()
            db.refresh(user)
            return user
        except Exception as e:
            db.rollback()
            raise DatabaseException(
                f"Failed to restore user: {str(e)}", original_exception=e
            )

    def get_users(
        self,
        db: Session,
        pagination: PaginationParams,
        search: Optional[str] = None,
        is_active: Optional[bool] = None,
    ):
        try:
            query = db.query(User).filter(User.is_deleted.is_(False))
            if search:
                query = query.filter(
                    (User.email.ilike(f"%{search}%"))
                    | (User.name.ilike(f"%{search}%"))
                    | (User.username.ilike(f"%{search}%"))
                )
            if is_active is not None:
                query = query.filter(User.is_active == is_active)

            total = query.count()
            items = (
                query.order_by(User.id.desc())
                .offset(pagination.offset)
                .limit(pagination.size)
                .all()
            )
            return get_paginated_response(items, total, pagination)
        except Exception as e:
            raise DatabaseException(
                f"Failed to query users: {str(e)}", original_exception=e
            )
