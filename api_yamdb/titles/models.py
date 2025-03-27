from django.contrib.auth.models import AbstractUser
from django.db import models
from django.db.models import Avg
from django.core.validators import MinValueValidator, MaxValueValidator


class User(AbstractUser):
    """Переопределение страндартной модели пользователя."""

    ROLE_CHOICES = [
        ('user', 'User'),
        ('moderator', 'Moderator'),
        ('admin', 'Admin'),
        ('superuser', 'Superuser'),
    ]
    confirmation_code = models.TextField(
        'Код подтверждения',
        default=''
    )
    bio = models.TextField(blank=True, null=True)
    role = models.CharField(
        max_length=50,
        choices=ROLE_CHOICES,
        default='user'
    )

    def save(self, *args, **kwargs):
        """Переопределение метода save для автоматической установки роли."""
        if self.is_superuser:
            self.role = 'superuser'
        elif self.is_staff:
            self.role = 'admin'
        super().save(*args, **kwargs)

    def __str__(self):
        return self.username


class Title(models.Model):
    name = models.CharField(max_length=200)
    category = models.ForeignKey(
        'Category',
        on_delete=models.SET_NULL,
        null=True,
        related_name='titles'
    )
    genre = models.ManyToManyField('Genre', related_name='titles')
    year = models.PositiveIntegerField()
    description = models.TextField(blank=True, null=True)
    rating = models.FloatField(null=True, blank=True)  # Средний рейтинг

    def update_rating(self):
        """Обновляет среднюю оценку произведения."""
        average_score = self.reviews.aggregate(
            avg_score=Avg('score'))['avg_score']
        self.rating = (
            round(average_score, 1)
            if average_score is not None
            else None
        )
        self.save()


class Review(models.Model):
    title = models.ForeignKey(
        Title,
        on_delete=models.CASCADE,
        related_name='reviews'
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='user_reviews'
    )
    text = models.TextField()
    score = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(10)]
    )
    pub_date = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['title', 'author'],
                name='unique_review_per_title'
            )
        ]


class Genre(models.Model):
    name = models.CharField(max_length=256, unique=True)
    slug = models.SlugField(max_length=256, unique=True)


class Category(models.Model):
    name = models.CharField(max_length=256, unique=True)
    slug = models.SlugField(unique=True)


class Comment(models.Model):
    review = models.ForeignKey(
        'Review',
        on_delete=models.CASCADE,
        related_name='comments'
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='comments'
    )
    text = models.TextField()
    pub_date = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-pub_date']
