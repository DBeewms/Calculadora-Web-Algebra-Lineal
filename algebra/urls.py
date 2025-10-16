from django.urls import path
from . import views

urlpatterns = [
    path("", views.index, name="index"),
    path("suma/", views.suma, name="suma"),
    path("multiplicacion/", views.multiplicacion, name="multiplicacion"),
    path("escalar/", views.escalar, name="escalar"),
    path("transposicion/", views.transposicion, name="transposicion"),
    path("inversa/", views.inversa, name="inversa"),
    path("gauss/", views.gauss, name="gauss"),
    path("gauss-jordan/", views.gauss_jordan, name="gauss_jordan"),
    path("homogeneo/", views.homogeneo, name="homogeneo"),
]