from django.core.paginator import Paginator
from django.db.models import Q
from django.shortcuts import get_object_or_404, render

from .models import Appointment, ProfessionalProfile, Service, ServiceCategory


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


def service_list(request):
    # Parametri letti dalla query string.
    # Esempio: /servizi/?q=documenti&category=1
    query = request.GET.get("q", "").strip()
    selected_category = request.GET.get("category", "").strip()

    # Mostriamo solo i servizi attivi nella parte pubblica del sito.
    services = Service.objects.filter(is_active=True).select_related("category")

    # Ricerca server-side su nome, descrizione e categoria.
    if query:
        services = services.filter(
            Q(name__icontains=query)
            | Q(description__icontains=query)
            | Q(category__name__icontains=query)
        )

    # Filtro opzionale per categoria.
    if selected_category:
        services = services.filter(category_id=selected_category)

    # Ordinamento stabile prima della paginazione.
    services = services.order_by("name")

    # Paginazione: 3 servizi per pagina, utile per dimostrare il requisito.
    paginator = Paginator(services, 3)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    # Categorie usate nella select del filtro.
    categories = ServiceCategory.objects.all().order_by("name")

    context = {
        "page_obj": page_obj,
        "services": page_obj.object_list,
        "categories": categories,
        "query": query,
        "selected_category": selected_category,
    }

    return render(request, "core/service_list.html", context)


def service_detail(request, pk):
    # Recupera solo servizi attivi, evitando dettagli pubblici per servizi disattivati.
    service = get_object_or_404(
        Service.objects.select_related("category"),
        pk=pk,
        is_active=True,
    )

    # Professionisti che possono svolgere il servizio selezionato.
    professionals = service.professionals.select_related("user").order_by(
        "user__last_name",
        "user__first_name",
    )

    context = {
        "service": service,
        "professionals": professionals,
    }

    return render(request, "core/service_detail.html", context)