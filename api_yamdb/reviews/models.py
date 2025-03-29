from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from titles.models import Title, User


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

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        self.title.update_rating()

    def delete(self, *args, **kwargs):
        super().delete(*args, **kwargs)
        self.title.update_rating()


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
