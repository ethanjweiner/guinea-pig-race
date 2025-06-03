from django.urls import path

from . import views

urlpatterns = [
    path("", views.index, name="index"),
    path("home", views.home, name="home"),
    path("register", views.register, name="register"),
    path("results", views.results, name="results"),
    path("awards", views.awards, name="awards"),
    path("about", views.about, name="about"),
]
