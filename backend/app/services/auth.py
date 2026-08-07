from uuid import uuid4

from sqlalchemy.orm import Session

from app.Core.security import hash_password, verify_password
from app.db.models import User


class AuthServiceError(RuntimeError):
    pass


class InvalidCredentialsError(AuthServiceError):
    pass


class EmailAlreadyRegisteredError(AuthServiceError):
    pass


class AuthService:
    def register(self, db: Session, full_name: str, email: str, password: str) -> User:
        normalized_email = email.strip().lower()
        if db.query(User).filter(User.email == normalized_email).first() is not None:
            raise EmailAlreadyRegisteredError("El correo ya se encuentra registrado")

        user = User(
            id=str(uuid4()),
            full_name=full_name,
            email=normalized_email,
            hashed_password=hash_password(password),
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        return user

    def authenticate(self, db: Session, email: str, password: str) -> User:
        normalized_email = email.strip().lower()
        user = db.query(User).filter(User.email == normalized_email).first()
        if user is None or not verify_password(password, user.hashed_password):
            raise InvalidCredentialsError(
                "Las credenciales no se encuentran en la base de datos de usuarios registrados"
            )
        return user
