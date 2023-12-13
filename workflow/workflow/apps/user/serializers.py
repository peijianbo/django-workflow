from django.contrib.auth.models import Group
from rest_framework import serializers
from rest_framework.serializers import ModelSerializer

from .models import *


__all__ = ['UserSerializer', 'MenuSerializer', 'RoleSerializer']


class UserSerializer(ModelSerializer):

    class Meta:
        model = User
        fields = ('id', 'username', 'email', 'date_joined')


class RoleSerializer(ModelSerializer):

    class Meta:
        model = Group
        fields = ('id', 'name')


class MenuTinySerializer(ModelSerializer):

    class Meta:
        model = Menu
        fields = ('id', 'name')


class MenuSerializer(ModelSerializer):
    parent_id = serializers.IntegerField(allow_null=True, required=False, label='父级菜单ID')
    parent = MenuTinySerializer(read_only=True, label='父级菜单')

    class Meta:
        model = Menu
        fields = '__all__'
