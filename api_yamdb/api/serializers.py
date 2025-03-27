from rest_framework import serializers

from titles.models import Title, Category, Genre


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
        fields = ('id', 'name', 'slug')
