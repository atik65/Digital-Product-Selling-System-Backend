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
            "name": "ফেসবুক সার্ভিস",
            "slug": "facebook-services",
            "image": "https://admin.boostghor.com/products/1741968472.jpg",
            "description": "ফেসবুক পেজ ফলোয়ার, লাইক, রিঅ্যাক্ট এবং ভিডিও ভিউজ সার্ভিস",
            "sort_order": 1,
        },
        {
            "name": "বিনোদনমূলক সাবস্ক্রিপশন",
            "slug": "entertainment-subscriptions",
            "image": "https://admin.boostghor.com/products/1771728617.jpg",
            "description": "জনপ্রিয় ওটিটি এবং স্ট্রিমিং প্ল্যাটফর্ম সাবস্ক্রিপশন",
            "sort_order": 2,
        },
        {
            "name": "AI সাবস্ক্রিপশনস",
            "slug": "ai-subscriptions",
            "image": "https://admin.boostghor.com/products/1776170920.jpg",
            "description": "জনপ্রিয় কৃত্রিম বুদ্ধিমত্তা ও প্রোডাক্টিভিটি এআই টুলস",
            "sort_order": 3,
        },
        {
            "name": "অন্যান্য সাবস্ক্রিপশনস",
            "slug": "other-subscriptions",
            "image": "https://admin.boostghor.com/products/1776245447.jpg",
            "description": "ডিজাইন, লার্নিং, এডিটিং ও ইউটিলিটি প্ল্যাটফর্ম সাবস্ক্রিপশন",
            "sort_order": 4,
        },
        {
            "name": "অন্যান্য সার্ভিস",
            "slug": "other-services",
            "image": "https://admin.boostghor.com/products/1771727650.jpg",
            "description": "প্রিমিয়াম ভিপিএন এবং সিকিউরিটি সার্ভিসেস",
            "sort_order": 5,
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
        else:
            cat.name = c_data["name"]
            cat.image = c_data["image"]
            cat.description = c_data["description"]
            cat.sort_order = c_data["sort_order"]
            db.commit()
            db.refresh(cat)
        cat_map[cat.slug] = cat.id

    desc_fb_follower = """⦿ অর্ডার করার সময় অবশ্যই সঠিক লিংক দিবেন
⦿ অর্ডার কমপ্লিট হতে ১ ঘন্টা থেকে ৬ ঘন্টা+ সময় বা কিছু ক্ষেত্রে ২-৩ দিন সময় লাগতে পারে, তাই অর্ডার করার পর অধৈর্য না হয়ে অপেক্ষা করবেন
⦿ যদি ৩দিনের ভিতরে অর্ডার Complete না হয় তাহলে টেলিগ্রাম সাপোর্ট এ মেসেজ দিবেন সমস্যা সমাধান করে দেওয়া হবে
⦿ পেজ থেকে কিছু লাইক/ফলোয়ার কমে যেতে পারে, তবে না কমার সম্ভাবনাই বেশি"""

    desc_fb_react = """⦿ আপনার ফেসবুক আইডি অবশ্যই Public রাখবেন (আইডি Locked করা থাকলে অর্ডার ক্যানসেল হবে)
⦿ অর্ডার করার সময় অবশ্যই সঠিক লিংক দিবেন
⦿ অর্ডার কমপ্লিট হতে ১ ঘন্টা থেকে ৬ ঘন্টা+ সময় বা কিছু ক্ষেত্রে ২-৩ দিন সময় লাগতে পারে, তাই অর্ডার করার পর অধৈর্য না হয়ে অপেক্ষা করবেন
⦿ যদি ৩দিনের ভিতরে অর্ডার Complete না হয় তাহলে টেলিগ্রাম সাপোর্ট এ মেসেজ দিবেন সমস্যা সমাধান করে দেওয়া হবে
⦿ আইডি থেকে কিছু লাইক কমে যেতে পারে, তবে না কমার সম্ভাবনাই বেশি"""

    desc_fb_views = """⦿ আপনার ফেসবুক আইডি অবশ্যই Public রাখবেন (আইডি Locked করা থাকলে অর্ডার ক্যানসেল হবে)
⦿ অর্ডার করার সময় অবশ্যই সঠিক লিংক দিবেন
⦿ অর্ডার কমপ্লিট হতে ১ ঘন্টা থেকে ৬ ঘন্টা+ সময় বা কিছু ক্ষেত্রে ২-৩ দিন সময় লাগতে পারে, তাই অর্ডার করার পর অধৈর্য না হয়ে অপেক্ষা করবেন
⦿ যদি ৩দিনের ভিতরে অর্ডার Complete না হয় তাহলে টেলিগ্রাম সাপোর্ট এ মেসেজ দিবেন সমস্যা সমাধান করে দেওয়া হবে
⦿ আইডি থেকে কিছু Views কমে যেতে পারে, তবে না কমার সম্ভাবনাই বেশি"""

    desc_entertainment = """⦿ অর্ডার করার সময় অবশ্যই সঠিক Gmail Address প্রদান করুন। ভুল Gmail দিলে প্রোডাক্ট ডেলিভারি সম্ভব হবে না।
⦿ অর্ডার কমপ্লিট হতে ১ ঘন্টা থেকে ৬ ঘন্টা+ সময় লাগতে পারে, তাই অর্ডার করার পর অধৈর্য না হয়ে অপেক্ষা করবেন
⦿ অর্ডার স্ট্যাটাস "Complete" দেখানোর পর আপনার Gmail-এর Inbox অথবা Spam ফোল্ডার চেক করুন। সকল Account Details (ID & Password) Gmail-এ পাঠানো হয়।
⦿ ২৪ ঘণ্টার মধ্যে অর্ডার Complete না হলে Support-এ যোগাযোগ করুন। Telegram Support-এ মেসেজ দিলে দ্রুত সমাধান করা হবে"""

    desc_ai_default = """⦿ অর্ডার করার সময় সঠিক Gmail ব্যবহার করবেন, যে Gmail টি দিবেন সেখানে আপনার প্রিমিয়াম সাবস্ক্রিপশন চালু করার জন্য মেইল দেয়া হবে
⦿ অর্ডার কমপ্লিট হতে ১-২+ ঘন্টা সময় লাগতে পারে
⦿ যদি ২৪ ঘন্টার ভিতরে অর্ডার Complete না হয় তাহলে টেলিগ্রাম সাপোর্ট এ মেসেজ দিবেন সমস্যা সমাধান করে দেওয়া হবে
STAY CONNECTED"""

    desc_claude = """⦿ অর্ডার করার সময় সঠিক Gmail ব্যবহার করবেন, যে Gmail টি দিবেন সেখানে আপনার প্রিমিয়াম সাবস্ক্রিপশন চালু করার জন্য মেইল দেয়া হবে
⦿ Claude Pro সাবস্ক্রিপশন এর মাধ্যমে Claude 3.5 Sonnet এবং Opus এর আনলিমিটেড সুবিধা ব্যবহার করুন"""

    desc_duolingo = """⦿ অর্ডার করার সময় অবশ্যই সঠিক Gmail Address প্রদান করুন।
⦿ ডুওলিঙ্গো সুপার / ফ্যামিলি প্ল্যান ইনভাইট আপনার জিমেইলে পাঠানো হবে। বিজ্ঞাপন মুক্ত ভাষা শিক্ষার অভিজ্ঞতা উপভোগ করুন।"""

    desc_telegram = """⦿ অর্ডার করার সময় অবশ্যই সঠিক টেলিগ্রাম User Name প্রদান করুন।
⦿ টেলিগ্রাম প্রিমিয়াম গিফট লিংকের মাধ্যমে বা সরাসরি আপনার অ্যাকাউন্টে সক্রিয় করা হবে।"""

    desc_prism = """⦿ অর্ডার করার সময় অবশ্যই সঠিক Gmail Address প্রদান করুন।
⦿ প্রিযম লাইভ স্টুডিও প্রিমিয়াম এক্সেস উপভোগ করুন কোনো ওয়াটারমার্ক ছাড়া হাই-কোয়ালিটি লাইভ স্ট্রিমিং ও রেকর্ডিং সুবিধা সহ।"""

    desc_picsart = """⦿ অর্ডার করার সময় অবশ্যই সঠিক Gmail Address প্রদান করুন।
⦿ পিক্সআর্ট গোল্ড প্রিমিয়াম এক্সেস এর মাধ্যমে সব প্রিমিয়াম ফিল্টার, ফন্ট ও এআই এডিটিং টুলস আনলক করুন।"""

    desc_lightroom = """⦿ অর্ডার করার সময় অবশ্যই সঠিক Gmail Address প্রদান করুন।
⦿ অ্যাডোবি লাইটরুম প্রিমিয়াম একাউন্ট দিয়ে প্রফেশনাল কালার গ্রেডিং, মাস্কিং ও প্রিসেট ব্যবহার করুন।"""

    desc_vpn_nord = """⦿ অর্ডার করার সময় অবশ্যই সঠিক Gmail Address প্রদান করুন। ভুল Gmail দিলে প্রোডাক্ট ডেলিভারি সম্ভব হবে না।
⦿ অর্ডার কমপ্লিট হতে ১ ঘন্টা থেকে ৬ ঘন্টা+ সময় বা কিছু ক্ষেত্রে ২-৩ দিন সময় লাগতে পারে, তাই অর্ডার করার পর অধৈর্য না হয়ে অপেক্ষা করবেন
⦿ অর্ডার স্ট্যাটাস "Complete" দেখানোর পর আপনার Gmail-এর Inbox অথবা Spam ফোল্ডার চেক করুন। সকল Account Details (ID & Password) Gmail-এ পাঠানো হয়।
⦿ ২৪ ঘণ্টার মধ্যে অর্ডার Complete না হলে Support-এ যোগাযোগ করুন। Telegram Support-এ মেসেজ দিলে দ্রুত সমাধান করা হবে।"""

    desc_vpn_express = """⦿ অর্ডার করার সময় অবশ্যই সঠিক Gmail Address প্রদান করুন।
⦿ এক্সপ্রেস ভিপিএন এর অ্যাক্টিভেশন কোড বা প্রিমিয়াম লগইন অ্যাকাউন্ট আপনার জিমেইলে দেওয়া হবে। দ্রুততম ও সুরক্ষিত ব্রাউজিং উপভোগ করুন।"""

    products_data = [
        # =====================================================================
        # 1. ফেসবুক সার্ভিস
        # =====================================================================
        {
            "category_id": cat_map["facebook-services"],
            "name": "PAGE FOLLOWER",
            "slug": "page-follower",
            "image": "https://admin.boostghor.com/products/1776244581.jpg",
            "description": desc_fb_follower,
            "instructions": "অর্ডার করার সময় অবশ্যই সঠিক পেইজ লিংক দিবেন। পেইজ পাবলিক থাকতে হবে।",
            "sort_order": 1,
            "fields": [
                {
                    "name": "page_link",
                    "label": "এখানে পেইজ লিংক বসান",
                    "type": "url",
                    "placeholder": "https://facebook.com/yourpage",
                    "is_required": True,
                    "sort_order": 1,
                }
            ],
            "packages": [
                {
                    "name": "1,000 Page Followers",
                    "price": 120.0,
                    "compare_price": 150.0,
                    "duration": "1-6 Hours",
                    "sort_order": 1,
                },
                {
                    "name": "5,000 Page Followers",
                    "price": 550.0,
                    "compare_price": 700.0,
                    "duration": "1-2 Days",
                    "sort_order": 2,
                },
                {
                    "name": "10,000 Page Followers",
                    "price": 1050.0,
                    "compare_price": 1350.0,
                    "duration": "2-3 Days",
                    "sort_order": 3,
                },
            ],
        },
        {
            "category_id": cat_map["facebook-services"],
            "name": "FACEBOOK REACT",
            "slug": "facebook-react",
            "image": "https://admin.boostghor.com/products/1776244664.jpg",
            "description": desc_fb_react,
            "instructions": "পোস্ট পাবলিক রাখবেন এবং সঠিক পোস্টের লিংক বসাবেন।",
            "sort_order": 2,
            "fields": [
                {
                    "name": "post_link",
                    "label": "এখানে পোস্টের লিংক বসান",
                    "type": "url",
                    "placeholder": "https://facebook.com/.../posts/...",
                    "is_required": True,
                    "sort_order": 1,
                }
            ],
            "packages": [
                {
                    "name": "500 Mix Reacts",
                    "price": 45.0,
                    "compare_price": 60.0,
                    "duration": "1-3 Hours",
                    "sort_order": 1,
                },
                {
                    "name": "1,000 Love/Care Reacts",
                    "price": 85.0,
                    "compare_price": 110.0,
                    "duration": "1-6 Hours",
                    "sort_order": 2,
                },
                {
                    "name": "2,500 Custom Reacts",
                    "price": 200.0,
                    "compare_price": 250.0,
                    "duration": "1-12 Hours",
                    "sort_order": 3,
                },
            ],
        },
        {
            "category_id": cat_map["facebook-services"],
            "name": "VIDEO VIEWS",
            "slug": "video-views",
            "image": "https://admin.boostghor.com/products/1776244611.jpg",
            "description": desc_fb_views,
            "instructions": "ভিডিও পাবলিক থাকতে হবে। সঠিক ভিডিও লিংক প্রদান করুন।",
            "sort_order": 3,
            "fields": [
                {
                    "name": "video_link",
                    "label": "এখানে ভিডিও লিংক বসান",
                    "type": "url",
                    "placeholder": "https://facebook.com/watch/?v=...",
                    "is_required": True,
                    "sort_order": 1,
                }
            ],
            "packages": [
                {
                    "name": "1,000 Video Views",
                    "price": 30.0,
                    "compare_price": 45.0,
                    "duration": "1-3 Hours",
                    "sort_order": 1,
                },
                {
                    "name": "5,000 Video Views",
                    "price": 130.0,
                    "compare_price": 180.0,
                    "duration": "1-6 Hours",
                    "sort_order": 2,
                },
                {
                    "name": "10,000 Video Views",
                    "price": 240.0,
                    "compare_price": 320.0,
                    "duration": "1-12 Hours",
                    "sort_order": 3,
                },
            ],
        },

        # =====================================================================
        # 2. বিনোদনমূলক সাবস্ক্রিপশন
        # =====================================================================
        {
            "category_id": cat_map["entertainment-subscriptions"],
            "name": "NETFLIX",
            "slug": "netflix",
            "image": "https://admin.boostghor.com/products/1776243949.jpg",
            "description": desc_entertainment,
            "instructions": "অর্ডার স্ট্যাটাস Complete হলে আপনার Gmail এর Inbox বা Spam ফোল্ডার চেক করুন।",
            "sort_order": 1,
            "fields": [
                {
                    "name": "gmail",
                    "label": "এখানে আপনার জিমেইল বসান",
                    "type": "email",
                    "placeholder": "yourname@gmail.com",
                    "is_required": True,
                    "sort_order": 1,
                }
            ],
            "packages": [
                {
                    "name": "1 Month - 1 Screen (Shared)",
                    "price": 280.0,
                    "compare_price": 350.0,
                    "duration": "1 Month",
                    "sort_order": 1,
                },
                {
                    "name": "1 Month - Private Profile (PIN Protected)",
                    "price": 350.0,
                    "compare_price": 420.0,
                    "duration": "1 Month",
                    "sort_order": 2,
                },
                {
                    "name": "1 Month - Full Account (5 Profiles, 4K UHD)",
                    "price": 1250.0,
                    "compare_price": 1500.0,
                    "duration": "1 Month",
                    "sort_order": 3,
                },
            ],
        },
        {
            "category_id": cat_map["entertainment-subscriptions"],
            "name": "CRUNCHYROLL",
            "slug": "crunchyroll",
            "image": "https://admin.boostghor.com/products/1776243960.jpg",
            "description": desc_entertainment,
            "instructions": "সঠিক Gmail Address দিন। সকল লগইন তথ্য জিমেইলে প্রদান করা হবে।",
            "sort_order": 2,
            "fields": [
                {
                    "name": "gmail",
                    "label": "এখানে আপনার জিমেইল বসান",
                    "type": "email",
                    "placeholder": "yourname@gmail.com",
                    "is_required": True,
                    "sort_order": 1,
                }
            ],
            "packages": [
                {
                    "name": "1 Month Mega Fan (1 Screen)",
                    "price": 130.0,
                    "compare_price": 180.0,
                    "duration": "1 Month",
                    "sort_order": 1,
                },
                {
                    "name": "1 Month Mega Fan (Private Account)",
                    "price": 350.0,
                    "compare_price": 450.0,
                    "duration": "1 Month",
                    "sort_order": 2,
                },
            ],
        },
        {
            "category_id": cat_map["entertainment-subscriptions"],
            "name": "SPOTIFY",
            "slug": "spotify",
            "image": "https://admin.boostghor.com/products/1776243969.jpg",
            "description": desc_entertainment,
            "instructions": "সঠিক Gmail দিন। আপনার Spotify অ্যাকাউন্ট আপডেট বা ইনভাইট লিংক মেইলে পাঠানো হবে।",
            "sort_order": 3,
            "fields": [
                {
                    "name": "gmail",
                    "label": "এখানে আপনার জিমেইল বসান",
                    "type": "email",
                    "placeholder": "yourname@gmail.com",
                    "is_required": True,
                    "sort_order": 1,
                }
            ],
            "packages": [
                {
                    "name": "1 Month Premium (Personal)",
                    "price": 150.0,
                    "compare_price": 200.0,
                    "duration": "1 Month",
                    "sort_order": 1,
                },
                {
                    "name": "3 Months Premium",
                    "price": 420.0,
                    "compare_price": 550.0,
                    "duration": "3 Months",
                    "sort_order": 2,
                },
                {
                    "name": "6 Months Premium",
                    "price": 780.0,
                    "compare_price": 1000.0,
                    "duration": "6 Months",
                    "sort_order": 3,
                },
            ],
        },
        {
            "category_id": cat_map["entertainment-subscriptions"],
            "name": "PRIME VIDEO",
            "slug": "prime-video",
            "image": "https://admin.boostghor.com/products/1776244358.jpg",
            "description": desc_entertainment,
            "instructions": "সঠিক Gmail Address দিন। আমাজন প্রাইম ভিডিও অ্যাকাউন্ট তথ্য জিমেইলে প্রদান করা হবে।",
            "sort_order": 4,
            "fields": [
                {
                    "name": "gmail",
                    "label": "এখানে জিমেইল বসান",
                    "type": "email",
                    "placeholder": "yourname@gmail.com",
                    "is_required": True,
                    "sort_order": 1,
                }
            ],
            "packages": [
                {
                    "name": "1 Month - 1 Screen",
                    "price": 140.0,
                    "compare_price": 180.0,
                    "duration": "1 Month",
                    "sort_order": 1,
                },
                {
                    "name": "6 Months - 1 Screen",
                    "price": 650.0,
                    "compare_price": 850.0,
                    "duration": "6 Months",
                    "sort_order": 2,
                },
            ],
        },
        {
            "category_id": cat_map["entertainment-subscriptions"],
            "name": "CHORKI",
            "slug": "chorki",
            "image": "https://admin.boostghor.com/products/1776244060.jpg",
            "description": desc_entertainment,
            "instructions": "সঠিক Gmail Address দিন। চরকি প্রিমিয়াম সাবস্ক্রিপশন ডিটেইলস জিমেইলে পাঠানো হবে।",
            "sort_order": 5,
            "fields": [
                {
                    "name": "gmail",
                    "label": "এখানে জিমেইল বসান",
                    "type": "email",
                    "placeholder": "yourname@gmail.com",
                    "is_required": True,
                    "sort_order": 1,
                }
            ],
            "packages": [
                {
                    "name": "1 Month Subscription",
                    "price": 80.0,
                    "compare_price": 100.0,
                    "duration": "1 Month",
                    "sort_order": 1,
                },
                {
                    "name": "6 Months Subscription",
                    "price": 380.0,
                    "compare_price": 480.0,
                    "duration": "6 Months",
                    "sort_order": 2,
                },
                {
                    "name": "1 Year Subscription",
                    "price": 650.0,
                    "compare_price": 799.0,
                    "duration": "1 Year",
                    "sort_order": 3,
                },
            ],
        },
        {
            "category_id": cat_map["entertainment-subscriptions"],
            "name": "TOFEE",
            "slug": "tofee",
            "image": "https://admin.boostghor.com/products/1779884932.jpg",
            "description": desc_entertainment,
            "instructions": "সঠিক Gmail Address প্রদান করুন। টফি সাবস্ক্রিপশন মেইলে প্রদান করা হবে।",
            "sort_order": 6,
            "fields": [
                {
                    "name": "gmail",
                    "label": "এখানে জিমেইল বসান",
                    "type": "email",
                    "placeholder": "yourname@gmail.com",
                    "is_required": True,
                    "sort_order": 1,
                }
            ],
            "packages": [
                {
                    "name": "1 Month Premium",
                    "price": 70.0,
                    "compare_price": 90.0,
                    "duration": "1 Month",
                    "sort_order": 1,
                },
                {
                    "name": "3 Months Premium",
                    "price": 190.0,
                    "compare_price": 250.0,
                    "duration": "3 Months",
                    "sort_order": 2,
                },
            ],
        },
        {
            "category_id": cat_map["entertainment-subscriptions"],
            "name": "HBO MAX",
            "slug": "hbo-max",
            "image": "https://admin.boostghor.com/products/1776244105.jpg",
            "description": desc_entertainment,
            "instructions": "সঠিক জিমেইল আইডি দিন। এইচবিও ম্যাক্স এর অ্যাকাউন্ট তথ্য জিমেইলে প্রদান করা হবে।",
            "sort_order": 7,
            "fields": [
                {
                    "name": "gmail",
                    "label": "এখানে জিমেইল আইডি বসান",
                    "type": "email",
                    "placeholder": "yourname@gmail.com",
                    "is_required": True,
                    "sort_order": 1,
                }
            ],
            "packages": [
                {
                    "name": "1 Month - 1 Screen",
                    "price": 180.0,
                    "compare_price": 240.0,
                    "duration": "1 Month",
                    "sort_order": 1,
                },
                {
                    "name": "3 Months - 1 Screen",
                    "price": 490.0,
                    "compare_price": 650.0,
                    "duration": "3 Months",
                    "sort_order": 2,
                },
            ],
        },
        {
            "category_id": cat_map["entertainment-subscriptions"],
            "name": "DISNEY",
            "slug": "disney",
            "image": "https://admin.boostghor.com/products/1777224597.jpg",
            "description": desc_entertainment,
            "instructions": "সঠিক জিমেইল আইডি প্রদান করুন। ডিজনি প্লাস অ্যাকাউন্ট ডিটেইলস জিমেইলে পাঠানো হবে।",
            "sort_order": 8,
            "fields": [
                {
                    "name": "gmail",
                    "label": "এখানে জিমেইল আইডি বসান",
                    "type": "email",
                    "placeholder": "yourname@gmail.com",
                    "is_required": True,
                    "sort_order": 1,
                }
            ],
            "packages": [
                {
                    "name": "1 Month - 1 Screen",
                    "price": 160.0,
                    "compare_price": 220.0,
                    "duration": "1 Month",
                    "sort_order": 1,
                },
                {
                    "name": "3 Months - 1 Screen",
                    "price": 450.0,
                    "compare_price": 600.0,
                    "duration": "3 Months",
                    "sort_order": 2,
                },
            ],
        },

        # =====================================================================
        # 3. AI সাবস্ক্রিপশনস
        # =====================================================================
        {
            "category_id": cat_map["ai-subscriptions"],
            "name": "CHATGPT",
            "slug": "chatgpt",
            "image": "https://admin.boostghor.com/products/1776243999.jpg",
            "description": desc_ai_default,
            "instructions": "সঠিক Gmail ব্যবহার করবেন। সাবস্ক্রিপশন ইনভাইট বা অ্যাকাউন্ট মেইলে পাঠানো হবে।",
            "sort_order": 1,
            "fields": [
                {
                    "name": "gmail",
                    "label": "এখানে জিমেইল বসান",
                    "type": "email",
                    "placeholder": "yourname@gmail.com",
                    "is_required": True,
                    "sort_order": 1,
                }
            ],
            "packages": [
                {
                    "name": "ChatGPT Plus (Shared)",
                    "price": 450.0,
                    "compare_price": 600.0,
                    "duration": "1 Month",
                    "sort_order": 1,
                },
                {
                    "name": "ChatGPT Plus (Private Mail Invite)",
                    "price": 2300.0,
                    "compare_price": 2600.0,
                    "duration": "1 Month",
                    "sort_order": 2,
                },
            ],
        },
        {
            "category_id": cat_map["ai-subscriptions"],
            "name": "CLAUDE AI",
            "slug": "claude-ai",
            "image": "https://admin.boostghor.com/products/1779882979.png",
            "description": desc_claude,
            "instructions": "সঠিক Gmail ব্যবহার করবেন। ডেলিভারি ডিটেইলস মেইলে পাঠানো হবে।",
            "sort_order": 2,
            "fields": [
                {
                    "name": "gmail",
                    "label": "এখানে জিমেইল বসান",
                    "type": "email",
                    "placeholder": "yourname@gmail.com",
                    "is_required": True,
                    "sort_order": 1,
                }
            ],
            "packages": [
                {
                    "name": "Claude Pro (Shared)",
                    "price": 500.0,
                    "compare_price": 650.0,
                    "duration": "1 Month",
                    "sort_order": 1,
                },
                {
                    "name": "Claude Pro (Private)",
                    "price": 2400.0,
                    "compare_price": 2700.0,
                    "duration": "1 Month",
                    "sort_order": 2,
                },
            ],
        },
        {
            "category_id": cat_map["ai-subscriptions"],
            "name": "GEMINI",
            "slug": "gemini",
            "image": "https://admin.boostghor.com/products/1776244326.jpg",
            "description": desc_ai_default,
            "instructions": "সঠিক Gmail ব্যবহার করবেন। Google One Gemini Advanced সাবস্ক্রিপশন চালু করা হবে।",
            "sort_order": 3,
            "fields": [
                {
                    "name": "gmail",
                    "label": "এখানে জিমেইল বসান",
                    "type": "email",
                    "placeholder": "yourname@gmail.com",
                    "is_required": True,
                    "sort_order": 1,
                }
            ],
            "packages": [
                {
                    "name": "Gemini Advanced 1 Month",
                    "price": 350.0,
                    "compare_price": 500.0,
                    "duration": "1 Month",
                    "sort_order": 1,
                },
                {
                    "name": "Gemini Advanced 3 Months",
                    "price": 950.0,
                    "compare_price": 1300.0,
                    "duration": "3 Months",
                    "sort_order": 2,
                },
            ],
        },
        {
            "category_id": cat_map["ai-subscriptions"],
            "name": "QUILLBOT",
            "slug": "quillbot",
            "image": "https://admin.boostghor.com/products/1776244043.jpg",
            "description": desc_ai_default,
            "instructions": "সঠিক Gmail ব্যবহার করবেন। প্যারাফ্রেসিং ও গ্রামার চেকার প্রিমিয়াম এক্সেস প্রদান করা হবে।",
            "sort_order": 4,
            "fields": [
                {
                    "name": "gmail",
                    "label": "এখানে জিমেইল বসান",
                    "type": "email",
                    "placeholder": "yourname@gmail.com",
                    "is_required": True,
                    "sort_order": 1,
                }
            ],
            "packages": [
                {
                    "name": "1 Month Premium (Shared)",
                    "price": 150.0,
                    "compare_price": 220.0,
                    "duration": "1 Month",
                    "sort_order": 1,
                },
                {
                    "name": "6 Months Premium (Shared)",
                    "price": 650.0,
                    "compare_price": 900.0,
                    "duration": "6 Months",
                    "sort_order": 2,
                },
                {
                    "name": "1 Year Premium (Shared)",
                    "price": 1100.0,
                    "compare_price": 1500.0,
                    "duration": "1 Year",
                    "sort_order": 3,
                },
            ],
        },
        {
            "category_id": cat_map["ai-subscriptions"],
            "name": "GROK AI",
            "slug": "grok-ai",
            "image": "https://admin.boostghor.com/products/1776244049.jpg",
            "description": desc_ai_default,
            "instructions": "সঠিক Gmail ব্যবহার করবেন। X (Twitter) Premium ও Grok AI এক্সেস প্রদান করা হবে।",
            "sort_order": 5,
            "fields": [
                {
                    "name": "gmail",
                    "label": "এখানে জিমেইল বসান",
                    "type": "email",
                    "placeholder": "yourname@gmail.com",
                    "is_required": True,
                    "sort_order": 1,
                }
            ],
            "packages": [
                {
                    "name": "X Premium (Grok AI) 1 Month",
                    "price": 950.0,
                    "compare_price": 1200.0,
                    "duration": "1 Month",
                    "sort_order": 1,
                },
                {
                    "name": "X Premium+ (Grok Full Access) 1 Month",
                    "price": 1850.0,
                    "compare_price": 2200.0,
                    "duration": "1 Month",
                    "sort_order": 2,
                },
            ],
        },

        # =====================================================================
        # 4. অন্যান্য সাবস্ক্রিপশনস
        # =====================================================================
        {
            "category_id": cat_map["other-subscriptions"],
            "name": "CAPCUT",
            "slug": "capcut",
            "image": "https://admin.boostghor.com/products/1776244068.jpg",
            "description": desc_entertainment,
            "instructions": "সঠিক Gmail Address দিন। ক্যাপকাট প্রো অ্যাকাউন্ট/ইনভাইট মেইলে প্রদান করা হবে।",
            "sort_order": 1,
            "fields": [
                {
                    "name": "gmail",
                    "label": "এখানে জিমেইল বসান",
                    "type": "email",
                    "placeholder": "yourname@gmail.com",
                    "is_required": True,
                    "sort_order": 1,
                }
            ],
            "packages": [
                {
                    "name": "1 Month Pro (Shared)",
                    "price": 160.0,
                    "compare_price": 220.0,
                    "duration": "1 Month",
                    "sort_order": 1,
                },
                {
                    "name": "1 Year Pro (Private/Shared)",
                    "price": 1150.0,
                    "compare_price": 1500.0,
                    "duration": "1 Year",
                    "sort_order": 2,
                },
            ],
        },
        {
            "category_id": cat_map["other-subscriptions"],
            "name": "DUOLINGO",
            "slug": "duolingo",
            "image": "https://admin.boostghor.com/products/1779883659.png",
            "description": desc_duolingo,
            "instructions": "সঠিক Gmail দিন। আপনার জিমেইলে সুপার ডুওলিঙ্গো এক্সেস ইনভাইট লিংক পাঠানো হবে।",
            "sort_order": 2,
            "fields": [
                {
                    "name": "gmail",
                    "label": "এখানে আপনার জিমেইল বসান",
                    "type": "email",
                    "placeholder": "yourname@gmail.com",
                    "is_required": True,
                    "sort_order": 1,
                }
            ],
            "packages": [
                {
                    "name": "Super Duolingo (1 Year Plan)",
                    "price": 350.0,
                    "compare_price": 500.0,
                    "duration": "1 Year",
                    "sort_order": 1,
                },
            ],
        },
        {
            "category_id": cat_map["other-subscriptions"],
            "name": "CANVA PRO",
            "slug": "canva-pro",
            "image": "https://admin.boostghor.com/products/1776243988.jpg",
            "description": desc_ai_default,
            "instructions": "সঠিক Gmail ব্যবহার করবেন। আপনার মেইলে ক্যানভা টিম ইনভাইট পাঠানো হবে।",
            "sort_order": 3,
            "fields": [
                {
                    "name": "gmail",
                    "label": "এখানে জিমেইল বসান",
                    "type": "email",
                    "placeholder": "yourname@gmail.com",
                    "is_required": True,
                    "sort_order": 1,
                }
            ],
            "packages": [
                {
                    "name": "1 Month Personal Invite",
                    "price": 80.0,
                    "compare_price": 120.0,
                    "duration": "1 Month",
                    "sort_order": 1,
                },
                {
                    "name": "1 Year Team Invite",
                    "price": 290.0,
                    "compare_price": 450.0,
                    "duration": "1 Year",
                    "sort_order": 2,
                },
                {
                    "name": "Lifetime Edu Invite",
                    "price": 490.0,
                    "compare_price": 750.0,
                    "duration": "Lifetime",
                    "sort_order": 3,
                },
            ],
        },
        {
            "category_id": cat_map["other-subscriptions"],
            "name": "TRUECALLER",
            "slug": "truecaller",
            "image": "https://admin.boostghor.com/products/1776243979.jpg",
            "description": desc_entertainment,
            "instructions": "সঠিক Gmail Address অথবা ফোন নম্বর দিন। প্রিমিয়াম সক্রিয়করণ ডিটেইলস মেইলে দেওয়া হবে।",
            "sort_order": 4,
            "fields": [
                {
                    "name": "gmail_or_phone",
                    "label": "এখানে জিমেইল বসান",
                    "type": "text",
                    "placeholder": "yourname@gmail.com or 017xxxxxxxx",
                    "is_required": True,
                    "sort_order": 1,
                }
            ],
            "packages": [
                {
                    "name": "1 Year Premium Gold/Connect",
                    "price": 220.0,
                    "compare_price": 350.0,
                    "duration": "1 Year",
                    "sort_order": 1,
                },
            ],
        },
        {
            "category_id": cat_map["other-subscriptions"],
            "name": "TELEGRAM",
            "slug": "telegram",
            "image": "https://admin.boostghor.com/products/1776244088.jpg",
            "description": desc_telegram,
            "instructions": "সঠিক টেলিগ্রাম ইউজারনেম (@username) প্রদান করুন। অ্যাকাউন্ট প্রাইভেসি সেটিংস থেকে গিফট রিসিভ অপশন অন রাখবেন।",
            "sort_order": 5,
            "fields": [
                {
                    "name": "telegram_username",
                    "label": "এখানে টেলিগ্রাম User Name বসান",
                    "type": "text",
                    "placeholder": "@username",
                    "is_required": True,
                    "sort_order": 1,
                }
            ],
            "packages": [
                {
                    "name": "Telegram Premium 3 Months",
                    "price": 1150.0,
                    "compare_price": 1350.0,
                    "duration": "3 Months",
                    "sort_order": 1,
                },
                {
                    "name": "Telegram Premium 6 Months",
                    "price": 1950.0,
                    "compare_price": 2300.0,
                    "duration": "6 Months",
                    "sort_order": 2,
                },
                {
                    "name": "Telegram Premium 12 Months",
                    "price": 3450.0,
                    "compare_price": 4000.0,
                    "duration": "12 Months",
                    "sort_order": 3,
                },
            ],
        },
        {
            "category_id": cat_map["other-subscriptions"],
            "name": "PRISM LIVE",
            "slug": "prism-live",
            "image": "https://admin.boostghor.com/products/1779884304.png",
            "description": desc_prism,
            "instructions": "সঠিক Gmail Address দিন। অ্যাকাউন্ট তথ্য মেইলে পাঠানো হবে।",
            "sort_order": 6,
            "fields": [
                {
                    "name": "gmail",
                    "label": "এখানে আপনার জিমেইল বসান",
                    "type": "email",
                    "placeholder": "yourname@gmail.com",
                    "is_required": True,
                    "sort_order": 1,
                }
            ],
            "packages": [
                {
                    "name": "PRISM Live Studio 1 Month",
                    "price": 220.0,
                    "compare_price": 300.0,
                    "duration": "1 Month",
                    "sort_order": 1,
                },
                {
                    "name": "PRISM Live Studio 1 Year",
                    "price": 1450.0,
                    "compare_price": 1900.0,
                    "duration": "1 Year",
                    "sort_order": 2,
                },
            ],
        },
        {
            "category_id": cat_map["other-subscriptions"],
            "name": "PICSART",
            "slug": "picsart",
            "image": "https://admin.boostghor.com/products/1779885191.jpg",
            "description": desc_picsart,
            "instructions": "সঠিক Gmail দিন। পিক্সআর্ট গোল্ড অ্যাকাউন্ট বা ইনভাইট মেইলে পাঠানো হবে।",
            "sort_order": 7,
            "fields": [
                {
                    "name": "gmail",
                    "label": "এখানে আপনার জিমেইল বসান",
                    "type": "email",
                    "placeholder": "yourname@gmail.com",
                    "is_required": True,
                    "sort_order": 1,
                }
            ],
            "packages": [
                {
                    "name": "Picsart Gold 1 Month",
                    "price": 120.0,
                    "compare_price": 180.0,
                    "duration": "1 Month",
                    "sort_order": 1,
                },
                {
                    "name": "Picsart Gold 1 Year",
                    "price": 490.0,
                    "compare_price": 750.0,
                    "duration": "1 Year",
                    "sort_order": 2,
                },
            ],
        },
        {
            "category_id": cat_map["other-subscriptions"],
            "name": "LIGHTROOM",
            "slug": "lightroom",
            "image": "https://admin.boostghor.com/products/1779885299.jpg",
            "description": desc_lightroom,
            "instructions": "সঠিক Gmail দিন। অ্যাডোবি লাইটরুম প্রিমিয়াম লগইন ডিটেইলস মেইলে দেওয়া হবে।",
            "sort_order": 8,
            "fields": [
                {
                    "name": "gmail",
                    "label": "এখানে আপনার জিমেইল বসান",
                    "type": "email",
                    "placeholder": "yourname@gmail.com",
                    "is_required": True,
                    "sort_order": 1,
                }
            ],
            "packages": [
                {
                    "name": "Lightroom Premium 1 Month",
                    "price": 140.0,
                    "compare_price": 200.0,
                    "duration": "1 Month",
                    "sort_order": 1,
                },
                {
                    "name": "Lightroom Premium 1 Year",
                    "price": 650.0,
                    "compare_price": 900.0,
                    "duration": "1 Year",
                    "sort_order": 2,
                },
            ],
        },

        # =====================================================================
        # 5. অন্যান্য সার্ভিস
        # =====================================================================
        {
            "category_id": cat_map["other-services"],
            "name": "NORD VPN",
            "slug": "nord-vpn",
            "image": "https://admin.boostghor.com/products/1776244018.jpg",
            "description": desc_vpn_nord,
            "instructions": "সঠিক Gmail Address দিন। নর্ড ভিপিএন আইডি ও পাসওয়ার্ড জিমেইলে প্রদান করা হবে।",
            "sort_order": 1,
            "fields": [
                {
                    "name": "gmail",
                    "label": "এখানে জিমেইল বসান",
                    "type": "email",
                    "placeholder": "yourname@gmail.com",
                    "is_required": True,
                    "sort_order": 1,
                }
            ],
            "packages": [
                {
                    "name": "1 Month - 1 Device",
                    "price": 140.0,
                    "compare_price": 200.0,
                    "duration": "1 Month",
                    "sort_order": 1,
                },
                {
                    "name": "6 Months - 1 Device",
                    "price": 550.0,
                    "compare_price": 750.0,
                    "duration": "6 Months",
                    "sort_order": 2,
                },
                {
                    "name": "1 Year - 1 Device",
                    "price": 950.0,
                    "compare_price": 1300.0,
                    "duration": "1 Year",
                    "sort_order": 3,
                },
            ],
        },
        {
            "category_id": cat_map["other-services"],
            "name": "EXPRESS VPN",
            "slug": "express-vpn",
            "image": "https://admin.boostghor.com/products/1776244031.jpg",
            "description": desc_vpn_express,
            "instructions": "সঠিক জিমেইল আইডি দিন। এক্সপ্রেস ভিপিএন কি ও লগইন তথ্য মেইলে পাঠানো হবে।",
            "sort_order": 2,
            "fields": [
                {
                    "name": "gmail",
                    "label": "এখানে জিমেইল আইডি বসান",
                    "type": "email",
                    "placeholder": "yourname@gmail.com",
                    "is_required": True,
                    "sort_order": 1,
                }
            ],
            "packages": [
                {
                    "name": "1 Month - 1 Device Key",
                    "price": 180.0,
                    "compare_price": 250.0,
                    "duration": "1 Month",
                    "sort_order": 1,
                },
                {
                    "name": "6 Months - 1 Device Key",
                    "price": 750.0,
                    "compare_price": 990.0,
                    "duration": "6 Months",
                    "sort_order": 2,
                },
                {
                    "name": "1 Year - 1 Device Key",
                    "price": 1350.0,
                    "compare_price": 1750.0,
                    "duration": "1 Year",
                    "sort_order": 3,
                },
            ],
        },
    ]

    # Clean up unwanted categories and products (like Streaming, Gaming, Productivity) and any associated test orders
    new_product_slugs = [p["slug"] for p in products_data]
    old_products = db.query(Product).filter(~Product.slug.in_(new_product_slugs)).all()
    for old_p in old_products:
        for item in list(old_p.order_items):
            if item.order:
                db.delete(item.order)
            else:
                db.delete(item)
        db.delete(old_p)
    db.commit()

    new_cat_slugs = [c["slug"] for c in categories_data]
    old_categories = db.query(Category).filter(~Category.slug.in_(new_cat_slugs)).all()
    for old_c in old_categories:
        for p in list(old_c.products):
            for item in list(p.order_items):
                if item.order:
                    db.delete(item.order)
                else:
                    db.delete(item)
            db.delete(p)
        db.delete(old_c)
    db.commit()

    for p_info in products_data:
        fields = p_info.pop("fields")
        packages = p_info.pop("packages")
        prod = db.query(Product).filter(Product.slug == p_info["slug"]).first()
        if not prod:
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
        else:
            for k, v in p_info.items():
                setattr(prod, k, v)
            db.commit()

            # Ensure fields and packages exist if missing
            if not prod.input_fields:
                for f_data in fields:
                    f_data["product_id"] = prod.id
                    field = ProductInputField(**f_data)
                    db.add(field)
            if not prod.packages:
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
