from django.contrib import admin
from django.urls import include, path
from campus.views import DashboardView
from .health import health

urlpatterns = [
    path('health/', health),
    path("admin/", admin.site.urls),
    path("api/auth/", include("accounts.urls")),
    path("api/dashboard/", DashboardView.as_view()),
    path("api/", include("campus.urls")),
    path("api/", include("video_analysis.urls")),
]
