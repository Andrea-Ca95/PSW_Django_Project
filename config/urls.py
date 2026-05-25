from django.contrib import admin
from django.urls import include, path


# URL principali del progetto Django.
urlpatterns = [
    # Pannello amministrativo di Django.
    path("admin/", admin.site.urls),

    # URL standard Django per login, logout e gestione password.
    path("accounts/", include("django.contrib.auth.urls")),

    # URL dell'app principale.
    path("", include("core.urls")),
]