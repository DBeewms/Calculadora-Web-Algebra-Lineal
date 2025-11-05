from django.urls import path
from . import views

urlpatterns = [
    path("", views.index, name="index"),
    path("suma/", views.suma, name="suma"),
    path("multiplicacion/", views.multiplicacion, name="multiplicacion"),
    path("escalar/", views.escalar, name="escalar"),
    path("transposicion/", views.transposicion, name="transposicion"),
    path("compuestas/", views.compuestas, name="compuestas"),
    path("inversa/", views.inversa, name="inversa"),
    path("determinante/", views.determinante, name="determinante"),
    path("cramer/", views.cramer, name="cramer"),
    path("gauss/", views.gauss, name="gauss"),
    path("gauss-jordan/", views.gauss_jordan, name="gauss_jordan"),
    path("homogeneo/", views.homogeneo, name="homogeneo"),
    # Métodos numéricos (incorporación inicial)
    path("metodos/", views.metodos_index, name="metodos_index"),
    path("metodos/cerrados/", views.metodos_cerrados, name="metodos_cerrados"),
    path("metodos/cerrados/biseccion/", views.biseccion, name="biseccion"),
]