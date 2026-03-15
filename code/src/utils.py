import os
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.hkdf import HKDF
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

def sha256(data: bytes) -> bytes:
    """Compute SHA-256 hash of data."""
    digest = hashes.Hash(hashes.SHA256())
    digest.update(data)
    return digest.finalize()

def hkdf_derive(ikm: bytes, salt: bytes, info: bytes = b"", length: int = 32) -> bytes:
    """Derive a key using HKDF-SHA256."""
    hkdf = HKDF(
        algorithm=hashes.SHA256(),
        length=length,
        salt=salt,
        info=info,
    )
    return hkdf.derive(ikm)

def aes_gcm_encrypt(key: bytes, plaintext: bytes, associated_data: bytes = None, nonce: bytes = None) -> tuple[bytes, bytes, bytes]:
    """
    Encrypt data using AES-GCM.
    Returns (nonce, ciphertext, tag).
    """
    aesgcm = AESGCM(key)
    if nonce is None:
        nonce = os.urandom(12)
    ciphertext_with_tag = aesgcm.encrypt(nonce, plaintext, associated_data)
                                                    
    tag = ciphertext_with_tag[-16:]
    ciphertext = ciphertext_with_tag[:-16]
    return nonce, ciphertext, tag

def aes_gcm_decrypt(key: bytes, nonce: bytes, ciphertext: bytes, tag: bytes, associated_data: bytes = None) -> bytes:
    """
    Decrypt data using AES-GCM.
    Raises InvalidTag if decryption fails.
    """
    aesgcm = AESGCM(key)
                                                                            
    data = ciphertext + tag
    return aesgcm.decrypt(nonce, data, associated_data)
