"""Хэширование и сверка паролей через bcrypt."""
import bcrypt


class PasswordHasher:
    def hash(self, plaintext: str) -> str:
        return bcrypt.hashpw(plaintext.encode(), bcrypt.gensalt()).decode()

    def verify(self, plaintext: str, hashed: str) -> bool:
        return bcrypt.checkpw(plaintext.encode(), hashed.encode())
