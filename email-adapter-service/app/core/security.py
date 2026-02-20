from shared.security import TokenCipher

from app.core.config import get_settings


settings = get_settings()
token_cipher = TokenCipher(settings.token_encryption_key)


def encrypt_provider_token(token: str) -> str:
    return token_cipher.encrypt(token)


def decrypt_provider_token(token: str) -> str:
    return token_cipher.decrypt(token)
