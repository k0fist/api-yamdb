from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError

from reviews.models import Review, Comment, Title, Category, Genre
from reviews.validators import validate_username


User = get_user_model()

USERNAME_LENGTH_MAX = 150
EMAIL_LENGTH_MAX = 254


class UserValidationMixin:

    def validate_username(self, username):
        """Валидация username."""
        return validate_username(username)

    def validate_email(self, email):
        """Валидация email, разрешаем повторное использование."""
        user = User.objects.filter(email=email).first()
        if user:
            return email
        return email


class SignUpValidationMixin:
    def validate(self, data):
        """Проверяем соответствие username и email."""
        username = data.get("username")
        email = data.get("email")
        user = User.objects.filter(username=username).first()
        if user:
            if user.email != email:
                raise ValidationError(
                    "Этот username уже зарегистрирован с другим email."
                )
            return data
        if User.objects.filter(email=email).exists():
            raise ValidationError("Этот email уже зарегистрирован.")
        return data


class UserSerializer(UserValidationMixin, serializers.ModelSerializer):

    class Meta:
        model = User
        fields = (
            'username', 'email', 'first_name', 'last_name', 'bio', 'role'
        )


class SignUpSerializer(
    UserValidationMixin, SignUpValidationMixin, serializers.Serializer
):
    username = serializers.CharField(
        max_length=USERNAME_LENGTH_MAX,
        required=True
    )
    email = serializers.EmailField(max_length=EMAIL_LENGTH_MAX, required=True)


class TokenSerializer(UserValidationMixin, serializers.Serializer):
    """Сериализатор для запроса токена."""
    username = serializers.CharField(
        max_length=USERNAME_LENGTH_MAX,
        help_text="Имя пользователя.")
    confirmation_code = serializers.CharField(
        help_text="Код подтверждения, отправленный на почту."
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
#review/version_2.1
    #rating = serializers.SerializerMethodField()

    category = CategorySerializer()
    genre = GenreSerializer(many=True)


    class Meta:
        model = Title
        fields = ('id', 'name', 'year',
                  'category', 'genre', 'description', 'rating'
                  )
        read_only_fields = fields

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
