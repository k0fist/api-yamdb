import django_filters

from titles.models import Title


class TitleFilter(django_filters.FilterSet):
    genre = django_filters.CharFilter(
        field_name='genre__slug',
        method='filter_genre'
    )
    category = django_filters.CharFilter(
        field_name='category__slug',
        method='filter_category'
    )

    def filter_genre(self, titles, name, value):
        """Фильтрация по slug жанра"""
        return titles.filter(genre__slug=value)

    def filter_category(self, titles, name, value):
        """Фильтрация по slug категории"""
        return titles.filter(category__slug=value)

    class Meta:
        model = Title
        fields = ['genre', 'category', 'name', 'year']
