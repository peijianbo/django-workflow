from rest_framework.routers import DefaultRouter

from .views import *

router = DefaultRouter()
router.register('users', UserViewSet, 'users')

urlpatterns = [
]

urlpatterns += router.urls
