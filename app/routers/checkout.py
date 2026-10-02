"""
Checkout and Orders Router — Payment and order history endpoints.
"""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.middleware.auth import require_auth
from app.models.order import CheckoutRequest
from app.services.order_service import OrderService

router = APIRouter(prefix="/api", tags=["Checkout & Orders"])

order_service = OrderService()


@router.post("/checkout")
async def create_checkout(
    request: CheckoutRequest,
    current_user: dict = Depends(require_auth),
):
    """
    Process checkout: validate cart → create order → init payment.

    Returns a Paystack payment URL where the user completes payment.
    """
    result = await order_service.create_checkout(
        user_id=current_user["sub"],
        shipping_address=request.shipping_address.model_dump(),
        shipping_method=request.shipping_method,
    )
    return {"success": True, **result}


@router.get("/payments/verify")
async def verify_payment(
    reference: str = Query(..., description="Paystack payment reference"),
):
    """
    Verify payment after Paystack redirects back.

    Called when the user returns from Paystack's payment page.
    Also handles Paystack webhook callbacks.
    """
    order = await order_service.verify_and_complete_order(reference)
    return {"success": True, "order": order}


@router.get("/orders")
async def get_user_orders(current_user: dict = Depends(require_auth)):
    """Fetch all orders for the logged-in user, newest first."""
    orders = order_service.get_user_orders(current_user["sub"])
    return {"items": orders}


@router.get("/orders/{order_id}")
async def get_order_detail(
    order_id: UUID,
    current_user: dict = Depends(require_auth),
):
    """Fetch full details for a specific order."""
    order = order_service.get_order_detail(order_id)
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found",
        )
    return order
