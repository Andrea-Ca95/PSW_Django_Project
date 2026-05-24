from django.contrib import admin
from django.urls import include, path


# URL principali del progetto Django.
urlpatterns = [
    # Pannello amministrativo di Django.
    path("admin/", admin.site.urls),

    # Tutte le pagine pubbliche e interne dell'app core.
    path("", include("core.urls")),
]