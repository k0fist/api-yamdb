from rest_framework import serializers
from django.contrib.auth import get_user_model
from titles.models import Title, Category, Genre

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
        fields = '__all__'


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ('name', 'slug')


class GenreSerializer(serializers.ModelSerializer):
    class Meta:
        model = Genre
        fields = ('id', 'name', 'slug')
