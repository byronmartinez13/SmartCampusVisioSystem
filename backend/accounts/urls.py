from django.urls import path
from . import views

urlpatterns = [
    path("csrf/", views.CsrfView.as_view()),
    path("register/", views.RegisterView.as_view()),
    path("login/", views.LoginView.as_view()),
    path("logout/", views.LogoutView.as_view()),
    path("me/", views.MeView.as_view()),
    path("password/recover/", views.RecoveryView.as_view()),
    path("password/reset/", views.ResetView.as_view()),
    path("password/change/", views.ChangePasswordView.as_view()),
    path("users/", views.UserListView.as_view()),
    path('users/<int:pk>/access/', views.UserAccessView.as_view()),
]
