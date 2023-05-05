from django.contrib.auth.tokens import default_token_generator
from django.core.mail import EmailMessage
from django.db.models import Avg
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.pagination import LimitOffsetPagination
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken

from reviews.models import Category, Genre, Review, Title
from users.models import CustomUser
from .filters import TitleFilter
from .mixins import CustomModelMixin
from .permissions import (IsAdminOrReadOnly, IsAdminStaffOnly,
                          IsAuthorModeratorAdminOrReadOnly)
from .serializers import (CategorySerializer, CommentSerializer,
                          CustomUserSerializer, GenreSerializer,
                          GetTokenSerializer, InputTitleSerializer,
                          SelfUserSerializer, OutputTitleSerializer,
                          ReviewSerializer, SignUpSerializer)


class CategoryViewSet(CustomModelMixin):
    """Получение списка категорий. Доступ без токена на чтение."""

    queryset = Category.objects.all()
    serializer_class = CategorySerializer


class GenreViewSet(CustomModelMixin):
    """Получение списка жанров. Доступ без токена на чтение."""

    queryset = Genre.objects.all()
    serializer_class = GenreSerializer


class TitleViewSet(viewsets.ModelViewSet):
    """Получение списка произведений. Доступ без токена на чтение."""

    queryset = Title.objects.annotate(rating=Avg('reviews__score')).all()
    permission_classes = [IsAdminOrReadOnly]
    pagination_class = LimitOffsetPagination
    filter_backends = [DjangoFilterBackend]
    filterset_class = TitleFilter

    def get_serializer_class(self):
        if self.action in ('list', 'retrieve'):
            return OutputTitleSerializer
        return InputTitleSerializer


class ReviewViewSet(viewsets.ModelViewSet):
    """Получение списка отзывов. Доступ без токена на чтение."""

    serializer_class = ReviewSerializer
    permission_classes = [IsAuthorModeratorAdminOrReadOnly]
    pagination_class = LimitOffsetPagination

    def get_queryset(self):
        title = get_object_or_404(Title, id=self.kwargs.get('title_id'))
        return title.reviews.all()

    def perform_create(self, serializer):
        title = get_object_or_404(Title, id=self.kwargs.get('title_id'))
        serializer.save(author=self.request.user, title=title)


class CommentViewSet(viewsets.ModelViewSet):
    """Получение списка комментариев к отзывам. Доступ без токена на чтение."""

    serializer_class = CommentSerializer
    permission_classes = [IsAuthorModeratorAdminOrReadOnly]
    pagination_class = LimitOffsetPagination

    def get_queryset(self):
        review = get_object_or_404(Review, id=self.kwargs.get('review_id'))
        return review.comments.all()

    def perform_create(self, serializer):
        review = get_object_or_404(Review, id=self.kwargs.get('review_id'))
        serializer.save(author=self.request.user, review=review)


class SignUpView(APIView):
    """Регистрация нового пользователя."""

    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = SignUpSerializer(data=request.data)
        if CustomUser.objects.filter(**request.data.dict()).exists():
            return Response(serializer.initial_data, status=status.HTTP_200_OK)
        serializer.is_valid(raise_exception=True)
        user = CustomUser.objects.create(**serializer.validated_data)
        token = default_token_generator.make_token(user)
        email_data = {
            'subject': 'Код подтверждения',
            'email_to': user.email,
            'message': f'Ваш код подтверждения: {token}'
        }

        email = EmailMessage(
            subject=email_data['subject'],
            body=email_data['message'],
            to=[email_data['email_to']]
        )
        email.send()
        return Response(serializer.data, status=status.HTTP_200_OK)


class GetTokenView(APIView):
    """Получение токена для аунтификации пользователя."""

    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = GetTokenSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.data
        if not CustomUser.objects.filter(username=data['username']).exists():
            return Response('Такого пользователя не существует!',
                            status=status.HTTP_404_NOT_FOUND)
        user = CustomUser.objects.get(username=data['username'])
        if not default_token_generator.check_token(
                user, data['confirmation_code']):
            return Response('Неверный код подтверждения!',
                            status=status.HTTP_400_BAD_REQUEST)
        refresh = RefreshToken.for_user(user)
        return Response({'token': str(refresh.access_token)},
                        status=status.HTTP_200_OK)


class CustomUserViewSet(viewsets.ModelViewSet):
    """Получение списка пользователей. Доступ только с токеном."""

    queryset = CustomUser.objects.all()
    serializer_class = CustomUserSerializer
    http_method_names = ['get', 'post', 'patch', 'delete']
    permission_classes = [permissions.IsAuthenticated, IsAdminStaffOnly]
    pagination_class = LimitOffsetPagination
    filter_backends = [filters.SearchFilter]
    search_fields = ['username']
    lookup_field = 'username'

    @action(methods=['GET', 'PATCH'],
            detail=False,
            serializer_class=SelfUserSerializer,
            permission_classes=[permissions.IsAuthenticated])
    def me(self, request):
        if request.method == 'GET':
            serializer = self.get_serializer(request.user)
            return Response(serializer.data, status=status.HTTP_200_OK)
        serializer = self.get_serializer(
            request.user,
            data=request.data,
            partial=True
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_200_OK)
