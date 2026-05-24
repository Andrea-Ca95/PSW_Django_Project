from django.shortcuts import render

from .models import Appointment, ProfessionalProfile, Service


def index(request):
    # Numero di visite salvato nella sessione del browser.
    # Se non esiste ancora, parte da 0.
    num_visits = request.session.get("num_visits", 0) + 1
    request.session["num_visits"] = num_visits

    # Dati sintetici mostrati nella home.
    active_services_count = Service.objects.filter(is_active=True).count()
    professionals_count = ProfessionalProfile.objects.count()
    appointments_count = Appointment.objects.count()

    # Contesto passato al template home.html.
    context = {
        "num_visits": num_visits,
        "active_services_count": active_services_count,
        "professionals_count": professionals_count,
        "appointments_count": appointments_count,
    }

    return render(request, "core/home.html", context)