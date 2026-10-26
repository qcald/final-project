"""Password hashing and session tokens for Friend Recs accounts.

New accounts are hashed with PBKDF2-HMAC-SHA256 and stored in a self-describing
format so the parameters live alongside the hash:

    pbkdf2_sha256$<iterations>$<salt_hex>$<hash_hex>

Sessions use a stateless HMAC-signed token (no server-side store):

    <base64url(user_id)>.<base64url(hmac_sha256(secret, user_id))>
"""

import base64
import hashlib
import hmac
import secrets
from pathlib import Path

ALGORITHM = "pbkdf2_sha256"
ITERATIONS = 390_000
SALT_BYTES = 16

_SECRET_PATH = Path(__file__).resolve().parent / ".auth_secret"


def _load_secret() -> bytes:
    """Load (or create once) the key used to sign session tokens."""
    if _SECRET_PATH.exists():
        return _SECRET_PATH.read_bytes()
    secret = secrets.token_bytes(32)
    _SECRET_PATH.write_bytes(secret)
    return secret


_SECRET = _load_secret()


def hash_password(password: str) -> str:
    salt = secrets.token_bytes(SALT_BYTES)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, ITERATIONS)
    return f"{ALGORITHM}${ITERATIONS}${salt.hex()}${digest.hex()}"


def verify_password(password: str, stored: str) -> bool:
    """Check a password against a stored hash. Only the 4-field format above
    can be verified; legacy 3-field seed hashes have unknown iterations."""
    try:
        algorithm, iterations, salt_hex, digest_hex = stored.split("$")
    except ValueError:
        return False
    if algorithm != ALGORITHM:
        return False
    expected = hashlib.pbkdf2_hmac(
        "sha256", password.encode(), bytes.fromhex(salt_hex), int(iterations)
    )
    return hmac.compare_digest(expected.hex(), digest_hex)


def _b64(raw: bytes) -> str:
    return base64.urlsafe_b64encode(raw).rstrip(b"=").decode()


def _unb64(text: str) -> bytes:
    return base64.urlsafe_b64decode(text + "=" * (-len(text) % 4))


def create_token(user_id: int) -> str:
    payload = str(user_id).encode()
    signature = hmac.new(_SECRET, payload, hashlib.sha256).digest()
    return f"{_b64(payload)}.{_b64(signature)}"


def verify_token(token: str) -> int | None:
    """Return the user id encoded in a valid token, or None."""
    try:
        payload_b64, signature_b64 = token.split(".")
        payload = _unb64(payload_b64)
        expected = hmac.new(_SECRET, payload, hashlib.sha256).digest()
        if not hmac.compare_digest(expected, _unb64(signature_b64)):
            return None
        return int(payload)
    except (ValueError, TypeError):
        return None


def create_invite_code(user_id: int) -> str:
    """A shareable code that says "befriend this user". Signed with a different label than session
    tokens, so an invite code can never be used to log in."""
    payload = str(user_id).encode()
    signature = hmac.new(_SECRET, b"invite:" + payload, hashlib.sha256).digest()[:12]
    return f"{_b64(payload)}.{_b64(signature)}"


def verify_invite_code(code: str) -> int | None:
    """Return the inviting user's id for a valid invite code, or None."""
    try:
        payload_b64, signature_b64 = code.split(".")
        payload = _unb64(payload_b64)
        expected = hmac.new(_SECRET, b"invite:" + payload, hashlib.sha256).digest()[:12]
        if not hmac.compare_digest(expected, _unb64(signature_b64)):
            return None
        return int(payload)
    except (ValueError, TypeError):
        return None
