from django.urls import path
from rest_framework.routers import DefaultRouter

from .views import *

router = DefaultRouter()
router.register('users', UserViewSet, 'users')
router.register('roles', RoleViewSet, 'roles')
router.register('menus', MenuViewSet, 'menus')

urlpatterns = [
    path(f'login/', ObtainAuthToken.as_view()),

]

urlpatterns += router.urls
