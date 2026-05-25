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

    # Creazione appuntamento per un servizio selezionato.
    path(
    "servizi/<int:service_pk>/prenota/",
    views.appointment_create,
    name="appointment-create",),

    # Annullamento prenotazione da parte del cliente.
    path("appuntamenti/<int:pk>/annulla/",views.appointment_cancel,name="appointment-cancel",),

    # Aggiornamento stato appuntamento da parte del professionista.
    path(
    "appuntamenti/<int:pk>/aggiorna-stato/",views.professional_update_appointment_status, name="professional-update-appointment-status",),

    # Registrazione pubblica per nuovi clienti.
    path("registrazione/", views.customer_signup, name="signup"),

    # Area riservata ai clienti.
    path("area-cliente/", views.customer_dashboard, name="customer-dashboard"),

    # Area riservata ai professionisti.
    path(
        "area-professionista/",
        views.professional_dashboard,
        name="professional-dashboard",
    ),
]