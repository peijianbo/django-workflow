from rest_framework.serializers import ModelSerializer
from rest_framework.settings import api_settings

from .models import *


__all__ = ['UserSerializer',]


class UserSerializer(ModelSerializer):

    class Meta:
        model = User
        fields = ('id', 'username', 'email', 'date_joined')
