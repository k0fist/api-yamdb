from rest_framework import serializers, status
from rest_framework.validators import UniqueValidator
from django.contrib.auth import get_user_model
from rest_framework_simplejwt.tokens import RefreshToken
from titles.models import Title, Category, Genre
from reviews.models import Review, Comment
from titles.validators import validate_username
from datetime import datetime
from django.core.validators import MinValueValidator, MaxValueValidator


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
        """Общая валидация."""
        if User.objects.filter(username=data.get('username')).exists():
            if not User.objects.filter(email=data.get('email')).exists():
                raise serializers.ValidationError('Username уже занят.')
        if User.objects.filter(email=data.get('email')).exists():
            if not User.objects.filter(username=data.get('username')).exists():
                raise serializers.ValidationError('Email уже занят.')

        return data

    def validate_username(self, value):
        """Валидация username."""
        validate_username(value)
        return value


class TokenSerializer(serializers.ModelSerializer):

    username = serializers.CharField(max_length=150, required=True)
    confirmation_code = serializers.CharField(max_length=6, required=True)

    class Meta:
        """Настройки для сериализации модели User."""

        model = get_user_model()
        fields = (
            'username', 'confirmation_code'
        )


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
                raise serializers.ValidationError('Такие символы '
                                                  'запрещены в slug.')
        return value


class GenreSerializer(serializers.ModelSerializer):

    class Meta:
        model = Genre
        fields = ('name', 'slug')

    def validate_slug(self, value):
        """Проверяем, что slug соответствует правилам."""
        if len(value) > 50:
            raise serializers.ValidationError(
                'Slug не должен превышать 50 символов.'
            )
        if not value.replace('-', '').replace('_', '').isalnum():
            raise serializers.ValidationError(
                'Slug может содержать только латинские буквы,'
                'цифры, дефис и нижнее подчеркивание.'
            )
        return value


class TitleSerializer(serializers.ModelSerializer):
    category = serializers.SlugRelatedField(
        queryset=Category.objects.all(), slug_field='slug', write_only=True
    )
    genre = serializers.SlugRelatedField(
        queryset=Genre.objects.all(),
        slug_field='slug', many=True, write_only=True
    )
    name = serializers.CharField(max_length=256)

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

    def validate_name(self, value):
        if len(value) > 256:
            raise serializers.ValidationError('Название произведения не может '
                                              'быть длиннее 256 символов.')
        return value

    def validate_year(self, value):
        current_year = datetime.now().year
        if value and int(value) > current_year:
            raise serializers.ValidationError(
                {'year': 'Год: {year} не может быть больше текущего.'}
            )
        return value


class ReviewSerializer(serializers.ModelSerializer):
    author = serializers.SlugRelatedField(
        read_only=True,
        slug_field='username'
    )
    title = serializers.PrimaryKeyRelatedField(read_only=True)
    pub_date = serializers.DateTimeField(
        format='%Y-%m-%dT%H:%M:%SZ',
        read_only=True
    )
    score = serializers.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(10)]
    )

    class Meta:
        model = Review
        fields = ['id', 'title', 'author', 'text', 'score', 'pub_date']

    # def validate_score(self, value):
    #     """Валидация оценки (score)"""
    #     if value < 1 or value > 10:
    #         raise serializers.ValidationError('Оценка должна быть от 1 до 10.')
    #     return value

    def validate(self, data):
        request = self.context.get('request')
        if request and request.method == 'POST':
            user = request.user
            title_id = self.context['view'].kwargs.get('title_id')
            if Review.objects.filter(title_id=title_id, author=user).exists():
                raise serializers.ValidationError('Вы уже оставили отзыв'
                                                  ' к этому заголовку.')
        return data


class CommentSerializer(serializers.ModelSerializer):
    author = serializers.StringRelatedField()
    pub_date = serializers.DateTimeField(
        format='%Y-%m-%dT%H:%M:%SZ',
        read_only=True
    )

    class Meta:
        model = Comment
        fields = ['id', 'text', 'author', 'pub_date']
    