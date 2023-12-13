from django.contrib.auth.models import Group
from rest_framework import status, mixins
from rest_framework.authtoken.models import Token
from rest_framework.authtoken.views import ObtainAuthToken as ObtainAuthToken_
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet, GenericViewSet

from .models import *
from .serializers import *


__all__ = ['ObtainAuthToken', 'UserViewSet', 'MenuViewSet', 'RoleViewSet']


class ObtainAuthToken(ObtainAuthToken_):
    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data['user']
        token, created = Token.objects.get_or_create(user=user)
        return Response({'id': user.id, 'username': user.username, 'token': token.key})


class UserViewSet(ModelViewSet):
    filter_fields = ()
    search_fields = filter_fields

    queryset = User.objects.all()
    serializer_class = UserSerializer


class RoleViewSet(mixins.ListModelMixin,
                  GenericViewSet):
    filter_fields = ()
    search_fields = filter_fields

    queryset = Group.objects.all()
    serializer_class = RoleSerializer


class MenuViewSet(ModelViewSet):
    ordering_fields = ('name', 'code')
    filter_fields = ()
    search_fields = filter_fields

    queryset = Menu.objects.all()
    serializer_class = MenuSerializer

    @action(methods=['get'], detail=False, url_path='menu_tree', name='menu_tree')
    def menu_tree(self, request, **kwargs):
        """菜单树"""
        roles = request.user.groups.all()
        menus_queryset = self.filter_queryset(queryset=self.queryset).filter(roles__in=roles)
        menus = self.serializer_class(menus_queryset, many=True).data
        tree = [menu for menu in menus if menu['parent_id'] is None]
        for menu in menus:
            menu['children'] = [m for m in menus if menu['id'] == m['parent_id']]
        return Response(data=tree, status=status.HTTP_200_OK)
