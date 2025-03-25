from rest_framework import viewsets, mixins, permissions, serializers, status
from rest_framework.response import Response
from rest_framework.views import APIView
from django_filters.rest_framework import DjangoFilterBackend
from datetime import datetime
from django.contrib.auth import get_user_model
from rest_framework_simplejwt.tokens import RefreshToken
import uuid
from django.core.mail import send_mail

from titles.models import Title, Category, Genre
from .serializers import (
    TitleSerializer, CategorySerializer, GenreSerializer)
# from .permissions import


User = get_user_model()


class SignupView(APIView):
    """Регистрация нового пользовователя."""

    def post(self, request):
        # import pdb; pdb.set_trace()
        email = request.data.get('email')
        username = request.data.get('username')
        if username == 'me':
            return Response(
                {'error': 'Введите корректный username'},
                status=status.HTTP_400_BAD_REQUEST
            )
        if not email or not username:
            return Response(
                {'error': 'Email и username обязательны'},
                status=status.HTTP_400_BAD_REQUEST
            )
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
            {'message': 'Проверьте свою почту для получения '
             'кода подтверждения'},
            status=status.HTTP_200_OK
        )


class TokenView(APIView):
    """Формирование токена при корретный данных."""

    def post(self, request):
        #import pdb; pdb.set_trace()
        username = request.data.get('username')
        confirmation_code = request.data.get('confirmation_code')
        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            return Response(
                {'error': 'Неверные данные'},
                status=status.HTTP_400_BAD_REQUEST
            )
        if user.confirmation_code != confirmation_code:
            return Response(
                {'error': 'Неверный код подтверждения'},
                status=status.HTTP_400_BAD_REQUEST
            )
        refresh = RefreshToken.for_user(user)
        user.confirmation_code = ""
        user.save()
        return Response({
            'access': str(refresh.access_token),
            'refresh': str(refresh)
        }, status=status.HTTP_200_OK)

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
