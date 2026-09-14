from typing import Optional, List, Union
from pydantic import BaseModel, ConfigDict


class SpecialProductItem(BaseModel):
    id: int
    name: str
    brand_id: int
    category_id: int = 0
    lavel: int = 1
    description: Optional[str] = "null"
    tag_line: Optional[str] = "null"
    logo: Optional[str] = "null"
    buy_price: str = "1.000"
    sale_price: Union[int, float] = 1
    is_shop: int = 1
    quantity: int = 999999
    type: int = 1
    is_auto: int = 0
    is_active: int = 1
    is_hot: str = "0"
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    check_id: int = 0
    slug: Optional[str] = "null"
    have_time_limite: int = 0
    limite_qty: int = 0
    limite_duration: int = 0
    is_reseller: int = 0
    input_name: Optional[str] = "এখানে আপনার তথ্য বসান"
    main_price: Union[int, float] = 0
    is_qty_minus: int = 0
    is_user_show_qty: int = 0
    is_remove_char: int = 0
    sec_input_name: Optional[str] = "null"
    redem_link: Optional[str] = "null"
    package_design: int = 2
    check_unique_player_id: int = 0
    is_premium: int = 0
    premium_min_amount: int = 10000

    model_config = ConfigDict(from_attributes=True)


class SpecialCategoryResponse(BaseModel):
    id: int
    name: str
    logo: Optional[str] = "null"
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    lavel: int = 1
    is_active: int = 1
    product_design: int = 1
    products: List[SpecialProductItem] = []

    model_config = ConfigDict(from_attributes=True)
