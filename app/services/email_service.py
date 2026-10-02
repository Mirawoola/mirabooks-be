"""
Email Service — Mailgun integration for order confirmation emails.

HOW MAILGUN WORKS (Like You're 5):
When you buy books, we send you a letter (email) saying "Thank you!
Here's what you ordered." Mailgun is like a super-fast postal service
that delivers emails for us.

WHY Mailgun instead of sending emails ourselves?
- Email delivery is HARD (spam filters, reputation, etc.)
- Mailgun is an expert at getting emails into inboxes
- We just write the letter, Mailgun delivers it
"""

import httpx

from app.config import settings


class EmailService:
    """Handles sending transactional emails via Mailgun."""

    def __init__(self):
        self.api_url = (
            f"https://api.mailgun.net/v3/{settings.mailgun_domain}/messages"
        )
        self.auth = ("api", settings.mailgun_api_key)

    async def send_order_confirmation(self, order: dict, email: str) -> bool:
        """
        Send an order confirmation email after successful payment.

        Args:
            order: The complete order data including items
            email: Customer's email address

        Returns:
            True if email was sent successfully, False otherwise
        """
        from pybars import Compiler
        import os

        # Format currency safely
        def format_currency(value):
            if value is None:
                return "0.00"
            return f"{float(value):,.2f}"
            
        items = []
        for item in order.get("items", []):
            items.append({
                "title": item.get("title", "Book"),
                "quantity": item.get("quantity", 1),
                "unit_price": format_currency(item.get("unit_price", 0))
            })
            
        template_data = {
            "customer_name": order.get("customer_name", "Customer"),
            "order_number": order.get("order_number", "N/A"),
            "items": items,
            "subtotal": format_currency(order.get("subtotal", 0)),
            "shipping_cost": format_currency(order.get("shipping_cost", 0)),
            "total": format_currency(order.get("total", 0))
        }

        # Load Handlebars template
        template_path = os.path.join(os.path.dirname(__file__), "..", "templates", "order_confirmation.hbs")
        with open(template_path, "r", encoding="utf-8") as f:
            source = f.read()
            
        compiler = Compiler()
        template = compiler.compile(source)
        html_body = template(template_data)

        try:
            import aiosmtplib
            from email.message import EmailMessage

            msg = EmailMessage()
            msg.set_content("Please enable HTML to view this email.")
            msg.add_alternative(html_body, subtype='html')
            
            msg['Subject'] = f"Order Confirmed! #{order.get('order_number', '')}"
            msg['From'] = f"Mirabooks <{settings.mailgun_sender_email}>"
            msg['To'] = email

            await aiosmtplib.send(
                msg,
                hostname="smtp.mailgun.org",
                port=587,
                start_tls=True,
                username=f"postmaster@{settings.mailgun_domain}",
                password=settings.mailgun_api_key,
                timeout=15.0
            )
            return True
        except Exception as e:
            print(f"[EMAIL ERROR] Failed to send SMTP email: {e}")
            return False
