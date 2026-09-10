from app.models.product import Product
from app.models.user import User
from scripts.seed import seed_products, seed_users


def test_seed_users_creation_and_idempotence(db):
    # 1. Run seed_users for the first time
    seed_users(db)

    admin = db.query(User).filter(User.email == "admin@example.com").first()
    assert admin is not None
    assert admin.role == "admin"
    assert admin.username == "admin"

    user = db.query(User).filter(User.email == "user@example.com").first()
    assert user is not None
    assert user.role == "user"

    # 2. Run seed_users a second time to ensure idempotency (no duplicate errors)
    seed_users(db)
    total_admins = db.query(User).filter(User.email == "admin@example.com").count()
    assert total_admins == 1


def test_seed_products_creation_and_idempotence(db):
    # 1. Run seed_products for the first time
    seed_products(db)

    products = db.query(Product).all()
    assert len(products) == 8

    # 2. Run seed_products a second time to ensure idempotency
    seed_products(db)
    assert db.query(Product).count() == 8
