from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed
from django.conf import settings

class GlobalTokenAuthentication(BaseAuthentication):
    def authenticate(self, request):
        auth_header = request.META.get("HTTP_AUTHORIZATION")

        if not auth_header:
            raise AuthenticationFailed("No Authorization header provided")

        try:
            method, token = auth_header.strip().split(" ")
        except ValueError:
            raise AuthenticationFailed("Invalid Authorization header format")

        if method != "Token":
            raise AuthenticationFailed("Invalid token type")

        if token != settings.GLOBAL_API_TOKEN:
            raise AuthenticationFailed("Invalid API token")

        return (None, None)