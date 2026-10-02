"""
Order Service — Business logic for checkout and order management.

THE CHECKOUT FLOW (Like You're 5):
1. Customer says "I want to buy these books!"
2. We check: "Do we have enough books in stock?"
3. We calculate the total (books + shipping)
4. We tell Paystack "This person wants to pay ₦X"
5. Paystack gives us a payment page link
6. Customer pays on that page
7. Paystack tells us "They paid!" (webhook/verify)
8. We update the order status and reduce stock
9. We send a confirmation email

WHY we check stock AGAIN at checkout:
Between adding to cart and paying, someone else might have bought
the last copy. We must verify at the moment of purchase.
"""

import uuid
from decimal import Decimal
from uuid import UUID

from fastapi import HTTPException, status

from app.models.order import SHIPPING_METHODS
from app.repositories.book_repository import BookRepository
from app.repositories.cart_repository import CartRepository
from app.repositories.order_repository import OrderRepository
from app.services.email_service import EmailService
from app.services.payment_service import PaymentService


class OrderService:
    """Business logic for checkout and order operations."""

    def __init__(self):
        self.order_repo = OrderRepository()
        self.cart_repo = CartRepository()
        self.book_repo = BookRepository()
        self.payment_service = PaymentService()
        self.email_service = EmailService()

    async def create_checkout(
        self,
        user_id: UUID,
        shipping_address: dict,
        shipping_method: str,
    ) -> dict:
        """
        Process checkout: validate cart → create order → init payment.

        This is the most critical function in the entire app. It must
        be reliable and handle edge cases gracefully.
        """
        # Step 1: Get the user's cart
        cart = self.cart_repo.get_or_create_cart(user_id)
        cart_items = self.cart_repo.get_cart_items(cart["id"])

        if not cart_items:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Your cart is empty",
            )

        # Step 2: Validate stock for every item
        subtotal = Decimal("0.00")
        validated_items = []

        for item in cart_items:
            book = item.get("books", {})
            if book.get("stock_quantity", 0) < item["quantity"]:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=(
                        f"'{book.get('title', 'A book')}' only has "
                        f"{book.get('stock_quantity', 0)} copies left"
                    ),
                )

            unit_price = Decimal(str(item["unit_price"]))
            line_total = unit_price * item["quantity"]
            subtotal += line_total

            validated_items.append({
                "book_id": item["book_id"],
                "quantity": item["quantity"],
                "unit_price": float(unit_price),
                "title": book.get("title", ""),
                "cover_image_url": book.get("cover_image_url"),
            })

        # Step 3: Calculate shipping
        shipping_info = SHIPPING_METHODS.get(shipping_method, SHIPPING_METHODS["standard"])
        shipping_cost = shipping_info["cost"]
        total = subtotal + shipping_cost

        # Step 4: Create the order
        payment_reference = f"mira_{uuid.uuid4().hex[:12]}"

        order = self.order_repo.create_order({
            "user_id": str(user_id),
            "subtotal": float(subtotal),
            "shipping_cost": float(shipping_cost),
            "total": float(total),
            "shipping_method": shipping_method,
            "payment_reference": payment_reference,
            "status": "pending",
            "payment_status": "pending",
        })

        # Step 5: Create order items
        order_items_data = [
            {
                "order_id": order["id"],
                "book_id": item["book_id"],
                "quantity": item["quantity"],
                "unit_price": item["unit_price"],
            }
            for item in validated_items
        ]
        self.order_repo.create_order_items(order_items_data)

        # Step 6: Save shipping address snapshot
        self.order_repo.create_shipping_address({
            "order_id": order["id"],
            **shipping_address,
        })

        # Step 7: Initialize Paystack payment
        payment_data = await self.payment_service.initialize_payment(
            email=shipping_address["email"],
            amount=total,
            reference=payment_reference,
        )

        return {
            "order_id": order["id"],
            "order_number": order["order_number"],
            "total": total,
            "payment_url": payment_data["authorization_url"],
            "payment_reference": payment_reference,
        }

    async def verify_and_complete_order(self, reference: str) -> dict:
        """
        Verify payment with Paystack and complete the order.

        Called after the customer returns from Paystack's payment page
        or via webhook.
        """
        # Step 1: Verify with Paystack
        payment_data = await self.payment_service.verify_payment(reference)

        if payment_data.get("status") != "success":
            # Payment failed or pending
            order = self.order_repo.get_order_by_reference(reference)
            if order:
                self.order_repo.update_order_status(
                    order["id"], "failed", "failed"
                )
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Payment was not successful",
            )

        # Step 2: Find and update the order
        order = self.order_repo.get_order_by_reference(reference)
        if not order:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Order not found",
            )

        # Prevent double-processing
        if order["payment_status"] == "paid":
            return self.order_repo.get_order_by_id(order["id"])

        # Step 3: Mark order as paid
        self.order_repo.update_order_status(order["id"], "confirmed", "paid")

        # Step 4: Reduce stock for each book
        full_order = self.order_repo.get_order_by_id(order["id"])
        if full_order and full_order.get("order_items"):
            for item in full_order["order_items"]:
                self.book_repo.update_stock(
                    item["book_id"], -item["quantity"]
                )

        # Step 5: Clear the user's cart
        if order.get("user_id"):
            cart = self.cart_repo.get_or_create_cart(order["user_id"])
            self.cart_repo.clear_cart(cart["id"])

        # Step 6: Send confirmation email (async, non-blocking)
        if full_order and full_order.get("shipping_addresses"):
            email = full_order["shipping_addresses"].get("email", "")
            order_for_email = {
                "order_number": full_order["order_number"],
                "subtotal": full_order["subtotal"],
                "shipping_cost": full_order["shipping_cost"],
                "total": full_order["total"],
                "customer_name": full_order["shipping_addresses"].get("full_name", "Customer").split()[0],
                "items": [
                    {
                        "title": item.get("books", {}).get("title", "Book"),
                        "quantity": item["quantity"],
                        "unit_price": item["unit_price"],
                    }
                    for item in full_order.get("order_items", [])
                ],
            }
            await self.email_service.send_order_confirmation(
                order_for_email, email
            )

        return full_order

    def get_user_orders(self, user_id: UUID) -> list[dict]:
        """Fetch all orders for a user."""
        return self.order_repo.get_user_orders(user_id)

    def get_order_detail(self, order_id: UUID) -> dict | None:
        """Fetch full details for a single order."""
        return self.order_repo.get_order_by_id(order_id)
