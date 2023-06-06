from rest_framework.viewsets import ModelViewSet

from .models import *
from .serializers import *


__all__ = ['UserViewSet']


class UserViewSet(ModelViewSet):
    filter_fields = ()
    search_fields = filter_fields

    queryset = User.objects.all()
    serializer_class = UserSerializer
