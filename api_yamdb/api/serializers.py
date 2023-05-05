from django.shortcuts import get_object_or_404
from rest_framework import serializers
from rest_framework.relations import SlugRelatedField

from api_yamdb.settings import (FORBIDDEN_USERNAME,
                                MINSCORE, MAXSCORE)
from .mixins import ValidateUsernameSerializerMixin
from reviews.models import Category, Comment, Genre, Review, Title
from users.models import CustomUser


class CategorySerializer(serializers.ModelSerializer):
    """Сериализатор модели Category."""

    class Meta:
        exclude = ['id']
        model = Category


class GenreSerializer(serializers.ModelSerializer):
    """Сериализатор модели Genre."""

    class Meta:
        exclude = ['id']
        model = Genre


class OutputTitleSerializer(serializers.ModelSerializer):
    """Сериализатор модели Title для чтения данных."""

    category = CategorySerializer(read_only=True)
    genre = GenreSerializer(read_only=True, many=True)
    rating = serializers.IntegerField(read_only=True)

    class Meta:
        fields = '__all__'
        model = Title


class InputTitleSerializer(serializers.ModelSerializer):
    """Сериализатор модели Title для измнения данных."""

    category = serializers.SlugRelatedField(
        queryset=Category.objects.all(),
        slug_field='slug'
    )
    genre = serializers.SlugRelatedField(
        queryset=Genre.objects.all(),
        slug_field='slug',
        many=True
    )

    class Meta:
        fields = '__all__'
        model = Title


class ReviewSerializer(serializers.ModelSerializer):
    """Сериализатор модели Review."""

    title = SlugRelatedField(slug_field='name', read_only=True)
    author = SlugRelatedField(slug_field='username', read_only=True)

    def validate_score(self, value):
        if MINSCORE > value > MAXSCORE:
            raise serializers.ValidationError(
                'Допускается оценка только от 1 до 10!')
        return value

    def validate(self, data):
        request = self.context['request']
        author = request.user
        title_id = self.context.get('view').kwargs.get('title_id')
        title = get_object_or_404(Title, pk=title_id)
        if (request.method == 'POST'
           and Review.objects.filter(title=title, author=author).exists()):
            raise serializers.ValidationError('Вы уже оставляли свой отзыв!')
        return data

    class Meta:
        fields = '__all__'
        model = Review


class CommentSerializer(serializers.ModelSerializer):
    """Сериализатор модели Comment."""

    review = SlugRelatedField(slug_field='text', read_only=True)
    author = SlugRelatedField(slug_field='username', read_only=True)

    class Meta:
        fields = '__all__'
        model = Comment


class SignUpSerializer(serializers.ModelSerializer,
                       ValidateUsernameSerializerMixin):
    """Сериализатор регистрации пользователя."""

    class Meta:
        model = CustomUser
        fields = ('email', 'username')

    def validate(self, data):
        if data.get('username') == FORBIDDEN_USERNAME:
            raise serializers.ValidationError(
                f'Использовать имя {FORBIDDEN_USERNAME} '
                f'в качестве username запрещено')
        return data


class GetTokenSerializer(serializers.ModelSerializer,
                         ValidateUsernameSerializerMixin):
    """Сериализатор получения токена."""

    confirmation_code = serializers.CharField(source='password')
    username = serializers.CharField(validators=[])

    class Meta:
        model = CustomUser
        fields = ('username', 'confirmation_code')


class CustomUserSerializer(serializers.ModelSerializer,
                           ValidateUsernameSerializerMixin):
    """Сериализатор модели CustomUser."""

    class Meta:
        exclude = ['id', 'password', 'last_login', 'is_superuser',
                   'is_staff', 'is_active', 'date_joined',
                   'groups', 'user_permissions']
        model = CustomUser


class SelfUserSerializer(serializers.ModelSerializer,
                         ValidateUsernameSerializerMixin):
    """Сериализатор данных учётной записи."""

    class Meta:
        exclude = ['id']
        model = CustomUser
        read_only_fields = ['role']
