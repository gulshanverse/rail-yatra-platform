# app/intelligence/metadata.py
import base64
from app.intelligence.interfaces import IMetadataManager


class MetadataManager(IMetadataManager):
    def __init__(self, key: str = "RailYatraSecureKey32BytesLong12"):
        self.key = key.encode("utf-8")

    def encrypt_pii(self, plaintext: str) -> str:
        if not plaintext:
            return ""
        b_val = plaintext.encode("utf-8")
        xor_val = bytes(
            b_val[i] ^ self.key[i % len(self.key)] for i in range(len(b_val))
        )
        return base64.b64encode(xor_val).decode("utf-8")

    def decrypt_pii(self, ciphertext: str) -> str:
        if not ciphertext:
            return ""
        try:
            xor_val = base64.b64decode(ciphertext.encode("utf-8"))
            b_val = bytes(
                xor_val[i] ^ self.key[i % len(self.key)] for i in range(len(xor_val))
            )
            return b_val.decode("utf-8")
        except Exception:
            return ciphertext
