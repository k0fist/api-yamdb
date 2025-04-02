from django.contrib.auth.models import AbstractUser
from django.db import models
from django.db.models import Avg

from .validators import validate_username


ADMIN = 'admin'
MODERATOR = 'moderator'
USER = 'user'


class User(AbstractUser):
    """Переопределение страндартной модели пользователя."""

    ROLE_CHOICES = [
        (ADMIN, 'Admin'),
        (MODERATOR, 'Moderator'),
        (USER, 'User'),
    ]
    confirmation_code = models.TextField(
        'Код подтверждения',
        max_length=6,
        default=''
    )
    username = models.CharField(max_length=150, unique=True, validators=[validate_username])
    email = models.EmailField(max_length=254, unique=True)  # Уникальный email
    first_name = models.CharField(max_length=150, blank=True)  # Необязательное поле для имени
    last_name = models.CharField(max_length=150, blank=True)
    bio = models.TextField(blank=True, null=True)
    role = models.CharField(
        max_length=50,
        choices=ROLE_CHOICES,
        default='user'
    )
    email = models.EmailField(unique=True)
    username = models.CharField(max_length=150, unique=True)

    def save(self, *args, **kwargs):
        """Переопределение метода save для автоматической установки роли."""
        if self.is_superuser:
            self.role = 'superuser'
        elif self.is_staff:
            self.role = 'admin'
        super().save(*args, **kwargs)

    def clean(self):
        super().clean()
        validate_username(self.username)

    def is_admin(self):
        return self.role == ADMIN or self.is_staff
    
    def is_moderator_or_admin(self):
        return self.role in {ADMIN, MODERATOR} or self.is_staff

    def __str__(self):
        return self.username


class Genre(models.Model):
    name = models.CharField(max_length=256, unique=True)
    slug = models.SlugField(max_length=50, unique=True)

    def __str__(self):
        return self.name


class Category(models.Model):
    name = models.CharField(max_length=256, unique=True)
    slug = models.SlugField(max_length=50, unique=True)

    def __str__(self):
        return self.name


class Title(models.Model):
    name = models.CharField(max_length=256)
    category = models.ForeignKey(
        Category,
        on_delete=models.SET_NULL,
        null=True,
        related_name='titles'
    )
    genre = models.ManyToManyField(Genre, related_name='titles')
    year = models.PositiveIntegerField()
    description = models.TextField(blank=True, null=True)
    rating = models.FloatField(null=True, blank=True)

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
