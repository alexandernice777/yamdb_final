import re

from rest_framework import serializers
from rest_framework import filters, mixins, viewsets
from rest_framework.pagination import LimitOffsetPagination

from api_yamdb.settings import REGEXP_USERNAME
from .permissions import IsAdminOrReadOnly


class CustomModelMixin(mixins.ListModelMixin,
                       mixins.CreateModelMixin,
                       mixins.DestroyModelMixin,
                       viewsets.GenericViewSet):
    permission_classes = [IsAdminOrReadOnly]
    pagination_class = LimitOffsetPagination
    filter_backends = [filters.SearchFilter]
    search_fields = ['name']
    lookup_field = 'slug'


class ValidateUsernameSerializerMixin():
    def validate_username(self, value):
        if not re.match(REGEXP_USERNAME, value):
            raise serializers.ValidationError(
                'Поле "username" содержит запрещенные символы')
        return value
