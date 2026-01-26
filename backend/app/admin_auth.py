"""
Admin authentication using TOTP (Time-based One-Time Password).
Uses Google Authenticator-compatible TOTP codes.
"""
import pyotp
import qrcode
import io
import base64
from fastapi import HTTPException, Header
from typing import Optional

from .config import get_settings

settings = get_settings()


def generate_totp_secret() -> str:
    """Generate a new TOTP secret (base32 encoded)."""
    return pyotp.random_base32()


def get_totp_uri(secret: str, name: str = "Word Registry Admin") -> str:
    """
    Get TOTP URI for QR code generation.

    Args:
        secret: TOTP secret key
        name: Display name in authenticator app

    Returns:
        otpauth:// URI string
    """
    totp = pyotp.TOTP(secret)
    return totp.provisioning_uri(name=name, issuer_name="Word Registry")


def generate_qr_code(totp_uri: str) -> str:
    """
    Generate QR code image for TOTP setup.

    Args:
        totp_uri: otpauth:// URI string

    Returns:
        Base64-encoded PNG image
    """
    qr = qrcode.QRCode(version=1, box_size=10, border=5)
    qr.add_data(totp_uri)
    qr.make(fit=True)

    img = qr.make_image(fill_color="black", back_color="white")

    # Convert to base64
    buffer = io.BytesIO()
    img.save(buffer, format='PNG')
    buffer.seek(0)
    img_base64 = base64.b64encode(buffer.getvalue()).decode()

    return f"data:image/png;base64,{img_base64}"


def verify_totp_code(code: str, secret: Optional[str] = None) -> bool:
    """
    Verify a TOTP code.

    Args:
        code: 6-digit TOTP code from authenticator app
        secret: TOTP secret (uses config if not provided)

    Returns:
        True if code is valid, False otherwise
    """
    if secret is None:
        secret = settings.admin_totp_secret

    if not secret:
        raise ValueError("ADMIN_TOTP_SECRET not configured")

    totp = pyotp.TOTP(secret)

    # Verify with window of 1 (allows for 30-second time skew)
    return totp.verify(code, valid_window=1)


async def verify_admin_token(x_admin_token: Optional[str] = Header(None)) -> bool:
    """
    FastAPI dependency to verify admin TOTP token.

    Usage:
        @router.get("/admin/endpoint")
        async def admin_endpoint(authorized: bool = Depends(verify_admin_token)):
            ...

    Args:
        x_admin_token: TOTP code from X-Admin-Token header

    Raises:
        HTTPException: If token is invalid or missing

    Returns:
        True if authorized
    """
    if not x_admin_token:
        raise HTTPException(
            status_code=401,
            detail="Admin authentication required. Provide X-Admin-Token header."
        )

    # Remove any whitespace
    code = x_admin_token.strip().replace(" ", "")

    # Validate format (6 digits)
    if not code.isdigit() or len(code) != 6:
        raise HTTPException(
            status_code=401,
            detail="Invalid admin token format. Must be 6 digits."
        )

    # Verify TOTP code
    if not verify_totp_code(code):
        raise HTTPException(
            status_code=401,
            detail="Invalid or expired admin token."
        )

    return True


def get_setup_info() -> dict:
    """
    Get TOTP setup information for first-time configuration.

    Returns:
        Dictionary with:
        - secret: TOTP secret to store in .env
        - qr_code: Base64-encoded QR code image
        - manual_entry: Secret for manual entry
    """
    secret = settings.admin_totp_secret

    if not secret:
        raise ValueError(
            "ADMIN_TOTP_SECRET not configured. "
            "Generate one with: python -c \"import pyotp; print(pyotp.random_base32())\""
        )

    totp_uri = get_totp_uri(secret)
    qr_code = generate_qr_code(totp_uri)

    return {
        "secret": secret,
        "qr_code": qr_code,
        "manual_entry": secret,
        "instructions": (
            "1. Install Google Authenticator or similar app on your phone\n"
            "2. Scan the QR code or manually enter the secret\n"
            "3. Use the 6-digit code from your app to access admin panel"
        )
    }
