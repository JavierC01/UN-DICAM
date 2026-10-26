import base64
import hashlib
import hmac
import json
import secrets
import time

_ALGORITHM = "sha256"
_ITERATIONS = 260_000


def hash_password(password: str) -> str:
    salt = secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac(_ALGORITHM, password.encode("utf-8"), salt.encode("utf-8"), _ITERATIONS)
    return f"{salt}${digest.hex()}"


def verify_password(password: str, hashed_password: str) -> bool:
    salt, _, digest_hex = hashed_password.partition("$")
    if not digest_hex:
        return False
    expected = hashlib.pbkdf2_hmac(_ALGORITHM, password.encode("utf-8"), salt.encode("utf-8"), _ITERATIONS)
    return hmac.compare_digest(expected.hex(), digest_hex)


def _b64(datos: bytes) -> str:
    return base64.urlsafe_b64encode(datos).rstrip(b"=").decode("ascii")


def _desde_b64(texto: str) -> bytes:
    return base64.urlsafe_b64decode(texto + "=" * (-len(texto) % 4))


def crear_token(user_id: str, secret_key: str, minutos: int) -> str:
    """JWT HS256 firmado con SECRET_KEY; el claim sub es el id del usuario."""
    header = _b64(json.dumps({"alg": "HS256", "typ": "JWT"}).encode())
    payload = _b64(json.dumps({"sub": user_id, "exp": int(time.time()) + minutos * 60}).encode())
    firma = hmac.new(secret_key.encode(), f"{header}.{payload}".encode(), hashlib.sha256).digest()
    return f"{header}.{payload}.{_b64(firma)}"


def verificar_token(token: str, secret_key: str) -> str | None:
    """Devuelve el id del usuario si la firma es valida y el token no expiro; si no, None."""
    try:
        header, payload, firma = token.split(".")
        esperada = hmac.new(secret_key.encode(), f"{header}.{payload}".encode(), hashlib.sha256).digest()
        if not hmac.compare_digest(esperada, _desde_b64(firma)):
            return None
        if json.loads(_desde_b64(header)).get("alg") != "HS256":
            return None
        datos = json.loads(_desde_b64(payload))
    except (ValueError, TypeError):
        return None
    if not isinstance(datos.get("exp"), int) or datos["exp"] < time.time():
        return None
    return datos.get("sub") if isinstance(datos.get("sub"), str) else None
