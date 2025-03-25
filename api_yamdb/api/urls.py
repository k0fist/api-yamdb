from django.urls import include, path
from . import views

urlpatterns = [
    path(
        'v1/auth/signup/',
        views.SignupView.as_view(),
        name='signup'
    ),
    path(
        'v1/auth/token/',
        views.TokenView.as_view(),
        name='token'
    )
]
