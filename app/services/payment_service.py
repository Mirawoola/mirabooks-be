"""
Payment Service — Paystack integration.

HOW PAYSTACK WORKS (Like You're 5):
1. Customer wants to pay → we tell Paystack "Someone wants to pay ₦5000"
2. Paystack creates a special payment page and gives us the link
3. We send the customer to that link
4. Customer pays on Paystack's secure page (we never see card details!)
5. Paystack tells us "Payment successful!" (via redirect + webhook)
6. We verify the payment and confirm the order

WHY we never handle card details directly:
- It's MUCH safer (PCI compliance)
- Paystack handles all the security
- If something goes wrong, it's Paystack's responsibility
"""

from decimal import Decimal

import httpx

from app.config import settings


PAYSTACK_BASE_URL = "https://api.paystack.co"


class PaymentService:
    """Handles Paystack payment initialization and verification."""

    def __init__(self):
        self.headers = {
            "Authorization": f"Bearer {settings.paystack_secret_key}",
            "Content-Type": "application/json",
        }

    async def initialize_payment(
        self,
        email: str,
        amount: Decimal,
        reference: str,
        callback_url: str | None = None,
    ) -> dict:
        """
        Initialize a Paystack transaction.

        Args:
            email: Customer's email address
            amount: Amount in Naira (we convert to kobo for Paystack)
            reference: Our unique order reference
            callback_url: Where Paystack redirects after payment

        Returns:
            Dict with authorization_url (the payment page link)
        """
        # Paystack expects amount in kobo (smallest currency unit)
        # ₦1 = 100 kobo, so ₦5000 = 500000 kobo
        amount_in_kobo = int(amount * 100)

        redirect_url = callback_url or (
            f"{settings.frontend_url}/order-confirmation"
        )

        payload = {
            "email": email,
            "amount": amount_in_kobo,
            "reference": reference,
            "callback_url": redirect_url,
            "currency": "NGN",
        }

        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{PAYSTACK_BASE_URL}/transaction/initialize",
                json=payload,
                headers=self.headers,
            )

        result = response.json()

        if not result.get("status"):
            raise ValueError(
                f"Paystack initialization failed: {result.get('message')}"
            )

        return result["data"]

    async def verify_payment(self, reference: str) -> dict:
        """
        Verify a payment after Paystack redirects back.

        We ALWAYS verify on our server — never trust the frontend
        alone to confirm payment. A malicious user could skip the
        payment and tell us "I paid!" without actually paying.
        """
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{PAYSTACK_BASE_URL}/transaction/verify/{reference}",
                headers=self.headers,
            )

        result = response.json()

        if not result.get("status"):
            raise ValueError(
                f"Payment verification failed: {result.get('message')}"
            )

        return result["data"]
