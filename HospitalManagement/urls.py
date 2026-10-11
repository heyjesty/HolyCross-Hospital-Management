from django.contrib import admin
from django.urls import include, path, re_path

from Frontend.views import media

urlpatterns = [
    path("admin/", admin.site.urls),
    path("Backend/", include("Backend.urls")),
    re_path(r"^media/(?P<path>.+)$", media, name="media"),
    path("", include("Frontend.urls")),
]

handler404 = "Frontend.views.page_not_found"
