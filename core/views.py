from django.shortcuts import render
from django.http import HttpResponse

def home(request):
    return HttpResponse("Hola, Andrea 👋")


def custom_404(request, exception=None):
    """Custom 404 error page.
    Renders templates/404.html with status code 404.
    """
    return render(request, "404.html", status=404)


def preview_404(request):
    """Render the 404 template with 200 status for preview while DEBUG=True."""
    return render(request, "404.html", status=200)