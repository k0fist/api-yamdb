from rest_framework import serializers
from rest_framework.validators import UniqueValidator
from django.contrib.auth import get_user_model
from titles.models import Title, Category, Genre, Review, Comment

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    username = serializers.CharField(max_length=150, required=True)
    email = serializers.EmailField(max_length=254, required=True)
    first_name = serializers.CharField(max_length=150, required=False)
    last_name = serializers.CharField(max_length=150, required=False)

    class Meta:
        """Настройки для сериализации модели User."""

        model = get_user_model()
        fields = (
            'username', 'email', 'first_name', 'last_name', 'bio', 'role'
        )

    def validate(self, data):
        if User.objects.filter(username=data.get('username')).exists():
            raise serializers.ValidationError('Username уже занят.')
        if User.objects.filter(email=data.get('email')).exists():
            raise serializers.ValidationError('Email уже занят.')

        return data

    def validate_username(self, value):
        """Проверка, что username соответствует регулярному выражению."""
        if value:
            import re
            if not re.match(r'^[\w.@+-]+\Z', value):
                raise serializers.ValidationError("Invalid username format.")
        return value


class TitleSerializer(serializers.ModelSerializer):
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
        model = Title
        fields = ('id', 'category', 'genre', 'name', 'year')


class CategorySerializer(serializers.ModelSerializer):
    name = serializers.CharField(max_length=256, required=True)
    slug = serializers.SlugField(
        max_length=50, required=True,
        validators=[UniqueValidator(queryset=Category.objects.all())]
    )

    class Meta:
        model = Category
        fields = ('name', 'slug')

    def validate_slug(self, value):
        """Проверка, что username соответствует регулярному выражению."""
        if value:
            import re
            if not re.match(r'^[-a-zA-Z0-9_]+$', value):
                raise serializers.ValidationError("Invalid slug format.")
        return value


class GenreSerializer(serializers.ModelSerializer):

    def validate_slug(self, value):
        """Проверяем, что slug соответствует правилам."""
        if len(value) > 50:
            raise serializers.ValidationError("Slug не должен превышать 50 символов.")
        if not value.replace("-", "").replace("_", "").isalnum():
            raise serializers.ValidationError(
                "Slug может содержать только латинские буквы, цифры, дефис и нижнее подчеркивание."
            )
        return value

    class Meta:
        model = Genre
        fields = ('name', 'slug')


class ReviewSerializer(serializers.ModelSerializer):
    author = serializers.StringRelatedField(read_only=True)
    pub_date = serializers.DateTimeField(format="%Y-%m-%dT%H:%M:%SZ", read_only=True)
    class Meta:
        model = Review
        fields = ['id', 'title', 'author', 'text', 'score', 'pub_date']

    def validate(self, data):
        """Проверка на уникальность отзыва для произведения и пользователя"""
        if Review.objects.filter(title=data['title'], author=data['author']).exists():
            raise serializers.ValidationError(
                "Вы уже оставили отзыв для этого произведения."
            )
        return data


class CommentSerializer(serializers.ModelSerializer):
    author = serializers.StringRelatedField()
    pub_date = serializers.DateTimeField(
        format="%Y-%m-%dT%H:%M:%SZ",
        read_only=True
    )

    class Meta:
        model = Comment
        fields = ['id', 'text', 'author', 'pub_date']
