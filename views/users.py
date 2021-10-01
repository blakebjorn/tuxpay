import datetime

import jwt
from fastapi import APIRouter
from pydantic import BaseModel, Field

from modules.config import get_app_secret
from modules.credentials import check_password_hash
from modules.helpers import JSONResponse
from modules.models import database, User

router = APIRouter(prefix='/api')


class AuthenticationModel(BaseModel):
    email: str = Field(None, title="User's email address")
    password: str = Field(None, title="User's password")
    remember: bool = Field(False, title="How long the login is valid for."
                                        " Generated token expires in 5 hours if false, or 14 days if true")


class AuthenticationResponse(BaseModel):
    token: str = Field(None, title="JWT Bearer Token",
                       example="eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9."
                               "eyJpZCI6MSwiZW1haWwiOiJ0ZXN0dXNlckBtZS5jb20iLCJ"
                               "uYW1lIjoiVGVzdCBVc2VyIiwiZXhwIjoxNzAwMDAwMDAwfQ."
                               "TcEE3JjltOULdfKKmIQvu19kRnaJrSRVCWb-TXTvJqA")


@router.post('/authenticate', response_model=AuthenticationResponse, tags=['authentication'])
async def authenticate(payload: AuthenticationModel):
    """
    Authenticates with the admin API with an email + password. Returns a JWT Bearer token
    """
    email = payload.email
    password = payload.password
    remember = payload.remember

    user = await database.fetch_one(User.select().where(User.c.email.ilike(email)))
    if user is not None and check_password_hash(password, user['password']):
        if remember:
            exp = datetime.datetime.now() + datetime.timedelta(days=14)
        else:
            exp = datetime.datetime.now() + datetime.timedelta(hours=5)

        token = jwt.encode({
            "id": user['id'],
            "email": user['email'],
            "name": user['name'],
            "exp": exp.timestamp()
        }, get_app_secret(), algorithm="HS256")

        return JSONResponse({"token": token})

    return JSONResponse({"error": "unauthorized"}, status_code=401)
