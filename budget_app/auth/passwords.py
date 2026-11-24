"""Password hashing with argon2id."""

from pwdlib import PasswordHash
from pwdlib.hashers.argon2 import Argon2Hasher


def hash_password(pw: str) -> str:
    """Return the argon2id hash of `pw`, salted, starting with `$argon2id$`."""
    return PasswordHash((Argon2Hasher(),)).hash(pw)


def verify_password(pw: str, hashed: str) -> bool:
    """Return True when `pw` matches the argon2id hash `hashed`."""
    return PasswordHash((Argon2Hasher(),)).verify(pw, hashed)
