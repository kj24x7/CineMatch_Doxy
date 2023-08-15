from django.contrib import admin
from django.urls import include, path
from django.views.generic import RedirectView

urlpatterns = [
    path("CineMatch/", include("CineMatch.urls")),
    path("admin/", admin.site.urls),
]
