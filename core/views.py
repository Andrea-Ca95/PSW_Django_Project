from django.contrib.auth import login
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib.auth.models import Group
from django.core.paginator import Paginator
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from .forms import AppointmentCreateForm, CustomerSignUpForm
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

@login_required
@permission_required("core.can_access_customer_area", raise_exception=True)
def appointment_create(request, service_pk):
    # Recupera il servizio da prenotare solo se è attivo.
    service = get_object_or_404(Service, pk=service_pk, is_active=True)

    if request.method == "POST":
        # Form compilata dal cliente.
        form = AppointmentCreateForm(request.POST, service=service)

        if form.is_valid():
            appointment = form.save(commit=False)

            # Il cliente è sempre l'utente autenticato.
            appointment.customer = request.user

            # Il servizio arriva dall'URL, non dal form.
            appointment.service = service

            appointment.save()

            return redirect("customer-dashboard")
    else:
        # Primo caricamento: form vuota filtrata sul servizio scelto.
        form = AppointmentCreateForm(service=service)

    context = {
        "form": form,
        "service": service,
    }

    return render(request, "core/appointment_form.html", context)

@login_required
@permission_required("core.can_access_customer_area", raise_exception=True)
@require_POST
def appointment_cancel(request, pk):
    # Recupera solo appuntamenti appartenenti al cliente autenticato.
    appointment = get_object_or_404(
        Appointment,
        pk=pk,
        customer=request.user,
    )

    # Il cliente può annullare solo appuntamenti ancora gestibili.
    if appointment.can_be_cancelled_by_customer():
        appointment.status = Appointment.STATUS_CANCELLED
        appointment.save()

    return redirect("customer-dashboard")

@login_required
@permission_required("core.can_manage_appointments", raise_exception=True)
@require_POST
def professional_update_appointment_status(request, pk):
    # Recupera solo appuntamenti assegnati al professionista autenticato.
    appointment = get_object_or_404(
        Appointment,
        pk=pk,
        operator=request.user,
    )

    # Azione scelta dal pulsante premuto nella dashboard professionista.
    action = request.POST.get("action")

    # Un appuntamento in attesa può essere confermato solo se non è passato.
    # Può invece essere annullato anche se è già passato.
    if appointment.status == Appointment.STATUS_PENDING:
        if action == "confirm" and not appointment.is_past:
            appointment.status = Appointment.STATUS_CONFIRMED
            appointment.save()

        elif action == "cancel":
            appointment.status = Appointment.STATUS_CANCELLED
            appointment.save()

    # Un appuntamento confermato può essere completato o annullato.
    elif appointment.status == Appointment.STATUS_CONFIRMED:
        if action == "complete":
            appointment.status = Appointment.STATUS_COMPLETED
            appointment.save()

        elif action == "cancel":
            appointment.status = Appointment.STATUS_CANCELLED
            appointment.save()

    return redirect("professional-dashboard")

@login_required
@permission_required("core.change_service", raise_exception=True)
def admin_dashboard(request):
    # Area gestionale visibile solo agli utenti con permesso di modifica servizi.

    total_services = Service.objects.count()
    active_services = Service.objects.filter(is_active=True).count()
    total_customers = CustomerProfile.objects.count()
    total_professionals = ProfessionalProfile.objects.count()

    pending_appointments = Appointment.objects.filter(
        status=Appointment.STATUS_PENDING
    ).count()

    confirmed_appointments = Appointment.objects.filter(
        status=Appointment.STATUS_CONFIRMED
    ).count()

    cancelled_appointments = Appointment.objects.filter(
        status=Appointment.STATUS_CANCELLED
    ).count()

    completed_appointments = Appointment.objects.filter(
        status=Appointment.STATUS_COMPLETED
    ).count()

    # Ultimi appuntamenti inseriti, utili per un riepilogo rapido.
    recent_appointments = (
        Appointment.objects.select_related("service", "customer", "operator")
        .order_by("-created_at")[:5]
    )

    context = {
        "total_services": total_services,
        "active_services": active_services,
        "total_customers": total_customers,
        "total_professionals": total_professionals,
        "pending_appointments": pending_appointments,
        "confirmed_appointments": confirmed_appointments,
        "cancelled_appointments": cancelled_appointments,
        "completed_appointments": completed_appointments,
        "recent_appointments": recent_appointments,
    }

    return render(request, "core/admin_dashboard.html", context)