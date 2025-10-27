"""
Multi-Factor Authentication (MFA/2FA) Support
Provides TOTP-based two-factor authentication using pyotp
"""
import pyotp
import qrcode
from io import BytesIO
import base64
from typing import Optional, Tuple
from app.core.config import settings
from app.core.logging import get_logger
import secrets
import string

logger = get_logger(__name__)


def generate_mfa_secret() -> str:
    """
    Generate a new MFA secret key for TOTP.

    Returns:
        str: Base32-encoded secret key
    """
    return pyotp.random_base32()


def generate_backup_codes(count: int = 10) -> list:
    """
    Generate backup codes for MFA recovery.

    Args:
        count: Number of backup codes to generate

    Returns:
        list: List of backup codes
    """
    backup_codes = []
    for _ in range(count):
        # Generate 8-character alphanumeric code
        code = ''.join(secrets.choice(string.ascii_uppercase + string.digits) for _ in range(8))
        # Format as XXXX-XXXX
        formatted_code = f"{code[:4]}-{code[4:]}"
        backup_codes.append(formatted_code)

    return backup_codes


def get_totp_uri(secret: str, username: str) -> str:
    """
    Generate TOTP provisioning URI for QR code.

    Args:
        secret: MFA secret key
        username: User's username or email

    Returns:
        str: TOTP URI
    """
    totp = pyotp.TOTP(secret)
    return totp.provisioning_uri(
        name=username,
        issuer_name=settings.MFA_ISSUER_NAME
    )


def generate_qr_code(uri: str) -> str:
    """
    Generate QR code image for TOTP URI.

    Args:
        uri: TOTP provisioning URI

    Returns:
        str: Base64-encoded QR code image
    """
    # Create QR code
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(uri)
    qr.make(fit=True)

    # Create image
    img = qr.make_image(fill_color="black", back_color="white")

    # Convert to base64
    buffer = BytesIO()
    img.save(buffer, format='PNG')
    buffer.seek(0)
    img_base64 = base64.b64encode(buffer.getvalue()).decode()

    return f"data:image/png;base64,{img_base64}"


def verify_totp_code(secret: str, code: str, window: int = 1) -> bool:
    """
    Verify a TOTP code.

    Args:
        secret: MFA secret key
        code: TOTP code to verify
        window: Number of time windows to check (default: 1)

    Returns:
        bool: True if code is valid, False otherwise
    """
    try:
        totp = pyotp.TOTP(secret)
        return totp.verify(code, valid_window=window)
    except Exception as e:
        logger.error(f"TOTP verification error: {e}")
        return False


def verify_backup_code(backup_codes: list, code: str) -> Tuple[bool, Optional[list]]:
    """
    Verify a backup code and remove it from the list if valid.

    Args:
        backup_codes: List of backup codes
        code: Backup code to verify

    Returns:
        tuple: (is_valid, updated_backup_codes)
    """
    # Normalize the code (remove spaces and dashes, convert to uppercase)
    normalized_code = code.replace(" ", "").replace("-", "").upper()

    for backup_code in backup_codes:
        normalized_backup = backup_code.replace(" ", "").replace("-", "").upper()

        if normalized_code == normalized_backup:
            # Code is valid, remove it from the list
            updated_codes = [c for c in backup_codes if c != backup_code]
            return True, updated_codes

    return False, backup_codes


def setup_mfa_for_user(username: str) -> dict:
    """
    Complete MFA setup for a user.

    Args:
        username: User's username or email

    Returns:
        dict: MFA setup data including secret, QR code, and backup codes
    """
    # Generate secret
    secret = generate_mfa_secret()

    # Generate TOTP URI
    uri = get_totp_uri(secret, username)

    # Generate QR code
    qr_code = generate_qr_code(uri)

    # Generate backup codes
    backup_codes = generate_backup_codes()

    return {
        "secret": secret,
        "qr_code": qr_code,
        "backup_codes": backup_codes,
        "uri": uri
    }


def validate_mfa_code(secret: str, code: str, backup_codes: Optional[list] = None) -> Tuple[bool, Optional[list], str]:
    """
    Validate MFA code (either TOTP or backup code).

    Args:
        secret: MFA secret key
        code: Code to validate
        backup_codes: List of backup codes (optional)

    Returns:
        tuple: (is_valid, updated_backup_codes, code_type)
            code_type: "totp" or "backup"
    """
    # First try TOTP
    if verify_totp_code(secret, code):
        return True, backup_codes, "totp"

    # Try backup codes if provided
    if backup_codes:
        is_valid, updated_codes = verify_backup_code(backup_codes, code)
        if is_valid:
            logger.info("Backup code used for MFA")
            return True, updated_codes, "backup"

    return False, backup_codes, "invalid"


def get_current_totp(secret: str) -> str:
    """
    Get the current TOTP code (for testing purposes).

    Args:
        secret: MFA secret key

    Returns:
        str: Current TOTP code
    """
    totp = pyotp.TOTP(secret)
    return totp.now()


def is_mfa_enabled(user) -> bool:
    """
    Check if MFA is enabled for a user.

    Args:
        user: User object

    Returns:
        bool: True if MFA is enabled
    """
    return bool(user.mfa_enabled and user.mfa_secret)


def require_mfa_verification(user) -> bool:
    """
    Check if user requires MFA verification.

    Args:
        user: User object

    Returns:
        bool: True if MFA verification is required
    """
    if not settings.MFA_ENABLED:
        return False

    return is_mfa_enabled(user)