from rest_framework import serializers

from titles.models import Title, Category, Genre, Review, Comment


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
