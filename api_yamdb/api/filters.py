import django_filters

from reviews.models import Title


class TitleFilter(django_filters.FilterSet):
    name = django_filters.Filter(
        field_name='name',
        lookup_expr='contains'
    )
    year = django_filters.Filter(
        field_name='year',
        lookup_expr='contains'
    )
    genre = django_filters.Filter(
        field_name='genre__slug',
        lookup_expr='contains'
    )
    category = django_filters.Filter(
        field_name='category__slug',
        lookup_expr='contains'
    )

    class Meta:
        model = Title
        fields = ['name', 'year', 'genre', 'category']
