import os
import jwt
from datetime import datetime, timedelta
from rest_framework import authentication, exceptions
from .models import User

class JWTAuthentication(authentication.BaseAuthentication):
    """Custom JWT authentication for DRF"""
    def authenticate(self, request):
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            return None

        token = auth_header.split(' ')[1]
        secret_key = os.getenv('SECRET_KEY')

        try:
            payload = jwt.decode(token, secret_key, algorithms=['HS256'])
        except jwt.ExpiredSignatureError:
            raise exceptions.AuthenticationFailed('Token has expired')
        except jwt.InvalidTokenError:
            raise exceptions.AuthenticationFailed('Invalid token')

        try:
            user = User.objects.get(id=payload['user_id'], is_active=True)
        except User.DoesNotExist:
            raise exceptions.AuthenticationFailed('User not found')

        return (user, token)