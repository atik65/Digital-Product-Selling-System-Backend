import sys
from pathlib import Path
from datetime import datetime, timezone, timedelta

# Fix Windows console encoding for Unicode/Emojis
if sys.platform == "win32" and hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

# Add project root directory to Python path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.core.database import SessionLocal
from app.core.security import hash_password
from app.models.user import User
from app.models.category import Category
from app.models.product import Product
from app.models.product_input_field import ProductInputField
from app.models.package import Package
from app.models.payment_method import PaymentMethod
from app.models.coupon import Coupon
from app.models.wallet import Wallet
from app.models.wallet_transaction import WalletTransaction
from app.models.marketing import Banner
from app.models.setting import SiteSetting
from app.models.lottery import Lottery, LotteryPrize


def seed_users_and_wallets(db) -> None:
    users_data = [
        {
            "email": "admin@example.com",
            "username": "admin",
            "name": "Super Admin",
            "plain_password": "admin123",
            "role": "admin",
            "is_active": True,
        },
        {
            "email": "user@example.com",
            "username": "customer",
            "name": "Regular Customer",
            "plain_password": "user123",
            "role": "customer",
            "is_active": True,
        },
    ]

    for u_info in users_data:
        user = db.query(User).filter(User.email == u_info["email"]).first()
        if not user:
            user = User(
                email=u_info["email"],
                username=u_info["username"],
                name=u_info["name"],
                hashed_password=hash_password(u_info["plain_password"]),
                role=u_info["role"],
                is_active=u_info["is_active"],
            )
            db.add(user)
            db.commit()
            db.refresh(user)
            print(f"  [CREATED] User '{user.username}' ({user.email}) [{user.role}]")

        # Ensure wallet with 1000 initial balance for testing
        wallet = db.query(Wallet).filter(Wallet.user_id == user.id).first()
        if not wallet:
            wallet = Wallet(user_id=user.id, balance=1000.0)
            db.add(wallet)
            db.flush()
            tx = WalletTransaction(
                wallet_id=wallet.id,
                type="BONUS",
                amount=1000.0,
                balance_before=0.0,
                balance_after=1000.0,
                description="Welcome initial testing balance",
            )
            db.add(tx)
            db.commit()
            print(f"  [CREATED] Initial wallet with 1000.0 BDT for {user.username}")


def seed_catalog(db) -> None:
    categories_data = [
        {
            "name": "Streaming",
            "slug": "streaming",
            "description": "OTT and entertainment platforms",
            "sort_order": 1,
        },
        {
            "name": "Productivity",
            "slug": "productivity",
            "description": "Design, work and utility subscriptions",
            "sort_order": 2,
        },
        {
            "name": "Gaming",
            "slug": "gaming",
            "description": "In-game currencies and top-ups",
            "sort_order": 3,
        },
    ]

    cat_map = {}
    for c_data in categories_data:
        cat = db.query(Category).filter(Category.slug == c_data["slug"]).first()
        if not cat:
            cat = Category(**c_data)
            db.add(cat)
            db.commit()
            db.refresh(cat)
            print(f"  [CREATED] Category '{cat.name}'")
        cat_map[cat.slug] = cat.id

    products_data = [
        {
            "category_id": cat_map["streaming"],
            "name": "Netflix Premium",
            "slug": "netflix-premium",
            "description": "4K Ultra HD private and shared profiles.",
            "instructions": "Enter your account email or profile name. Delivery in 10-30 mins.",
            "sort_order": 1,
            "fields": [
                {
                    "name": "account_email",
                    "label": "Account Email",
                    "type": "email",
                    "placeholder": "user@gmail.com",
                    "is_required": True,
                    "sort_order": 1,
                },
                {
                    "name": "profile_name",
                    "label": "Profile Name",
                    "type": "text",
                    "placeholder": "e.g. My Profile",
                    "is_required": False,
                    "sort_order": 2,
                },
            ],
            "packages": [
                {
                    "name": "1 Month Ultra HD",
                    "price": 450.0,
                    "compare_price": 550.0,
                    "duration": "30 Days",
                    "sort_order": 1,
                },
                {
                    "name": "3 Months Ultra HD",
                    "price": 1250.0,
                    "compare_price": 1500.0,
                    "duration": "90 Days",
                    "sort_order": 2,
                },
            ],
        },
        {
            "category_id": cat_map["productivity"],
            "name": "Canva Pro",
            "slug": "canva-pro",
            "description": "Premium design tools, templates, and unlimited cloud storage.",
            "instructions": "Enter the email associated with your Canva account.",
            "sort_order": 2,
            "fields": [
                {
                    "name": "canva_email",
                    "label": "Canva Account Email",
                    "type": "email",
                    "placeholder": "user@canva.com",
                    "is_required": True,
                    "sort_order": 1,
                },
            ],
            "packages": [
                {
                    "name": "1 Year Invite",
                    "price": 350.0,
                    "compare_price": 500.0,
                    "duration": "1 Year",
                    "sort_order": 1,
                },
                {
                    "name": "Lifetime Educational",
                    "price": 600.0,
                    "compare_price": 900.0,
                    "duration": "Lifetime",
                    "sort_order": 2,
                },
            ],
        },
        {
            "category_id": cat_map["gaming"],
            "name": "Free Fire Diamonds",
            "slug": "free-fire-diamonds",
            "description": "Instant game top-up via Player ID.",
            "instructions": "Provide your in-game Player ID carefully.",
            "sort_order": 3,
            "fields": [
                {
                    "name": "player_id",
                    "label": "Player ID (UID)",
                    "type": "number",
                    "placeholder": "e.g. 192847291",
                    "is_required": True,
                    "sort_order": 1,
                },
            ],
            "packages": [
                {
                    "name": "115 Diamonds",
                    "price": 85.0,
                    "compare_price": 95.0,
                    "duration": "Instant",
                    "sort_order": 1,
                },
                {
                    "name": "575 Diamonds",
                    "price": 420.0,
                    "compare_price": 475.0,
                    "duration": "Instant",
                    "sort_order": 2,
                },
            ],
        },
    ]

    for p_info in products_data:
        prod = db.query(Product).filter(Product.slug == p_info["slug"]).first()
        if not prod:
            fields = p_info.pop("fields")
            packages = p_info.pop("packages")
            prod = Product(**p_info)
            db.add(prod)
            db.commit()
            db.refresh(prod)
            print(f"  [CREATED] Product '{prod.name}'")

            for f_data in fields:
                f_data["product_id"] = prod.id
                field = ProductInputField(**f_data)
                db.add(field)

            for pkg_data in packages:
                pkg_data["product_id"] = prod.id
                pkg = Package(**pkg_data)
                db.add(pkg)

            db.commit()


def seed_payment_methods_and_coupons(db) -> None:
    methods = [
        {
            "name": "bKash Personal",
            "account_number": "01812345678",
            "instructions": "Use Send Money option from bKash app.",
            "sort_order": 1,
        },
        {
            "name": "Nagad Personal",
            "account_number": "01712345678",
            "instructions": "Send Money to Nagad personal number.",
            "sort_order": 2,
        },
        {
            "name": "Rocket Personal",
            "account_number": "01912345678",
            "instructions": "Send Money via Rocket wallet.",
            "sort_order": 3,
        },
    ]

    for m_data in methods:
        existing = (
            db.query(PaymentMethod).filter(PaymentMethod.name == m_data["name"]).first()
        )
        if not existing:
            method = PaymentMethod(**m_data)
            db.add(method)
            db.commit()
            print(f"  [CREATED] Payment Method '{method.name}'")

    coupons = [
        {
            "code": "WELCOME50",
            "type": "FIXED",
            "value": 50.0,
            "minimum_order_amount": 300.0,
            "usage_limit": 100,
            "per_user_limit": 1,
        },
        {
            "code": "EID10",
            "type": "PERCENTAGE",
            "value": 10.0,
            "max_discount": 200.0,
            "minimum_order_amount": 400.0,
            "usage_limit": 500,
            "per_user_limit": 2,
        },
    ]

    for c_data in coupons:
        existing = db.query(Coupon).filter(Coupon.code == c_data["code"]).first()
        if not existing:
            coupon = Coupon(**c_data)
            db.add(coupon)
            db.commit()
            print(f"  [CREATED] Coupon '{coupon.code}'")


def seed_marketing_and_lottery(db) -> None:
    # Site settings
    setting = db.query(SiteSetting).first()
    if not setting:
        setting = SiteSetting(
            site_name="BoostGhor Digital",
            site_title="Fast & Secure Digital Subscriptions",
            support_phone="+8801812345678",
            telegram_url="https://t.me/boostghordigital",
        )
        db.add(setting)
        db.commit()
        print("  [CREATED] Site Settings")

    # Banner
    banner = db.query(Banner).first()
    if not banner:
        banner = Banner(
            title="Big Savings on OTT Subscriptions",
            description="Get Netflix, Spotify and Canva Pro at discounted rates!",
            image="https://images.unsplash.com/photo-1522869635100-9f4c5e86aa37",
            button_text="Browse Deals",
            button_url="/products",
            sort_order=1,
        )
        db.add(banner)
        db.commit()
        print("  [CREATED] Promotional Banner")

    # Lottery Campaign
    lottery = db.query(Lottery).first()
    if not lottery:
        lottery = Lottery(
            name="Friday Lucky Spin",
            description="Spin to win exclusive discounts on streaming subscriptions!",
            starts_at=datetime.now(timezone.utc) - timedelta(days=1),
            ends_at=datetime.now(timezone.utc) + timedelta(days=30),
            is_active=True,
        )
        db.add(lottery)
        db.commit()
        db.refresh(lottery)

        prizes = [
            {
                "lottery_id": lottery.id,
                "discount_type": "PERCENTAGE",
                "discount_value": 50.0,
                "probability": 0.20,
                "quantity": 10,
            },
            {
                "lottery_id": lottery.id,
                "discount_type": "PERCENTAGE",
                "discount_value": 20.0,
                "probability": 0.50,
                "quantity": 50,
            },
        ]
        for p_data in prizes:
            db.add(LotteryPrize(**p_data))
        db.commit()
        print("  [CREATED] Active Lottery Campaign with Prizes")


def seed_database() -> None:
    print("\n Starting database seeding...")
    db = SessionLocal()
    try:
        print("\n--- Seeding Users & Wallets ---")
        seed_users_and_wallets(db)

        print("\n--- Seeding Digital Products & Packages ---")
        seed_catalog(db)

        print("\n--- Seeding Payment Methods & Coupons ---")
        seed_payment_methods_and_coupons(db)

        print("\n--- Seeding Marketing, Settings & Lottery ---")
        seed_marketing_and_lottery(db)

        print("\n Database seeding finished successfully!\n")
    except Exception as e:
        db.rollback()
        print(f"\n❌ Error during seeding: {e}")
        sys.exit(1)
    finally:
        db.close()


if __name__ == "__main__":
    seed_database()
