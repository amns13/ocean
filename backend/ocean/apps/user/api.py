from django.contrib.auth import authenticate, login, logout
from django.http import HttpRequest
from ninja import Router, Status
from ninja.errors import AuthenticationError

from ocean.apps.user.schemas import UserDetailsSchema, UserLoginSchemaIn

router = Router()


@router.post("/login/", response=UserDetailsSchema, url_name="login")
def login_user(request: HttpRequest, data: UserLoginSchemaIn):
    if request.user.is_authenticated:
        return request.user

    user = authenticate(username=data.username, password=data.password)
    if user:
        login(request, user)
        return user
    else:
        raise AuthenticationError(message="Invalid username or password.")


@router.post("/logout/", response={204: None}, url_name="logout")
def logout_user(request: HttpRequest):
    logout(request)
    return Status(204, None)
