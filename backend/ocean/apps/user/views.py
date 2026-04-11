from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import AnonymousUser
from rest_framework import status
from rest_framework.exceptions import AuthenticationFailed
from rest_framework.response import Response
from rest_framework.views import APIView


class LoginView(APIView):
    def post(self, request):
        if self.request.user.is_authenticated:
            return Response(
                {
                    "uid": self.request.user.uid,
                    "email": self.request.user.email,
                    "username": self.request.user.username,
                },
                status=status.HTTP_200_OK,
            )

        try:
            username = request.data["username"]
            password = request.data["password"]
        except KeyError:
            raise AuthenticationFailed("Invalid username or password.")

        user = authenticate(username=username, password=password)
        if user:
            login(request, user)
            return Response(
                {"uid": user.uid, "email": user.email, "username": user.username}, status=status.HTTP_200_OK
            )
        else:
            raise AuthenticationFailed("Invalid username or password.")


class LogOutView(APIView):
    def post(self, request):
        logout(request)
        return Response(status=status.HTTP_204_NO_CONTENT)
