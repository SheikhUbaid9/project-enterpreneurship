import base64
import os

from cryptography.hazmat.primitives.ciphers.aead import AESGCM


class TokenCipher:
    """
    AES-256-GCM helper for storing provider tokens at rest.
    """

    def __init__(self, key: str):
        raw = base64.urlsafe_b64decode(key)
        if len(raw) != 32:
            raise ValueError("TOKEN_ENCRYPTION_KEY must decode to 32 bytes (AES-256).")
        self._key = raw

    def encrypt(self, plaintext: str) -> str:
        nonce = os.urandom(12)
        cipher = AESGCM(self._key)
        ciphertext = cipher.encrypt(nonce, plaintext.encode("utf-8"), None)
        token = nonce + ciphertext
        return base64.urlsafe_b64encode(token).decode("utf-8")

    def decrypt(self, encrypted_text: str) -> str:
        raw = base64.urlsafe_b64decode(encrypted_text)
        nonce = raw[:12]
        ciphertext = raw[12:]
        cipher = AESGCM(self._key)
        plaintext = cipher.decrypt(nonce, ciphertext, None)
        return plaintext.decode("utf-8")
