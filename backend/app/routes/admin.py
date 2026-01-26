"""
Admin API routes.
Protected with TOTP authentication.
"""
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
from decimal import Decimal
from typing import Optional

from ..database import get_db
from ..admin_auth import verify_admin_token, get_setup_info
from ..admin_service import AdminService
from ..ratelimit import limiter

router = APIRouter(prefix="/api/admin", tags=["admin"])


class LoginRequest(BaseModel):
    """Admin login request."""
    totp_code: str = Field(..., min_length=6, max_length=6)


class ResetWordRequest(BaseModel):
    """Request to reset a word's price and ownership."""
    word: str
    new_price: Decimal = Field(..., gt=0)
    owner_name: Optional[str] = None
    owner_message: Optional[str] = Field(None, max_length=140)


@router.post("/login")
@limiter.limit("10/minute")
async def admin_login(request: Request, login_data: LoginRequest):
    """
    Verify admin TOTP code.

    Returns a success message if code is valid.
    Frontend should store the code and send it with subsequent requests.

    Args:
        login_data: TOTP code from authenticator app

    Returns:
        Success message and instructions
    """
    from ..admin_auth import verify_totp_code

    if not verify_totp_code(login_data.totp_code):
        raise HTTPException(
            status_code=401,
            detail="Invalid or expired authentication code"
        )

    return {
        "success": True,
        "message": "Authentication successful",
        "instructions": "Include X-Admin-Token header with TOTP code in all admin requests"
    }


@router.get("/setup")
@limiter.limit("5/minute")
async def admin_setup(request: Request):
    """
    Get TOTP setup information (QR code for first-time setup).

    IMPORTANT: This endpoint should be disabled in production or require
    a separate setup token. It's only for initial configuration.

    Returns:
        QR code and setup instructions
    """
    try:
        setup_info = get_setup_info()
        return setup_info
    except ValueError as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/dashboard")
async def get_dashboard(
    authorized: bool = Depends(verify_admin_token),
    db: Session = Depends(get_db)
):
    """
    Get admin dashboard summary.

    Requires: X-Admin-Token header with valid TOTP code

    Returns:
        Dashboard data including income, popular words, and errors
    """
    return AdminService.get_dashboard_summary(db)


@router.get("/income")
async def get_income_stats(
    authorized: bool = Depends(verify_admin_token),
    db: Session = Depends(get_db)
):
    """
    Get income statistics (excluding admin actions).

    Requires: X-Admin-Token header with valid TOTP code

    Returns:
        Income statistics for total, today, and this week
    """
    return AdminService.get_income_stats(db)


@router.get("/popular-words")
async def get_popular_words(
    limit: int = 20,
    authorized: bool = Depends(verify_admin_token),
    db: Session = Depends(get_db)
):
    """
    Get most viewed words in the last 30 days.

    Requires: X-Admin-Token header with valid TOTP code

    Args:
        limit: Number of results (default: 20)

    Returns:
        List of most viewed words with view counts
    """
    return AdminService.get_most_viewed_words(db, limit)


@router.get("/errors")
async def get_recent_errors(
    limit: int = 50,
    authorized: bool = Depends(verify_admin_token),
    db: Session = Depends(get_db)
):
    """
    Get recent error logs.

    Requires: X-Admin-Token header with valid TOTP code

    Args:
        limit: Number of results (default: 50)

    Returns:
        List of recent errors
    """
    return AdminService.get_recent_errors(db, limit)


@router.post("/reset-word")
async def reset_word(
    reset_data: ResetWordRequest,
    authorized: bool = Depends(verify_admin_token),
    db: Session = Depends(get_db)
):
    """
    Reset a word's price and optionally set owner.

    This creates a transaction marked as admin action (won't count in revenue).

    Requires: X-Admin-Token header with valid TOTP code

    Args:
        reset_data: Word text, new price, and optional owner info

    Returns:
        Updated word information
    """
    try:
        word = AdminService.reset_word(
            db=db,
            word_text=reset_data.word,
            new_price=reset_data.new_price,
            owner_name=reset_data.owner_name,
            owner_message=reset_data.owner_message
        )

        return {
            "success": True,
            "message": f"Word '{word.text}' has been reset",
            "word": {
                "text": word.text,
                "price": float(word.price),
                "owner_name": word.owner_name,
                "owner_message": word.owner_message,
                "lockout_ends_at": word.lockout_ends_at.isoformat() if word.lockout_ends_at else None
            }
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
