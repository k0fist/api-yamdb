from rest_framework import viewsets, mixins, serializers, status, filters
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.filters import SearchFilter
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.pagination import LimitOffsetPagination
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.decorators import action

from datetime import datetime
from django_filters.rest_framework import DjangoFilterBackend
from django.contrib.auth import get_user_model
from django.core.mail import send_mail
from django.core.validators import validate_email
from django.core.exceptions import ValidationError
from django.shortcuts import get_object_or_404
import uuid
import re

from titles.models import Title, Category, Genre
from reviews.models import Review
from .serializers import (
    TitleSerializer, CategorySerializer, GenreSerializer,
    UserSerializer, ReviewSerializer, CommentSerializer
)
from .permissions import AdminPermission, IsAuthorOrAdminOrModerator
from .filters import TitleFilter


User = get_user_model()

REQUIRED_FIELD_PHRASE = 'Это поле обязательно для заполнения.'


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
        permission_classes=(IsAuthenticated,)
    )
    def me(self, request, *args, **kwargs):
        user = request.user
        if request.method == 'GET':
            serializer = UserSerializer(user)
            return Response(serializer.data)
        elif request.method == 'PATCH':
            data = request.data.copy()
            data.pop('role', None)
            serializer = UserSerializer(user, data=data, partial=True)
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data)
            return Response(
                serializer.errors,
                status=status.HTTP_400_BAD_REQUEST
            )


def validate_username(username):
    errors = {}
    if not username:
        errors['username'] = [REQUIRED_FIELD_PHRASE]
    elif username == 'me':
        errors['username'] = ['Введите корректный username']
    elif len(username) > 150:
        errors.setdefault(
            'username', []
        ).append('Username не должен превышать 150 символов.')
    elif not re.fullmatch(r'^[\w.@+-]+\Z', username):
        errors['username'] = ['Username имеет недопустимые символы']
    return errors


class SignupView(APIView):
    """Регистрация нового пользовователя."""

    def post(self, request):
        email = request.data.get('email', '').strip()
        username = request.data.get('username', '').strip()

        errors = {}
        if User.objects.filter(email=email).exists():
            if not User.objects.filter(username=username).exists():
                errors['email'] = ['Этот email уже занят.']
        elif User.objects.filter(username=username).exists():
            if not User.objects.filter(email=email).exists():
                errors['username'] = ['Этот username уже занят.']
        if not email:
            errors['email'] = [REQUIRED_FIELD_PHRASE]
        else:
            try:
                validate_email(email)
            except ValidationError:
                errors['email'] = ['Введите корректный email адрес.']
            if len(email) > 254:
                errors.setdefault(
                    'email', []
                ).append('Email не должен превышать 254 символа.')
        errors.update(validate_username(username))

        if errors:
            return Response(errors, status=status.HTTP_400_BAD_REQUEST)

        user, created = User.objects.get_or_create(
            username=username,
            defaults={'email': email}
        )
        confirmation_code = str(uuid.uuid4())[:6]
        user.confirmation_code = confirmation_code
        user.save()
        send_mail(
            'Код подтверждения',
            f'Ваш код подтверждения для получения токена: {confirmation_code},'
            ' никому не сообщайте его!',
            from_email='sirotkin.201515@gmail.com',
            recipient_list=[email]
        )
        return Response(
            {
                'email': f'{email}',
                'username': f'{username}',
            },
            status=status.HTTP_200_OK
        )


class TokenView(APIView):
    """Формирование токена при корретный данных."""

    def post(self, request):
        username = request.data.get('username')
        confirmation_code = request.data.get('confirmation_code')
        errors = {}
        errors.update(validate_username(username))
        if not errors:
            try:
                user = User.objects.get(username=username)
                if not confirmation_code:
                    errors['confirmation_code'] = [REQUIRED_FIELD_PHRASE]
                if user.confirmation_code != confirmation_code:
                    errors['confirmation_code'] = ['Не верный код.']
            except User.DoesNotExist:
                return Response(
                    {
                        'username': 'Пользователь не найден'
                    },
                    status=status.HTTP_404_NOT_FOUND
                )
        if errors:
            return Response(errors, status=status.HTTP_400_BAD_REQUEST)
        refresh = RefreshToken.for_user(user)
        user.confirmation_code = ''
        user.save()
        return Response({
            'access': str(refresh.access_token),
            'refresh': str(refresh)
        }, status=status.HTTP_200_OK)


class TitleViewSet(viewsets.ModelViewSet):
    queryset = Title.objects.select_related(
        'category'
    ).prefetch_related('genre').all()
    serializer_class = TitleSerializer
    pagination_class = LimitOffsetPagination
    filter_backends = (DjangoFilterBackend, SearchFilter)
    filterset_class = TitleFilter
    search_fields = ['name']
    permission_classes = [AllowAny]

    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            return [AllowAny()]
        return [AdminPermission()]

    def update(self, request, *args, **kwargs):
        return Response(
            {'detail': 'Метод PUT не поддерживается.'},
            status=status.HTTP_405_METHOD_NOT_ALLOWED
        )

    def partial_update(self, request, *args, **kwargs):
        """Обработка PATCH-запроса с валидацией длины поля `name`."""
        instance = self.get_object()
        serializer = self.get_serializer(
            instance,
            data=request.data,
            partial=True
        )
        if serializer.is_valid():
            name = request.data.get('name', '')
            if len(name) > 256:
                return Response(
                    {'detail': 'Название произведения'
                     'не может быть длиннее 256 символов.'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

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
    queryset = Category.objects.all().order_by('name')
    serializer_class = CategorySerializer
    pagination_class = LimitOffsetPagination
    filter_backends = (DjangoFilterBackend, SearchFilter)
    search_fields = ('name',)
    lookup_field = 'slug'

    # Настройка разрешений
    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            return [AllowAny()]
        return [AdminPermission()]

    def __str__(self):
        return self.name


class GenreViewSet(
    mixins.ListModelMixin,
    mixins.CreateModelMixin,
    mixins.DestroyModelMixin,
    viewsets.GenericViewSet
):
    queryset = Genre.objects.all()
    serializer_class = GenreSerializer
    pagination_class = LimitOffsetPagination
    filter_backends = (DjangoFilterBackend, SearchFilter)
    search_fields = ('name', )
    lookup_field = 'slug'

    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            return [AllowAny()]
        return [AdminPermission()]


class ReviewViewSet(viewsets.ModelViewSet):
    serializer_class = ReviewSerializer

    def get_permissions(self):
        """Определяет разрешения в зависимости от действия."""
        if self.action in ['list', 'retrieve']:
            return [AllowAny()]
        elif self.action == 'create':
            return [IsAuthenticated()]
        elif self.action in ['update', 'partial_update', 'destroy']:
            return [IsAuthorOrAdminOrModerator()]
        return []

    def update(self, request, *args, **kwargs):
        return Response(
            {"detail": "Метод PUT не поддерживается."},
            status=status.HTTP_405_METHOD_NOT_ALLOWED
        )

    def partial_update(self, request, *args, **kwargs):
        """Обработка PATCH-запроса с дополнительной валидацией."""
        instance = self.get_object()
        serializer = self.get_serializer(
            instance,
            data=request.data,
            partial=True
        )

        if serializer.is_valid():
            score = request.data.get('score')
            try:
                score = float(score)
            except (ValueError, TypeError):
                return Response(
                    {'detail': 'Оценка должна быть числом.'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            if score < 1 or score > 10:
                return Response(
                    {'detail': 'Оценка должна быть от 1 до 10.'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            serializer.save()
            return Response(serializer.data)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def get_queryset(self):
        title = get_object_or_404(Title, id=self.kwargs['title_id'])
        return title.reviews.all().order_by('-pub_date')

    def perform_create(self, serializer):
        title = get_object_or_404(Title, id=self.kwargs['title_id'])
        serializer.save(author=self.request.user, title=title)


class CommentViewSet(viewsets.ModelViewSet):
    serializer_class = CommentSerializer

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
        review = get_object_or_404(Review, id=self.kwargs['review_id'])
        return review.comments.all()

    def perform_create(self, serializer):
        """Добавить новый комментарий к отзыву."""
        review = get_object_or_404(Review, id=self.kwargs['review_id'])
        serializer.save(author=self.request.user, review=review)

    def post(self, request, *args, **kwargs):
        """Обработка POST-запросов для детализированного эндпоинта."""
        if not request.user.is_authenticated:
            return Response(
                {'detail': 'Вы не авторизованы.'},
                status=status.HTTP_401_UNAUTHORIZED
            )
        return Response(
            {'detail': 'Метод POST не поддерживается для этого эндпоинта.'},
            status=status.HTTP_405_METHOD_NOT_ALLOWED
        )

    def update(self, request, *args, **kwargs):
        return Response(
            {'detail': 'Метод PUT не поддерживается.'},
            status=status.HTTP_405_METHOD_NOT_ALLOWED
        )

    def partial_update(self, request, *args, **kwargs):
        """Обработка PATCH-запроса."""
        instance = self.get_object()
        serializer = self.get_serializer(
            instance,
            data=request.data,
            partial=True
        )
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        return Response(serializer.data)
