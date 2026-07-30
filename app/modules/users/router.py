from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from datetime import timedelta

from app.core.db import get_db
from app.modules.users.schemas import UserCreate, UserLogin, TokenResponse
from app.modules.users.service import UserService

router = APIRouter(prefix="/users", tags=["Users"])



@router.get("/")
def health_check():
    return {"status": "ok", "message": f"Welcome to PROJECT_NAME"}

@router.post("/signup", response_model=TokenResponse)
def signup(user_data: UserCreate, db: Session = Depends(get_db)):
    res = UserService.sign_up(db, user_in=user_data)
    return res


@router.post("/login", response_model=TokenResponse)
def login(user_data: UserLogin, db: Session = Depends(get_db)):
    res = UserService.login(db, user_data=user_data)
    return res
