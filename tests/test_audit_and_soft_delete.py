from datetime import datetime
from app.repositories.product_repository import ProductRepository
from app.repositories.user_repository import UserRepository
from app.core.security import hash_password


def test_product_audit_fields_and_soft_delete(db):
    repo = ProductRepository()

    # 1. Create product and check audit timestamps
    product_data = {
        "name": "Audit Test Monitor",
        "slug": "audit-test-monitor",
        "description": "High refresh rate",
    }
    product = repo.create(db, product_data)

    assert product.id is not None
    assert product.created_at is not None
    assert product.updated_at is not None
    assert product.is_deleted is False
    assert product.deleted_at is None
    assert isinstance(product.created_at, datetime)

    # 2. Soft delete the product
    deleted = repo.delete(db, product.id)
    assert deleted is not None
    assert deleted.is_deleted is True
    assert deleted.deleted_at is not None

    # 3. Verify normal lookup hides soft-deleted product
    found = repo.get_by_id(db, product.id)
    assert found is None

    # 4. Verify lookup with include_deleted=True still finds it in DB
    found_with_deleted = repo.get_by_id(db, product.id, include_deleted=True)
    assert found_with_deleted is not None
    assert found_with_deleted.is_deleted is True

    # 5. Restore the product
    restored = repo.restore(db, product.id)
    assert restored.is_deleted is False
    assert restored.deleted_at is None

    # Verify normal lookup finds it again
    assert repo.get_by_id(db, product.id) is not None


def test_user_soft_delete(db):
    user_repo = UserRepository()

    # 1. Create a user
    user_dict = {
        "email": "softdelete@example.com",
        "username": "softuser",
        "hashed_password": hash_password("pass123"),
        "role": "user",
        "is_active": True,
    }
    user = user_repo.create(db, user_dict)
    assert user.is_deleted is False
    assert user.created_at is not None
    assert user.updated_at is not None

    # 2. Soft delete the user
    user_repo.delete(db, user.id)

    # 3. Verify user is excluded from normal queries
    assert user_repo.get_by_id(db, user.id) is None
    assert user_repo.get_by_email(db, "softdelete@example.com") is None
    assert user_repo.get_by_username(db, "softuser") is None
    assert user_repo.get_by_email_or_username(db, "softdelete@example.com") is None

    # 4. But row still exists in DB
    raw_user = user_repo.get_by_id(db, user.id, include_deleted=True)
    assert raw_user is not None
    assert raw_user.is_deleted is True
    assert raw_user.deleted_at is not None
