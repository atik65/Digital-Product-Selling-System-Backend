import sys
from pathlib import Path

# Fix Windows console encoding for Unicode/Emojis
if sys.platform == "win32" and hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

# Add project root directory to Python path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.core.database import SessionLocal
from app.core.security import hash_password
from app.models.user import User
from app.models.product import Product


def seed_users(db) -> None:
    """Seeds default Super Admin and Regular User accounts."""
    users_data = [
        {
            "email": "admin@example.com",
            "username": "admin",
            "plain_password": "admin123",
            "role": "admin",
            "is_active": True,
        },
        {
            "email": "user@example.com",
            "username": "user",
            "plain_password": "user123",
            "role": "user",
            "is_active": True,
        },
    ]

    for user_info in users_data:
        existing_user = db.query(User).filter(User.email == user_info["email"]).first()
        if existing_user:
            print(f"  [SKIP] User '{user_info['email']}' already exists.")
            continue

        user = User(
            email=user_info["email"],
            username=user_info["username"],
            hashed_password=hash_password(user_info["plain_password"]),
            role=user_info["role"],
            is_active=user_info["is_active"],
        )
        db.add(user)
        db.commit()
        print(
            f"  [CREATED] User '{user_info['username']}' ({user_info['email']}) with role '{user_info['role']}'"
        )


def seed_products(db) -> None:
    """Seeds initial mock products for testing filtering, search, and pagination."""
    sample_products = [
        {
            "name": "Mechanical Gaming Keyboard",
            "description": "RGB tactile mechanical switches with detachable USB-C cable.",
            "price": 89.99,
            "stock_quantity": 35,
            "image_url": "https://images.unsplash.com/photo-1587829741301-dc798b83add3",
        },
        {
            "name": "Wireless Ergonomic Mouse",
            "description": "Ergonomic vertical wireless mouse with adjustable DPI.",
            "price": 49.50,
            "stock_quantity": 50,
            "image_url": "https://images.unsplash.com/photo-1615663245857-ac93bb7c39e7",
        },
        {
            "name": "UltraWide 34-inch Curved Monitor",
            "description": "144Hz WQHD 3440x1440p HDR curved gaming and productivity monitor.",
            "price": 499.00,
            "stock_quantity": 12,
            "image_url": "https://images.unsplash.com/photo-1527443224154-c4a3942d3acf",
        },
        {
            "name": "Noise Cancelling Wireless Headphones",
            "description": "Active noise cancelling with 40-hour battery life and fast charging.",
            "price": 179.99,
            "stock_quantity": 20,
            "image_url": "https://images.unsplash.com/photo-1505740420928-5e560c06d30e",
        },
        {
            "name": "Aluminum Laptop Stand",
            "description": "Ergonomic foldable aluminum riser for laptops and tablets up to 17 inches.",
            "price": 29.99,
            "stock_quantity": 45,
            "image_url": "https://images.unsplash.com/photo-1544816155-12df9643f363",
        },
        {
            "name": "USB-C Multiport Docking Station",
            "description": "10-in-1 hub with 4K HDMI, Gigabit Ethernet, SD card reader, and 100W PD.",
            "price": 59.99,
            "stock_quantity": 60,
            "image_url": "https://images.unsplash.com/photo-1541807084-5c52b6b3adef",
        },
        {
            "name": "Smart LED Desk Lamp",
            "description": "Dimmable eye-caring desk lamp with wireless charging base and timer.",
            "price": 39.95,
            "stock_quantity": 25,
            "image_url": "https://images.unsplash.com/photo-1534972195531-a756b1146241",
        },
        {
            "name": "Waterproof Commuter Backpack",
            "description": "Minimalist anti-theft laptop backpack with padded compartment.",
            "price": 65.00,
            "stock_quantity": 18,
            "image_url": "https://images.unsplash.com/photo-1553062407-98eeb64c6a62",
        },
    ]

    created_count = 0
    for prod_data in sample_products:
        existing = db.query(Product).filter(Product.name == prod_data["name"]).first()
        if existing:
            continue

        product = Product(**prod_data)
        db.add(product)
        created_count += 1

    db.commit()
    if created_count > 0:
        print(f"  [CREATED] Added {created_count} sample products.")
    else:
        print("  [SKIP] All sample products already exist.")


def seed_database() -> None:
    """Entrypoint function for seeding all database entities."""
    print("\n Starting database seeding...")
    db = SessionLocal()
    try:
        print("\n--- Seeding Users ---")
        seed_users(db)

        print("\n--- Seeding Products ---")
        seed_products(db)

        print("\n Database seeding finished successfully!\n")
    except Exception as e:
        db.rollback()
        print(f"\n❌ Error during seeding: {e}")
        sys.exit(1)
    finally:
        db.close()


if __name__ == "__main__":
    seed_database()
