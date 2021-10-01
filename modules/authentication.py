import base64
import itertools
from functools import wraps

import jwt
from starlette.authentication import AuthenticationBackend, AuthCredentials, BaseUser
from fastapi.requests import Request

from modules.config import get_app_secret
from modules.helpers import NOT_AUTHENTICATED


def to_short_jwt(payload: dict, algorithm="HS256"):
    """Truncate the front half of the token for more manageable URLs"""
    token = jwt.encode(payload, get_app_secret(), algorithm=algorithm)
    return token.split(".", maxsplit=1)[-1]


def from_short_jwt(token: str, algorithm="HS256"):
    """reconstruct a shortened JWT"""
    prefix = base64.b64encode(f'{{"typ":"JWT","alg":"{algorithm}"}}'.encode()).decode()
    return jwt.decode(prefix + "." + token, get_app_secret(), algorithms=[algorithm])


def requires_auth(func):
    @wraps(func)
    async def wrapper(*args, **kwargs):
        for arg in itertools.chain(args, kwargs.values()):
            if isinstance(arg, Request):
                if arg.user.is_authenticated():
                    return await func(*args, **kwargs)
                return NOT_AUTHENTICATED
        raise ValueError("No request object passed to decorated function")

    return wrapper


class ApiUser(BaseUser):
    @property
    def display_name(self) -> str:
        return self.email

    def __init__(self, **kwargs) -> None:
        self.id = kwargs.get("id")
        self.email = kwargs.get("email")

    def is_authenticated(self) -> bool:
        return self.id is not None


class TokenAuthBackend(AuthenticationBackend):
    async def authenticate(self, request):
        if "Authorization" in request.headers:
            if " " in request.headers["Authorization"]:
                scheme, token = request.headers["Authorization"].split(maxsplit=1)
                if scheme.lower() == 'bearer':
                    try:
                        payload = jwt.decode(token, get_app_secret(), algorithms=["HS256"])
                        return AuthCredentials(["admin"]), ApiUser(**payload)
                    except jwt.exceptions.InvalidTokenError:
                        pass
        return AuthCredentials([]), ApiUser()
