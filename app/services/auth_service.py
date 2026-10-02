"""
Auth Service — Google OAuth and JWT token management.

HOW GOOGLE AUTH WORKS (Like You're 5):
1. User clicks "Sign in with Google" on the website
2. Google shows a popup: "Do you want to let Mirabooks know who you are?"
3. User says yes → Google gives us a special note (ID token)
4. We read the note to learn the user's name and email
5. We create our OWN wristband (JWT) so the user doesn't have to
   show Google's note every single time

WHY we make our own JWT instead of using Google's token directly:
- Google's token expires in ~1 hour
- We want to control how long our sessions last
- We can add custom data to our token (like user_id)
"""

from datetime import datetime, timedelta, timezone

import httpx
from jose import jwt

from app.config import settings
from app.repositories.user_repository import UserRepository


# Google's public endpoint to verify ID tokens
GOOGLE_TOKEN_INFO_URL = "https://oauth2.googleapis.com/tokeninfo"


class AuthService:
    """Handles Google OAuth verification and JWT token creation."""

    def __init__(self):
        self.user_repo = UserRepository()

    async def verify_google_token(self, credential: str) -> dict:
        """
        Verify a Google ID token and extract user information.

        We call Google's tokeninfo endpoint to verify the token is
        real and was issued for OUR app (matching our client_id).
        """
        async with httpx.AsyncClient() as client:
            response = await client.get(
                GOOGLE_TOKEN_INFO_URL,
                params={"id_token": credential},
            )

        if response.status_code != 200:
            print(f"[AUTH DEBUG] Google tokeninfo failed: status={response.status_code}, body={response.text}")
            raise ValueError("Invalid Google token")

        token_data = response.json()
        print(f"[AUTH DEBUG] Token aud={token_data.get('aud')}, expected={settings.google_client_id}")

        # Verify the token was issued for our app
        if token_data.get("aud") != settings.google_client_id:
            raise ValueError("Token was not issued for this application")

        return {
            "email": token_data["email"],
            "full_name": token_data.get("name", ""),
            "avatar_url": token_data.get("picture", ""),
        }

    def get_or_create_user(self, google_data: dict) -> dict:
        """
        Find existing user or create a new one from Google data.

        This is idempotent: calling it twice with the same email
        returns the same user without creating duplicates.
        """
        existing_user = self.user_repo.get_user_by_email(google_data["email"])

        if existing_user:
            # Update avatar and name in case they changed on Google's side
            return self.user_repo.update_user(
                existing_user["id"],
                {
                    "full_name": google_data["full_name"],
                    "avatar_url": google_data["avatar_url"],
                },
            )

        return self.user_repo.create_user({
            "email": google_data["email"],
            "full_name": google_data["full_name"],
            "avatar_url": google_data["avatar_url"],
            "auth_provider": "google",
        })

    def create_jwt_token(self, user: dict) -> str:
        """
        Create a JWT token containing the user's ID and email.

        This token is what the frontend sends with every request
        (in the Authorization header) to prove who they are.
        """
        expiration = datetime.now(timezone.utc) + timedelta(
            hours=settings.jwt_expiration_hours
        )
        payload = {
            "sub": user["id"],
            "email": user["email"],
            "full_name": user.get("full_name", ""),
            "exp": expiration,
        }
        return jwt.encode(
            payload,
            settings.app_secret_key,
            algorithm=settings.jwt_algorithm,
        )

    async def authenticate_with_google(self, credential: str) -> dict:
        """
        Complete Google auth flow: verify token → get/create user → issue JWT.

        Returns the user profile and JWT token for the frontend to store.
        """
        google_data = await self.verify_google_token(credential)
        user = self.get_or_create_user(google_data)
        token = self.create_jwt_token(user)

        return {
            "user": user,
            "token": token,
        }
