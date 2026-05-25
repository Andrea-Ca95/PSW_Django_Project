from django.contrib.auth import login
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib.auth.models import Group
from django.core.paginator import Paginator
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render

from .forms import CustomerSignUpForm
from .models import (
    Appointment,
    CustomerProfile,
    ProfessionalProfile,
    Service,
    ServiceCategory,
)


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


def customer_signup(request):
    # Se l'utente è già autenticato, non ha senso mostrare la registrazione.
    if request.user.is_authenticated:
        return redirect("index")

    if request.method == "POST":
        # Form compilata dall'utente.
        form = CustomerSignUpForm(request.POST)

        if form.is_valid():
            # Salva l'utente Django.
            user = form.save(commit=False)
            user.email = form.cleaned_data["email"]
            user.first_name = form.cleaned_data["first_name"]
            user.last_name = form.cleaned_data["last_name"]
            user.save()

            # Associa il nuovo utente al gruppo Cliente.
            customer_group, _ = Group.objects.get_or_create(name="Cliente")
            user.groups.add(customer_group)

            # Crea il profilo cliente collegato all'utente.
            CustomerProfile.objects.create(
                user=user,
                phone=form.cleaned_data["phone"],
            )

            # Dopo la registrazione l'utente viene autenticato automaticamente.
            login(request, user)

            return redirect("customer-dashboard")
    else:
        # Primo caricamento della pagina: form vuota.
        form = CustomerSignUpForm()

    return render(request, "core/signup.html", {"form": form})


@login_required
@permission_required("core.can_access_customer_area", raise_exception=True)
def customer_dashboard(request):
    # Mostra solo gli appuntamenti del cliente autenticato.
    appointments = (
        Appointment.objects.filter(customer=request.user)
        .select_related("service", "operator")
        .order_by("date", "start_time")
    )

    context = {
        "appointments": appointments,
    }

    return render(request, "core/customer_dashboard.html", context)


@login_required
@permission_required("core.can_access_professional_area", raise_exception=True)
def professional_dashboard(request):
    # Mostra solo gli appuntamenti assegnati al professionista autenticato.
    appointments = (
        Appointment.objects.filter(operator=request.user)
        .select_related("service", "customer")
        .order_by("date", "start_time")
    )

    context = {
        "appointments": appointments,
    }

    return render(request, "core/professional_dashboard.html", context)