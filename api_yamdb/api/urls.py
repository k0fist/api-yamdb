from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import (
    TitleViewSet, GenreViewSet, signup, token,
    CommentViewSet, ReviewViewSet, UserView, CategoryViewSet
)


router_v1 = DefaultRouter()
router_v1.register('users', UserView, basename='user')
router_v1.register('titles', TitleViewSet, basename='title')
router_v1.register('categories', CategoryViewSet, basename='category')
router_v1.register('genres', GenreViewSet, basename='genre')
router_v1.register(
    r'titles/(?P<title_id>\d+)/reviews',
    ReviewViewSet,
    basename='review'
)
router_v1.register(
    r'titles/(?P<title_id>\d+)/reviews/(?P<review_id>\d+)/comments',
    CommentViewSet,
    basename='comment'
)

auth_urls = [
    path('signup/', SignupView.as_view(), name='signup'),
    path('token/', TokenView.as_view(), name='token')
]

urlpatterns = [

    path('v1/', include(router.urls)),
    path(
        'v1/auth/signup/',
        signup,
        name='signup'
    ),
    path(
        'v1/auth/token/',
        token,
        name='token'
    )
]
