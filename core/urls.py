from django.urls import path

from . import views


# URL gestiti dall'app core.
urlpatterns = [
    # Home pubblica di Appunto.
    path("", views.index, name="index"),

    # Lista pubblica dei servizi con ricerca e paginazione.
    path("servizi/", views.service_list, name="service-list"),

    # Dettaglio pubblico di un singolo servizio.
    path("servizi/<int:pk>/", views.service_detail, name="service-detail"),
]