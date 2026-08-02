from datetime import datetime

from pydantic import BaseModel, EmailStr, Field


class ProductOut(BaseModel):
    id: int
    sku: str
    name: str
    description: str
    category: str
    price_vnd: int
    stock: int
    image_hue: int
    image_emoji: str
    images: list[str] = []
    badge: str | None = None

    model_config = {"from_attributes": True}


class CategoryOut(BaseModel):
    name: str
    count: int


class RegisterIn(BaseModel):
    email: EmailStr
    password: str = Field(min_length=6, max_length=72)
    full_name: str = Field(min_length=2, max_length=120)
    phone: str = Field(default="", max_length=20)


class LoginIn(BaseModel):
    email: EmailStr
    password: str


class UserOut(BaseModel):
    id: int
    email: str
    full_name: str
    phone: str
    is_admin: bool

    model_config = {"from_attributes": True}


class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserOut


class CartItemIn(BaseModel):
    product_id: int
    quantity: int = Field(ge=1, le=99)


class CheckoutIn(BaseModel):
    customer_name: str = Field(min_length=2, max_length=120)
    customer_phone: str = Field(min_length=8, max_length=20)
    customer_address: str = Field(min_length=5, max_length=500)
    note: str | None = Field(default=None, max_length=500)
    items: list[CartItemIn] = Field(min_length=1)


class OrderItemOut(BaseModel):
    product_id: int
    product_name: str
    unit_price_vnd: int
    quantity: int

    model_config = {"from_attributes": True}


class BankTransferInfo(BaseModel):
    bank_name: str
    account_name: str
    account_number: str
    transfer_ref: str
    amount_vnd: int
    instruction: str


class OrderOut(BaseModel):
    id: int
    order_code: str
    transfer_ref: str
    customer_name: str
    customer_phone: str
    customer_address: str
    total_vnd: int
    status: str
    note: str | None = None
    paid_amount_vnd: int | None = None
    paid_at: datetime | None = None
    created_at: datetime
    user_id: int | None = None
    items: list[OrderItemOut]
    payment: BankTransferInfo | None = None

    model_config = {"from_attributes": True}


class MarkPaidIn(BaseModel):
    transfer_ref: str
    amount_vnd: int
    force_status: str | None = None


class AdminStatsOut(BaseModel):
    total: int
    pending_payment: int
    paid: int
    amount_mismatch: int
    failed: int
    cancelled: int
    expired: int
    revenue_paid_vnd: int


class FinancePointOut(BaseModel):
    period: str
    label: str
    inflow_vnd: int
    outflow_vnd: int
    profit_vnd: int
    orders_paid: int


class AdminFinanceOut(BaseModel):
    grain: str
    cost_ratio: float
    inflow_vnd: int
    outflow_vnd: int
    profit_vnd: int
    pending_vnd: int
    series: list[FinancePointOut]


class AdminOrderStatusIn(BaseModel):
    status: str
