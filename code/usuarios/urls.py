from django.contrib.auth.views import LoginView, LogoutView
from django.urls import path

from . import views
from .forms import LoginForm

app_name = "usuarios"

urlpatterns = [
    path(
        "login/",
        LoginView.as_view(
            template_name="usuarios/login.html",
            authentication_form=LoginForm,
        ),
        name="login",
    ),
    path("logout/", LogoutView.as_view(), name="logout"),
    path("registro/", views.RegistroView.as_view(), name="registro"),
    path("painel/", views.PainelView.as_view(), name="painel"),
]
