from rest_framework import viewsets, mixins, permissions, serializers
from django_filters.rest_framework import DjangoFilterBackend
from datetime import datetime

from titles.models import Title, Category, Genre
from .serializers import (
    TitleSerializer, CategorySerializer, GenreSerializer)
# from .permissions import


class TitleViewSet(viewsets.ModelViewSet):
    queryset = Title.objects.all()
    serializer_class = TitleSerializer
#    permission_classes = (,)
    filter_backends = [DjangoFilterBackend,]
    filterset_fields = ['category__slug', 'genre__slug', 'name', 'year']

    def perform_create(self, serializer):
        """Создание нового произведения с проверкой года выпуска."""
        year = self.request.data.get('year')
        current_year = datetime.now().year
        if year and int(year) > current_year:
            raise serializers.ValidationError(
                {'year': 'Год не может быть больше текущего.'}
            )
        serializer.save()


class CategoryViewSet(
    mixins.ListModelMixin,
    mixins.CreateModelMixin,
    mixins.DestroyModelMixin,
    viewsets.GenericViewSet
):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    lookup_field = 'slug'
    filter_backends = (DjangoFilterBackend,)
    search_fields = ('name',)
#    permission_classes = (,)


class GenreViewSet(viewsets.ModelViewSet):
    queryset = Genre.objects.all()
    serializer_class = GenreSerializer
    lookup_field = 'slug'
    filter_backends = (DjangoFilterBackend,)
    search_fields = ('name')
#    permission_classes = (,)
