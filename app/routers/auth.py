"""
Auth Router — Google OAuth login endpoints.
"""

from fastapi import APIRouter, Depends, HTTPException, status

from app.middleware.auth import require_auth
from app.models.user import GoogleAuthRequest
from app.services.auth_service import AuthService

router = APIRouter(prefix="/api/auth", tags=["Authentication"])

auth_service = AuthService()


@router.post("/google")
async def google_login(request: GoogleAuthRequest):
    """
    Authenticate with Google OAuth.

    The frontend sends the Google ID token (credential) it received
    from Google's sign-in popup. We verify it and return our JWT.
    """
    try:
        result = await auth_service.authenticate_with_google(request.credential)
        return {
            "success": True,
            "user": result["user"],
            "token": result["token"],
        }
    except ValueError as err:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(err),
        ) from err


@router.get("/me")
async def get_current_user(current_user: dict = Depends(require_auth)):
    """
    Get the currently logged-in user's profile.

    Requires a valid JWT token in the Authorization header.
    """
    return {
        "success": True,
        "user": current_user,
    }


@router.post("/logout")
async def logout():
    """
    Logout the user.

    Since we use JWT (stateless tokens), logout is handled on the
    frontend by deleting the stored token. This endpoint exists for
    API completeness and can be extended later (e.g., token blacklist).
    """
    return {
        "success": True,
        "message": "Logged out successfully",
    }
