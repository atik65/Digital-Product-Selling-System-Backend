from app.models.category import Category
from app.models.product import Product
from app.models.package import Package
from app.models.product_input_field import ProductInputField


def test_special_products_endpoint_and_sample_structure(client, db):
    # Setup test data
    cat = Category(
        name="ফেসবুক সার্ভিস",
        slug="facebook-services",
        image="1741968472.jpg",
        sort_order=2,
        is_active=True,
    )
    db.add(cat)
    db.commit()
    db.refresh(cat)

    prod = Product(
        name="PAGE FOLLOWER",
        slug="page-follower",
        category_id=cat.id,
        image="1776244581.jpg",
        description="<p>⦿ অর্ডার করার সময় সঠিক লিংক দিবেন</p>",
        instructions="এখানে পেইজ লিংক বসান",
        sort_order=1,
        is_active=True,
    )
    db.add(prod)
    db.commit()
    db.refresh(prod)

    pkg = Package(
        product_id=prod.id,
        name="1000 Followers",
        price=1.0,
        sort_order=1,
        is_active=True,
    )
    db.add(pkg)

    field = ProductInputField(
        product_id=prod.id,
        name="page_url",
        label="এখানে পেইজ লিংক বসান",
        type="text",
        is_required=True,
        sort_order=1,
    )
    db.add(field)
    db.commit()

    # 1. Test primary endpoint returns list matching sample
    res = client.get("/api/v1/special-products")
    assert res.status_code == 200
    data = res.json()
    assert isinstance(data, list)
    assert len(data) >= 1

    first_cat = data[0]
    expected_cat_keys = {
        "id",
        "name",
        "logo",
        "created_at",
        "updated_at",
        "lavel",
        "is_active",
        "product_design",
        "products",
    }
    assert expected_cat_keys.issubset(first_cat.keys())
    assert isinstance(first_cat["products"], list)
    assert len(first_cat["products"]) >= 1

    first_prod = first_cat["products"][0]
    expected_prod_keys = {
        "id",
        "name",
        "brand_id",
        "category_id",
        "lavel",
        "description",
        "tag_line",
        "logo",
        "buy_price",
        "sale_price",
        "is_shop",
        "quantity",
        "type",
        "is_auto",
        "is_active",
        "is_hot",
        "created_at",
        "updated_at",
        "check_id",
        "slug",
        "have_time_limite",
        "limite_qty",
        "limite_duration",
        "is_reseller",
        "input_name",
        "main_price",
        "is_qty_minus",
        "is_user_show_qty",
        "is_remove_char",
        "sec_input_name",
        "redem_link",
        "package_design",
        "check_unique_player_id",
        "is_premium",
        "premium_min_amount",
    }
    assert expected_prod_keys.issubset(first_prod.keys())
    assert first_prod["brand_id"] == first_cat["id"]
    assert first_prod["name"] == "PAGE FOLLOWER"
    assert first_prod["input_name"] == "এখানে পেইজ লিংক বসান"
    assert first_prod["buy_price"] == "1.000"
    assert first_prod["sale_price"] == 1


def test_special_products_envelope_mode(client, db):
    cat = Category(name="Test Cat", slug="test-cat", is_active=True)
    db.add(cat)
    db.commit()

    res = client.get("/api/v1/special-products?envelope=true")
    assert res.status_code == 200
    body = res.json()
    assert isinstance(body, dict)
    assert body["success"] is True
    assert body["status_code"] == 200
    assert isinstance(body["data"], list)


def test_special_products_aliases_and_filters(client, db):
    cat1 = Category(name="Cat 1", slug="cat-1", is_active=True)
    cat2 = Category(name="Cat 2", slug="cat-2", is_active=False)
    db.add_all([cat1, cat2])
    db.commit()

    # Alias /api/v1/products/special
    r1 = client.get("/api/v1/products/special")
    assert r1.status_code == 200
    assert isinstance(r1.json(), list)

    # Root alias /special-products
    r2 = client.get("/special-products")
    assert r2.status_code == 200
    assert isinstance(r2.json(), list)

    # Filter by category_id
    r3 = client.get(f"/api/v1/special-products?category_id={cat1.id}")
    assert r3.status_code == 200
    assert len(r3.json()) == 1
    assert r3.json()[0]["id"] == cat1.id

    # Filter active_only=false includes inactive
    r4 = client.get("/api/v1/special-products?active_only=false")
    assert r4.status_code == 200
    cat_ids = [c["id"] for c in r4.json()]
    assert cat1.id in cat_ids
    assert cat2.id in cat_ids
