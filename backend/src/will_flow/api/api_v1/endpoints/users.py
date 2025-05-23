from fastapi import APIRouter, Depends, HTTPException

from will_flow.models.user import User, UserCreate
from will_flow.services.user_service import UserService

router = APIRouter()
user_service = UserService()


@router.post("/", response_model=User)
async def create_user(user: UserCreate):
    """
    Create a new user or update login timestamp for existing user.
    """
    return await user_service.create_user(user)


@router.get("/{email}", response_model=User)
async def get_user(email: str):
    """
    Get user by email.
    """
    user = await user_service.get_user_by_email(email)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user 