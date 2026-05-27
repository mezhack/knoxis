import subprocess

from django.views.decorators.csrf import ensure_csrf_cookie
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from django.urls import path


@api_view(["GET"])
@permission_classes([AllowAny])
def healthz(request):
    return Response({"status": "ok"})


@api_view(["GET"])
@permission_classes([AllowAny])
@ensure_csrf_cookie
def csrf_view(request):
    return Response(status=204)


@api_view(["GET"])
@permission_classes([AllowAny])
def version_view(request):
    try:
        commit = subprocess.check_output(
            ["git", "rev-parse", "--short", "HEAD"], stderr=subprocess.DEVNULL
        ).decode().strip()
    except Exception:
        commit = "unknown"
    return Response({"version": "0.1.0", "commit": commit})


urlpatterns = [
    path("healthz", healthz),
    path("csrf", csrf_view),
    path("version", version_view),
]
