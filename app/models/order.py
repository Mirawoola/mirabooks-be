"""
Order and Checkout Pydantic schemas.

The checkout flow converts a cart into a paid order through these steps:
1. Collect contact + shipping info
2. Choose delivery method
3. Initialize payment with Paystack
4. Verify payment webhook
5. Confirm order and send email
"""

from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field


# --- Shipping ---

SHIPPING_METHODS = {
    "standard": {"label": "Standard Delivery (5-7 days)", "cost": Decimal("1500.00")},
    "express": {"label": "Express Delivery (1-2 days)", "cost": Decimal("3500.00")},
    "pickup": {"label": "Store Pickup (Free)", "cost": Decimal("0.00")},
}


class ShippingAddressCreate(BaseModel):
    """Shipping address submitted during checkout."""

    full_name: str = Field(min_length=2, max_length=100)
    email: EmailStr
    phone: str = Field(min_length=10, max_length=15)
    street: str = Field(min_length=5, max_length=200)
    city: str = Field(min_length=2, max_length=100)
    state: str = Field(min_length=2, max_length=100)
    postal_code: str = ""
    country: str = "Nigeria"


# --- Checkout ---

class CheckoutRequest(BaseModel):
    """Complete checkout submission from the frontend."""

    shipping_address: ShippingAddressCreate
    shipping_method: str = Field(
        default="standard",
        pattern="^(standard|express|pickup)$",
    )


class CheckoutResponse(BaseModel):
    """Response after initiating checkout — includes Paystack payment URL."""

    order_id: UUID
    order_number: str
    total: Decimal
    payment_url: str
    payment_reference: str


# --- Order ---

class OrderItemResponse(BaseModel):
    """Single item within an order."""

    id: UUID
    book_id: UUID
    title: str
    cover_image_url: str | None = None
    quantity: int
    unit_price: Decimal
    line_total: Decimal


class OrderResponse(BaseModel):
    """Full order details returned to the user."""

    id: UUID
    order_number: str
    status: str
    subtotal: Decimal
    shipping_cost: Decimal
    total: Decimal
    shipping_method: str
    payment_status: str
    payment_reference: str | None = None
    items: list[OrderItemResponse] = []
    shipping_address: ShippingAddressCreate | None = None
    created_at: datetime | None = None


class PaystackWebhookPayload(BaseModel):
    """Payload from Paystack webhook notification."""

    event: str
    data: dict
