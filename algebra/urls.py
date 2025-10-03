from django.urls import path
from . import views

urlpatterns = [
    path("", views.index, name="index"),
    path("suma/", views.suma, name="suma"),
    path("multiplicacion/", views.multiplicacion, name="multiplicacion"),
    path("gauss/", views.gauss, name="gauss"),
    path("gauss-jordan/", views.gauss_jordan, name="gauss_jordan"),
]