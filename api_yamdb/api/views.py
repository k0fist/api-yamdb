from rest_framework import viewsets, mixins, serializers, status, filters
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.filters import SearchFilter
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.pagination import LimitOffsetPagination
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.decorators import action, api_view
from django.conf import settings
from datetime import datetime
from django_filters.rest_framework import DjangoFilterBackend
from django.contrib.auth import get_user_model
from django.core.mail import send_mail
from django.core.exceptions import ValidationError
from django.shortcuts import get_object_or_404
import uuid
import re
import random
from titles.models import Title, Category, Genre
from reviews.models import Review
from .serializers import (
    TitleSerializer, CategorySerializer, GenreSerializer,
    UserSerializer, ReviewSerializer, CommentSerializer, TokenSerializer
)
from .permissions import AdminPermission, IsAuthorOrAdminOrModerator
from .filters import TitleFilter
from titles.validators import validate_username, REQUIRED_FIELD_PHRASE, USER_ME


User = get_user_model()


class UserView(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = (AdminPermission,)
    pagination_class = LimitOffsetPagination
    filter_backends = (filters.SearchFilter,)
    search_fields = ('username',)
    lookup_field = 'username'
    http_method_names = ['get', 'post', 'patch', 'delete']

    @action(
        detail=False,
        methods=['get', 'patch'],
        url_path=USER_ME,
        url_name=USER_ME,
        permission_classes=(IsAuthenticated,)
    )
    def me(self, request, *args, **kwargs):
        user = request.user
        # import pdb; pdb.set_trace()
        if request.method == 'GET':
            return Response(UserSerializer(user).data)
        else:
            serializer = UserSerializer(user, data=request.data, partial=True)
            serializer.is_valid(raise_exception=True)
            serializer.save(role=user.role)
            return Response(serializer.data)


@api_view(['POST'])
def signup(request):
    """Регистрация нового пользователя."""
    serializer = UserSerializer(data=request.data)

    if serializer.is_valid():
        email = serializer.validated_data['email']
        username = serializer.validated_data['username']
        user, created = User.objects.get_or_create(username=username, defaults={'email': email})

        confirmation_code = ''.join(
            random.choices(
                settings.PIN_CODE_CHARACTERS,
                k=settings.PIN_CODE_LENGTH
            ))
        user.confirmation_code = confirmation_code
        user.save()

        send_mail(
            'Код подтверждения',
            f'Ваш код подтверждения для получения токена: {confirmation_code},'
            ' никому не сообщайте его!',
            from_email=settings.FROM_EMAIL,
            recipient_list=[email]
        )

        return Response(
            {
                'email': email,
                'username': username,
            },
            status=status.HTTP_200_OK
        )
    else:
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
def token(request):
    """Формирование токена при корректных данных."""
    serializer = TokenSerializer(data=request.data)

    if serializer.is_valid():
        # Генерация токенов, если данные валидны
        username = serializer.validated_data.get('username')
        # Получаем пользователя, если он не найден - возвращаем 404
        user = get_object_or_404(User, username=username)

        # Проверка кода подтверждения (не обязательно, если она уже в сериализаторе)
        confirmation_code = serializer.validated_data.get('confirmation_code')
        if user.confirmation_code != confirmation_code:
            return Response(
                {'confirmation_code': 'Неверный код подтверждения.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Генерация refresh токенов
        refresh = RefreshToken.for_user(user)
        data = {
            'access': str(refresh.access_token),
            'refresh': str(refresh)
        }
        return Response(data, status=status.HTTP_200_OK)
    else:
        # Если данные невалидны, возвращаем ошибку с деталями
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class TitleViewSet(viewsets.ModelViewSet):
    queryset = Title.objects.select_related(
        'category'
    ).prefetch_related('genre').all()
    pagination_class = LimitOffsetPagination
    filter_backends = (DjangoFilterBackend, SearchFilter)
    filterset_class = TitleFilter
    search_fields = ['name']
    permission_classes = [AllowAny]
    http_method_names = ['get', 'post', 'patch', 'delete']

    def get_serializer_class(self):
        if self.action in ['create', 'update', 'partial_update']:
            return TitleCreateUpdateSerializer
        return TitleReadSerializer

    def get_permissions(self):
        self.permission_classes = [AdminPermission] if self.action not in ['list', 'retrieve'] else [AllowAny]
        return super().get_permissions()


class BaseViewSet_Category_Genre(
    mixins.ListModelMixin,
    mixins.CreateModelMixin,
    mixins.DestroyModelMixin,
    viewsets.GenericViewSet
):
    pagination_class = LimitOffsetPagination
    filter_backends = (DjangoFilterBackend, SearchFilter)
    search_fields = ('name',)
    lookup_field = 'slug'
    permission_classes = [AllowAny]

    def get_permissions(self):
        self.permission_classes = [AdminPermission] if self.action not in ['list', 'retrieve'] else [AllowAny]
        return super().get_permissions()

    def __str__(self):
        return self.name


class CategoryViewSet(
    BaseViewSet_Category_Genre
):
    queryset = Category.objects.all().order_by('name')
    serializer_class = CategorySerializer


class GenreViewSet(
    BaseViewSet_Category_Genre
):
    queryset = Genre.objects.all()
    serializer_class = GenreSerializer


def get_field(model, id):
    return get_object_or_404(model, id=id)


class ReviewViewSet(viewsets.ModelViewSet):
    serializer_class = ReviewSerializer
    http_method_names = ['get', 'post', 'patch', 'delete']
    
    def get_permissions(self):
        """Определяет разрешения в зависимости от действия."""
        if self.action in ['list', 'retrieve']:
            return [AllowAny()]
        elif self.action == 'create':
            return [IsAuthenticated()]
        elif self.action in ['update', 'partial_update', 'destroy']:
            return [IsAuthorOrAdminOrModerator()]
        return []

    # def get_title(self):
    #     return get_object_or_404(Title, id=self.kwargs['title_id'])
    
    def get_queryset(self):
        return get_field(
            Title, self.kwargs['title_id']
        ).reviews.all().order_by('-pub_date')

    def perform_create(self, serializer):
        serializer.save(
            author=self.request.user,
            title=get_field(Title, self.kwargs['title_id'])
        )


class CommentViewSet(viewsets.ModelViewSet):
    serializer_class = CommentSerializer
    http_method_names = ['get', 'post', 'patch', 'delete']

    def get_permissions(self):
        """Определяет разрешения в зависимости от действия."""
        if self.action in ['list', 'retrieve']:
            return [AllowAny()]
        elif self.action == 'create':
            return [IsAuthenticated()]
        elif self.action in ['update', 'partial_update', 'destroy']:
            return [IsAuthorOrAdminOrModerator()]
        return []

    def get_queryset(self):
        """Получить все комментарии к отзыву."""
        # review = get_object_or_404(Review, id=self.kwargs['review_id'])
        return get_field(Review, self.kwargs['review_id']).comments.all()

    def perform_create(self, serializer):
        """Добавить новый комментарий к отзыву."""
        # review = get_object_or_404(Review, id=self.kwargs['review_id'])
        serializer.save(
            author=self.request.user,
            review=get_field(Review, self.kwargs['review_id'])
        )

    # def post(self, request, *args, **kwargs):
    #     """Обработка POST-запросов для детализированного эндпоинта."""
    #     if not request.user.is_authenticated:
    #         return Response(
    #             {'detail': 'Вы не авторизованы.'},
    #             status=status.HTTP_401_UNAUTHORIZED
    #         )
    #     return Response(
    #         {'detail': 'Метод POST не поддерживается для этого эндпоинта.'},
    #         status=status.HTTP_405_METHOD_NOT_ALLOWED
    #     )
