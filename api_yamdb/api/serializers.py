from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.conf import settings

from reviews.models import (
    Review, Comment, Title, Category, Genre,
    USERNAME_LENGTH_MAX, EMAIL_LENGTH_MAX
)
from reviews.validators import validate_username


User = get_user_model()


class UserValidationMixin:

    def validate_username(self, username):
        """Валидация username."""
        return validate_username(username)


class UserSerializer(UserValidationMixin, serializers.ModelSerializer):

    class Meta:
        model = User
        fields = (
            'username', 'email', 'first_name', 'last_name', 'bio', 'role'
        )


class SignUpSerializer(UserValidationMixin, serializers.Serializer):
    username = serializers.CharField(
        max_length=USERNAME_LENGTH_MAX,
        required=True
    )
    email = serializers.EmailField(max_length=EMAIL_LENGTH_MAX, required=True)


class TokenSerializer(UserValidationMixin, serializers.Serializer):
    """Сериализатор для запроса токена."""
    username = serializers.CharField(max_length=USERNAME_LENGTH_MAX)
    confirmation_code = serializers.CharField(
        max_length=settings.PIN_CODE_LENGTH
    )


class CategorySerializer(serializers.ModelSerializer):

    class Meta:
        model = Category
        fields = ('name', 'slug')


class GenreSerializer(serializers.ModelSerializer):

    class Meta:
        model = Genre
        fields = ('name', 'slug')


class TitleReadSerializer(serializers.ModelSerializer):
    rating = serializers.FloatField(read_only=True)
    category = CategorySerializer()
    genre = GenreSerializer(many=True)

    class Meta:
        model = Title
        fields = ('id', 'name', 'year',
                  'category', 'genre', 'description', 'rating'
                  )
        read_only_fields = fields


class TitleCreateUpdateSerializer(serializers.ModelSerializer):
    category = serializers.SlugRelatedField(
        queryset=Category.objects.all(), slug_field='slug', write_only=True
    )
    genre = serializers.SlugRelatedField(
        queryset=Genre.objects.all(),
        slug_field='slug', many=True, write_only=True
    )

    class Meta:
        model = Title
        fields = ('id', 'name', 'year',
                  'category', 'genre', 'description'
                  )

    def to_representation(self, instance):
        """Изменяем вывод данных для соответствия ожидаемому формату."""
        return TitleReadSerializer(instance).data


class ReviewSerializer(serializers.ModelSerializer):
    author = serializers.SlugRelatedField(
        read_only=True,
        slug_field='username'
    )

    class Meta:
        model = Review
        fields = ('id', 'author', 'text', 'score', 'pub_date')

    def validate(self, data):
        request = self.context.get('request')
        if request.method != 'POST':
            return data
        user = request.user
        title_id = self.context['view'].kwargs['title_id']
        if Review.objects.filter(title_id=title_id, author=user).exists():
            raise serializers.ValidationError(
                'Вы уже оставили отзыв к этому заголовку.'
            )
        return data


class CommentSerializer(serializers.ModelSerializer):
    author = serializers.SlugRelatedField(
        read_only=True, slug_field='username'
    )

    class Meta:
        model = Comment
        fields = ('id', 'text', 'author', 'pub_date')
