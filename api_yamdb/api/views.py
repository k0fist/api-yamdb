import random

from django.conf import settings
from django.core.mail import send_mail
from django.contrib.auth import get_user_model
from django.db.models import Avg
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import viewsets, mixins, status, filters
from rest_framework.response import Response
from rest_framework.filters import SearchFilter
from rest_framework.permissions import IsAuthenticated
from rest_framework.pagination import LimitOffsetPagination
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.exceptions import ValidationError
from rest_framework.decorators import action, api_view, throttle_classes

from reviews.models import Review, Title, Category, Genre
from .serializers import (
    CategorySerializer, GenreSerializer,
    TitleCreateUpdateSerializer, TitleReadSerializer,
    UserSerializer, ReviewSerializer,
    CommentSerializer, TokenSerializer, SignUpSerializer
)
from .permissions import (
    AdminPermission, IsAuthorOrAdminOrModerator, ReadOnlyPermission
)
from .filters import TitleFilter


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
        url_path=settings.USER_ME,
        url_name=settings.USER_ME,
        permission_classes=(IsAuthenticated,)
    )
    def myself(self, request, *args, **kwargs):
        user = request.user
        if request.method == 'GET':
            return Response(UserSerializer(user).data)
        serializer = UserSerializer(user, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save(role=user.role)
        return Response(serializer.data)


@api_view(['POST'])
def signup(request):
    """Регистрация нового пользователя."""
    serializer = SignUpSerializer(data=request.data)

    serializer.is_valid(raise_exception=True)
    email = serializer.validated_data['email']
    username = serializer.validated_data['username']
    user = User.objects.filter(username=username).first()
    if user:
        if user.email != email:
            raise ValidationError(
                "Этот username уже зарегистрирован с другим email."
            )
    elif User.objects.filter(email=email).exists():
        raise ValidationError("Этот email уже зарегистрирован.")

    try:
        user, created = User.objects.get_or_create(
            username=username,
            defaults={'email': email}
        )
    except Exception as e:
        raise ValidationError(f"Ошибка при создании пользователя: {str(e)}")

    confirmation_code = ''.join(
        random.choices(
            settings.PIN_CODE_CHARACTERS,
            k=settings.PIN_CODE_LENGTH
        ))
    user.confirmation_code = confirmation_code
    user.save()

    send_mail(
        'Код подтверждения',
        f'Ваш код подтверждения для получения токена: {confirmation_code},',
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


@api_view(['POST'])
def token(request):
    """Формирование токена при корректных данных."""
    serializer = TokenSerializer(data=request.data)

    serializer.is_valid(raise_exception=True)
    username = serializer.validated_data.get('username')
    user = get_object_or_404(User, username=username)
    confirmation_code = serializer.validated_data.get('confirmation_code')
    if user.confirmation_code != confirmation_code:
        user.confirmation_code = ''
        user.save()
        raise ValidationError(
            {'confirmation_code': 'Неверный код подтверждения.'}
        )
    refresh = RefreshToken.for_user(user)
    data = {
        'access': str(refresh.access_token),
        'refresh': str(refresh)
    }
    user.confirmation_code = ''
    user.save()

    return Response(data, status=status.HTTP_200_OK)


class TitleViewSet(viewsets.ModelViewSet):
    queryset = Title.objects.select_related(
        'category'
    ).prefetch_related('genre').annotate(
        rating=Avg('reviews__score')
    ).order_by(*Title._meta.ordering)
    pagination_class = LimitOffsetPagination
    filter_backends = (DjangoFilterBackend, SearchFilter)
    filterset_class = TitleFilter
    search_fields = ['name']
    permission_classes = (ReadOnlyPermission | AdminPermission,)
    http_method_names = ['get', 'post', 'patch', 'delete']

    def get_serializer_class(self):
        if self.action in ['create', 'update', 'partial_update']:
            return TitleCreateUpdateSerializer
        return TitleReadSerializer


class BaseViewSetCategoryGenre(
    mixins.ListModelMixin,
    mixins.CreateModelMixin,
    mixins.DestroyModelMixin,
    viewsets.GenericViewSet
):
    pagination_class = LimitOffsetPagination
    filter_backends = (DjangoFilterBackend, SearchFilter)
    search_fields = ('name',)
    lookup_field = 'slug'
    permission_classes = (
        ReadOnlyPermission | AdminPermission,
    )

    def __str__(self):
        return self.name


class CategoryViewSet(
    BaseViewSetCategoryGenre
):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer


class GenreViewSet(
    BaseViewSetCategoryGenre
):
    queryset = Genre.objects.all()
    serializer_class = GenreSerializer


class ReviewViewSet(viewsets.ModelViewSet):
    serializer_class = ReviewSerializer
    http_method_names = ['get', 'post', 'patch', 'delete']
    permission_classes = (
        ReadOnlyPermission | IsAuthorOrAdminOrModerator | AdminPermission,
    )

    def get_queryset(self):
        return self.get_review().reviews.all()

    def get_review(self):
        return get_object_or_404(Title, id=self.kwargs['title_id'])

    def perform_create(self, serializer):
        serializer.save(
            author=self.request.user,
            title=self.get_review()
        )


class CommentViewSet(viewsets.ModelViewSet):
    serializer_class = CommentSerializer
    http_method_names = ['get', 'post', 'patch', 'delete']
    permission_classes = (
        ReadOnlyPermission | IsAuthorOrAdminOrModerator | AdminPermission,
    )

    def get_queryset(self):
        """Получить все комментарии к отзыву."""
        return self.get_comment().comments.all()

    def get_comment(self):
        return get_object_or_404(Review, id=self.kwargs['review_id'])

    def perform_create(self, serializer):
        """Добавить новый комментарий к отзыву."""
        serializer.save(
            author=self.request.user,
            review=self.get_comment()
        )
