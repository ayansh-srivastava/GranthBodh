from fastapi import HTTPException

from sqlalchemy.orm import Session

from datetime import timedelta

from app.modules.users.models import User
from app.core.security import hash_password, verify_password
from app.core.jwt_utitls import create_access_token, create_refresh_token
from app.core.config import settings
from app.modules.users.schemas import UserCreate, UserLogin, TokenResponse

class UserService:
    @staticmethod
    def get_user_by_email(db: Session, email: str):
        return db.query(User).filter(User.email == email).first()

    @staticmethod
    def sign_up(db: Session, user_in: UserCreate):
        try:
            existing = db.query(User).filter(User.email == user_in.email).first()
            if existing:
                raise HTTPException(400, "Email already registered")

            user = User(
                email=user_in.email,
                password=hash_password(user_in.password)
            )
            db.add(user)
            db.commit()
            db.refresh(user)

            access = create_access_token(
                {"sub": str(user.id)},
                timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
            )
            refresh = create_refresh_token(
                {"sub": str(user.id)},
                timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
            )

            return {"access_token": access, "refresh_token": refresh}
        except HTTPException as e:
            db.rollback()
            raise e
        except Exception as e:
            db.rollback()
            raise HTTPException(500, f"Error during sign up: {str(e)}")

    @staticmethod
    def login(db: Session, user_data: UserLogin):

        try:
            user = db.query(User).filter(User.email == user_data.email).first()

            if not user or not verify_password(user_data.password, user.password):
                raise HTTPException(401, "Invalid credentials")

            access = create_access_token(
                {"sub": str(user.id)},
                timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
            )
            refresh = create_refresh_token(
                {"sub": str(user.id)},
                timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
            )

            return {"access_token": access, "refresh_token": refresh}
        except HTTPException as e:
            raise e
        except Exception as e:
            raise HTTPException(500, f"Error during login: {str(e)}")
