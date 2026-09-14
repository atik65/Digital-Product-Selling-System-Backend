from typing import List, Optional
from sqlalchemy.orm import Session, selectinload
from app.models.category import Category
from app.models.product import Product
from app.schemas.special_product import SpecialCategoryResponse, SpecialProductItem
from app.core.exceptions import DatabaseException


class SpecialProductService:
    def get_special_products_by_category(
        self,
        db: Session,
        active_only: bool = True,
        category_id: Optional[int] = None,
    ) -> List[SpecialCategoryResponse]:
        """
        Retrieves all categories and their nested products formatted specifically
        for the website landing page showcase matching the exact requested JSON structure.
        """
        try:
            query = (
                db.query(Category)
                .filter(Category.is_deleted.is_(False))
                .options(
                    selectinload(Category.products).selectinload(Product.packages),
                    selectinload(Category.products).selectinload(Product.input_fields),
                )
            )

            if active_only:
                query = query.filter(Category.is_active.is_(True))

            if category_id is not None:
                query = query.filter(Category.id == category_id)

            categories = query.order_by(
                Category.sort_order.asc(), Category.id.asc()
            ).all()

            result: List[SpecialCategoryResponse] = []

            for cat in categories:
                # Filter and order active products for this category
                prod_list = [
                    p
                    for p in cat.products
                    if not p.is_deleted and (not active_only or p.is_active)
                ]
                prod_list.sort(key=lambda p: (p.sort_order if p.sort_order is not None else 0, p.id))

                mapped_products: List[SpecialProductItem] = []

                for prod in prod_list:
                    # Calculate lowest package price if packages exist
                    active_pkgs = [
                        pkg
                        for pkg in prod.packages
                        if not pkg.is_deleted and (not active_only or pkg.is_active)
                    ]
                    if active_pkgs:
                        lowest_price = min(pkg.price for pkg in active_pkgs)
                    else:
                        lowest_price = 1.0

                    # Format prices
                    buy_price_str = f"{lowest_price:.3f}"
                    sale_price_val = (
                        int(lowest_price)
                        if lowest_price.is_integer()
                        else round(lowest_price, 2)
                    )

                    # Dynamic input fields mapping
                    active_fields = [
                        f for f in prod.input_fields if not f.is_deleted
                    ]
                    active_fields.sort(key=lambda f: (f.sort_order if f.sort_order is not None else 0, f.id))

                    first_input = (
                        active_fields[0].label
                        if active_fields
                        else (prod.instructions or "এখানে আপনার তথ্য বসান")
                    )
                    sec_input = (
                        active_fields[1].label
                        if len(active_fields) > 1
                        else "null"
                    )

                    # Timestamps ISO format
                    p_created = prod.created_at.isoformat() if prod.created_at else None
                    p_updated = prod.updated_at.isoformat() if prod.updated_at else None

                    item = SpecialProductItem(
                        id=prod.id,
                        name=prod.name,
                        brand_id=cat.id,
                        category_id=0,
                        lavel=prod.sort_order if prod.sort_order is not None else 1,
                        description=prod.description or "null",
                        tag_line="null",
                        logo=prod.image or "null",
                        buy_price=buy_price_str,
                        sale_price=sale_price_val,
                        is_shop=1,
                        quantity=999999,
                        type=1,
                        is_auto=0,
                        is_active=1 if prod.is_active else 0,
                        is_hot="0",
                        created_at=p_created,
                        updated_at=p_updated,
                        check_id=0,
                        slug=prod.slug or "null",
                        have_time_limite=0,
                        limite_qty=0,
                        limite_duration=0,
                        is_reseller=0,
                        input_name=first_input,
                        main_price=0,
                        is_qty_minus=0,
                        is_user_show_qty=0,
                        is_remove_char=0,
                        sec_input_name=sec_input,
                        redem_link="null",
                        package_design=2,
                        check_unique_player_id=0,
                        is_premium=0,
                        premium_min_amount=10000,
                    )
                    mapped_products.append(item)

                cat_created = cat.created_at.isoformat() if cat.created_at else None
                cat_updated = cat.updated_at.isoformat() if cat.updated_at else None

                cat_response = SpecialCategoryResponse(
                    id=cat.id,
                    name=cat.name,
                    logo=cat.image or "null",
                    created_at=cat_created,
                    updated_at=cat_updated,
                    lavel=cat.sort_order if cat.sort_order is not None else 1,
                    is_active=1 if cat.is_active else 0,
                    product_design=1,
                    products=mapped_products,
                )
                result.append(cat_response)

            return result
        except Exception as e:
            raise DatabaseException(
                f"Failed to fetch landing page special products: {str(e)}",
                original_exception=e,
            )
