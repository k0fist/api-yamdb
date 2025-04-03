from rest_framework import serializers
from django.contrib.auth import get_user_model

from reviews.models import Review, Comment, Title, Category, Genre
from reviews.validators import validate_username


User = get_user_model()


class BaseUserSignupSerializer(serializers.ModelSerializer):
    def validate_username(self, username):
        """Валидация username."""
        validate_username(username)
        return username


class UserSerializer(BaseUserSignupSerializer):

    class Meta:
        """Настройки для сериализации модели User."""

        model = User
        fields = (
            'username', 'email', 'first_name', 'last_name', 'bio', 'role'
        )


class SignUpSerializer(BaseUserSignupSerializer):
    username = serializers.CharField(max_length=150, required=True)
    email = serializers.EmailField(max_length=254, required=True)

    class Meta:
        """Настройки для сериализации модели User."""

        model = User
        fields = (
            'username', 'email'
        )

    def validate(self, data):
        """Общая валидация."""
        if User.objects.filter(username=data.get('username')).exists():
            if not User.objects.filter(email=data.get('email')).exists():
                raise serializers.ValidationError('Username уже занят.')
        if User.objects.filter(email=data.get('email')).exists():
            if not User.objects.filter(username=data.get('username')).exists():
                raise serializers.ValidationError('Email уже занят.')

        return data


class TokenSerializer(serializers.ModelSerializer):

    class Meta:
        """Настройки для сериализации модели User."""

        model = User
        fields = (
            'username', 'confirmation_code'
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
    rating = serializers.SerializerMethodField()

    class Meta:
        model = Title
        fields = ('id', 'name', 'year',
                  'category', 'genre', 'description', 'rating'
                  )

    def to_representation(self, instance):
        """Изменяем вывод данных для соответствия ожидаемому формату."""
        representation = super().to_representation(instance)
        representation['category'] = {
            'name': instance.category.name,
            'slug': instance.category.slug
        }
        representation['genre'] = [
            {'name': genre.name, 'slug': genre.slug}
            for genre in instance.genre.all()
        ]
        return representation

    def get_rating(self, obj):
        reviews = obj.reviews.all()
        if reviews.exists():
            return round(
                sum(review.score for review in reviews) / reviews.count(), 1
            )
        return None


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
        title_id = self.context['view'].kwargs.get('title_id')
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
