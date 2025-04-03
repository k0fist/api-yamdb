from django.db import models
from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.core.validators import MinValueValidator, MaxValueValidator

from reviews.validators import validate_username, validate_year


MIN_SCORE = 1
MAX_SCORE = 10
ADMIN = 'admin'
MODERATOR = 'moderator'
USER = 'user'
SIZE_USERNAME = 150
SIZE_EMAIL = 254


class User(AbstractUser):
    """Переопределение стандартной модели пользователя."""

    ROLE_CHOICES = [
        (ADMIN, 'Admin'),
        (MODERATOR, 'Moderator'),
        (USER, 'User'),
    ]
    confirmation_code = models.CharField(
        verbose_name='Код подтверждения',
        max_length=settings.PIN_CODE_LENGTH,
        default=''
    )
    username = models.CharField(
        verbose_name='Имя пользователя',
        max_length=SIZE_USERNAME,
        unique=True,
        validators=[validate_username]
    )
    email = models.EmailField(
        verbose_name='Электронная почта',
        max_length=SIZE_EMAIL,
        unique=True
    )
    bio = models.TextField(
        verbose_name='Биография',
        blank=True,
        null=True
    )
    role = models.CharField(
        verbose_name='Роль',
        max_length=max(len(role) for role, _ in ROLE_CHOICES),
        choices=ROLE_CHOICES,
        default=USER
    )

    def is_admin(self):
        return self.role == ADMIN or self.is_staff

    def is_moderator(self):
        return self.role == MODERATOR

    def __str__(self):
        return self.username

    class Meta:
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'


class BaseNamedModel(models.Model):
    """Абстрактная модель для сущностей с названием и slug."""
    name = models.CharField(
        verbose_name='Название',
        max_length=256,
        unique=True
    )
    slug = models.SlugField(
        verbose_name='Slug',
        max_length=50,
        unique=True
    )

    def __str__(self):
        return self.name

    class Meta:
        abstract = True
        ordering = ('name',)


class Genre(BaseNamedModel):
    """Модель жанров."""

    class Meta(BaseNamedModel.Meta):
        verbose_name = 'Жанр'
        verbose_name_plural = 'Жанры'


class Category(BaseNamedModel):
    """Модель категорий."""

    class Meta(BaseNamedModel.Meta):
        verbose_name = 'Категория'
        verbose_name_plural = 'Категории'


class Title(models.Model):
    name = models.CharField(
        verbose_name='Название произведения',
        max_length=256
    )
    category = models.ForeignKey(
        Category,
        on_delete=models.SET_NULL,
        null=True,
        related_name='titles',
        verbose_name='Категория'
    )
    genre = models.ManyToManyField(
        Genre,
        related_name='titles',
        verbose_name='Жанр'
    )
    year = models.IntegerField(
        validators=[validate_year],
        verbose_name='Год выпуска'
    )
    description = models.TextField(
        verbose_name='Описание',
        blank=True,
        null=True
    )

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = 'Произведение'
        verbose_name_plural = 'Произведения'
        ordering = ('name',)


class BaseReviewComment(models.Model):
    """Базовая модель для отзывов и комментариев."""
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='%(class)ss',
        verbose_name='Автор'
    )
    text = models.TextField(verbose_name='Текст')
    pub_date = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Дата публикации'
    )

    class Meta:
        abstract = True
        ordering = ('-pub_date',)


class Review(BaseReviewComment):
    """Модель отзывов."""
    title = models.ForeignKey(
        Title,
        on_delete=models.CASCADE,
        related_name='reviews',
        verbose_name='Произведение'
    )
    score = models.IntegerField(
        validators=[
            MinValueValidator(MIN_SCORE),
            MaxValueValidator(MAX_SCORE)
        ],
        verbose_name='Оценка'
    )

    class Meta(BaseReviewComment.Meta):
        constraints = [
            models.UniqueConstraint(
                fields=['title', 'author'],
                name='unique_review_per_title'
            )
        ]
        verbose_name = 'Отзыв'
        verbose_name_plural = 'Отзывы'


class Comment(BaseReviewComment):
    """Модель комментариев к отзывам."""
    review = models.ForeignKey(
        Review,
        on_delete=models.CASCADE,
        related_name='comments',
        verbose_name='Отзыв'
    )

    class Meta(BaseReviewComment.Meta):
        verbose_name = 'Комментарий'
        verbose_name_plural = 'Комментарии'
