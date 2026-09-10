from app.models.category import Category
from app.models.product import Product
from app.models.user import User
from app.models.wallet import Wallet
from scripts.seed import seed_users_and_wallets, seed_catalog


def test_seed_users_creation_and_idempotence(db):
    seed_users_and_wallets(db)

    admin = db.query(User).filter(User.email == "admin@example.com").first()
    assert admin is not None
    assert admin.role == "admin"
    assert admin.username == "admin"

    customer = db.query(User).filter(User.email == "user@example.com").first()
    assert customer is not None
    assert customer.role == "customer"

    wallet = db.query(Wallet).filter(Wallet.user_id == customer.id).first()
    assert wallet is not None
    assert wallet.balance >= 1000.0

    # Test idempotence
    seed_users_and_wallets(db)
    assert db.query(User).filter(User.email == "admin@example.com").count() == 1


def test_seed_catalog_creation_and_idempotence(db):
    seed_catalog(db)

    categories = db.query(Category).all()
    assert len(categories) >= 3

    products = db.query(Product).all()
    assert len(products) >= 3

    # Test idempotence
    seed_catalog(db)
    assert db.query(Category).count() == len(categories)

