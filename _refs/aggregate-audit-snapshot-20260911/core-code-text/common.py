from __future__ import annotations

import base64
import hashlib
import json
from pathlib import Path
from typing import Any

from cryptography.hazmat.primitives import serialization
from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives.asymmetric.ed25519 import (
    Ed25519PrivateKey,
    Ed25519PublicKey,
)


def canonical(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":")).encode()


def digest(*parts: bytes) -> bytes:
    h = hashlib.sha256()
    for part in parts:
        h.update(len(part).to_bytes(8, "big"))
        h.update(part)
    return h.digest()


def hash_int(modulus: int, *parts: bytes, nonzero: bool = False) -> int:
    value = int.from_bytes(digest(*parts), "big") % modulus
    return value or int(nonzero)


def prf_int(seed: bytes, label: bytes, counter: int, modulus: int, *, nonzero: bool = False) -> int:
    return hash_int(modulus, seed, label, counter.to_bytes(8, "big"), nonzero=nonzero)


def b64(value: bytes) -> str:
    return base64.b64encode(value).decode("ascii")


def unb64(value: str) -> bytes:
    return base64.b64decode(value.encode("ascii"), validate=True)


def signing_key(seed: bytes, role: bytes) -> Ed25519PrivateKey:
    return Ed25519PrivateKey.from_private_bytes(digest(seed, role))


def private_bytes(key: Ed25519PrivateKey) -> str:
    return b64(
        key.private_bytes(
            serialization.Encoding.Raw,
            serialization.PrivateFormat.Raw,
            serialization.NoEncryption(),
        )
    )


def public_bytes(key: Ed25519PublicKey) -> str:
    return b64(key.public_bytes(serialization.Encoding.Raw, serialization.PublicFormat.Raw))


def sign(key_b64: str, value: Any) -> str:
    return b64(Ed25519PrivateKey.from_private_bytes(unb64(key_b64)).sign(canonical(value)))


def verify_signature(key_b64: str, value: Any, signature_b64: str) -> bool:
    try:
        Ed25519PublicKey.from_public_bytes(unb64(key_b64)).verify(unb64(signature_b64), canonical(value))
        return True
    except (InvalidSignature, ValueError, TypeError):
        return False


def dump_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))
