from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    TitleViewSet, CategoryViewSet, GenreViewSet, SignupView, TokenView,
    CommentViewSet, ReviewViewSet
)

router = DefaultRouter()
router.register('users', UserView, basename='user')
router.register('titles', TitleViewSet, basename='title')
router.register('categories', CategoryViewSet, basename='category')
router.register('genres', GenreViewSet, basename='genre')
router.register(
    r'titles/(?P<title_id>\d+)/reviews',
    ReviewViewSet,
    basename='review'
)
router.register(
    r'titles/(?P<title_id>\d+)/reviews/(?P<review_id>\d+)/comments',
    CommentViewSet,
    basename='comment'
)

urlpatterns = [
    path('v1/', include(router.urls)),
    path(
        'v1/auth/signup/',
        SignupView.as_view(),
        name='signup'
    ),
    path(
        'v1/auth/token/',
        TokenView.as_view(),
        name='token'
    )
]
