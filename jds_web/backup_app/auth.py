from rest_framework.authentication import TokenAuthentication as BaseTokenAuth
from rest_framework.exceptions import AuthenticationFailed


class TokenAuth(BaseTokenAuth):
    keyword = "Bearer"

    def authenticate_credentials(self, key):
        from .models import Client
        try:
            client = Client.objects.get(api_token=key, is_active=True)
        except Client.DoesNotExist:
            raise AuthenticationFailed("Ungültiger oder deaktivierter API-Token")
        return (client, None)
