from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/v1/", include("apps.core.urls")),
    path("api/v1/admin/", include("apps.accounts.urls")),
    path("api/v1/admin/", include("apps.elections.urls")),
    path("api/v1/admin/", include("apps.voting.urls_admin")),
    path("api/v1/public/", include("apps.voting.urls_public")),
    path("api/v1/admin/", include("apps.reports.urls")),
]
