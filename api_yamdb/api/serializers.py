import re

from rest_framework import serializers
from django.contrib.auth import get_user_model


from titles.models import Title, Category, Genre
from reviews.models import Review, Comment


User = get_user_model()


class UserSerializer(serializers.ModelSerializer):

    class Meta:
        """Настройки для сериализации модели User."""

        model = User
        fields = (
            'username', 'email', 'first_name', 'last_name', 'bio', 'role'
        )

    def validate_username(self, username):
        """Проверка, что username соответствует требованиям."""
        if username == "me":
            raise serializers.ValidationError('Запрещено использовать "me".')
        invalid_chars = re.findall(r'[^\w.@+-]', username)
        if invalid_chars:
            invalid_chars_str = ''.join(set(invalid_chars))
            raise serializers.ValidationError(
                f'Недопустимые символы в username: {invalid_chars_str}'
            )
        return username


class CategorySerializer(serializers.ModelSerializer):

    class Meta:
        model = Category
        fields = ('name', 'slug')


class GenreSerializer(serializers.ModelSerializer):

    class Meta:
        model = Genre
        fields = ('name', 'slug')


class TitleReadSerializer(serializers.ModelSerializer):
    
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
                  'category', 'genre', 'description', 'rating'
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
