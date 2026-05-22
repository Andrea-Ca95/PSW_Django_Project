from django.contrib import admin

from .models import (
    Appointment,
    CustomerProfile,
    ProfessionalProfile,
    Service,
    ServiceCategory,
)


class ServiceInline(admin.TabularInline):
    model = Service
    extra = 0
    fields = ("name", "duration_minutes", "price", "is_active")


@admin.register(ServiceCategory)
class ServiceCategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "service_count")
    search_fields = ("name", "description")
    inlines = [ServiceInline]

    def service_count(self, obj):
        # Mostra quanti servizi appartengono alla categoria.
        return obj.services.count()

    service_count.short_description = "Numero servizi"


@admin.register(Service)
class ServiceAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "category",
        "duration_minutes",
        "price",
        "is_active",
        "created_at",
    )
    list_filter = ("category", "is_active")
    search_fields = ("name", "description", "category__name")
    list_editable = ("is_active",)
    readonly_fields = ("created_at",)
    ordering = ("name",)

    fieldsets = (
        ("Informazioni servizio", {
            "fields": ("name", "description", "category")
        }),
        ("Dettagli prenotazione", {
            "fields": ("duration_minutes", "price", "is_active")
        }),
        ("Dati sistema", {
            "fields": ("created_at",)
        }),
    )


@admin.register(ProfessionalProfile)
class ProfessionalProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "phone", "services_list")
    search_fields = (
        "user__username",
        "user__first_name",
        "user__last_name",
        "user__email",
        "phone",
    )
    list_filter = ("services",)
    filter_horizontal = ("services",)

    def services_list(self, obj):
        # Rende leggibili i servizi associati al professionista.
        return ", ".join(service.name for service in obj.services.all())

    services_list.short_description = "Servizi"


@admin.register(CustomerProfile)
class CustomerProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "phone")
    search_fields = (
        "user__username",
        "user__first_name",
        "user__last_name",
        "user__email",
        "phone",
    )


@admin.register(Appointment)
class AppointmentAdmin(admin.ModelAdmin):
    list_display = (
        "service",
        "customer",
        "operator",
        "date",
        "start_time",
        "status",
        "created_at",
    )
    list_filter = ("status", "date", "service")
    search_fields = (
        "service__name",
        "customer__username",
        "customer__first_name",
        "customer__last_name",
        "operator__username",
        "operator__first_name",
        "operator__last_name",
    )
    readonly_fields = ("created_at", "updated_at")
    date_hierarchy = "date"
    ordering = ("date", "start_time")
    actions = ("mark_as_confirmed", "mark_as_completed", "mark_as_cancelled")

    fieldsets = (
        ("Prenotazione", {
            "fields": ("customer", "operator", "service")
        }),
        ("Data e orario", {
            "fields": ("date", "start_time")
        }),
        ("Stato e note", {
            "fields": ("status", "notes")
        }),
        ("Dati sistema", {
            "fields": ("created_at", "updated_at")
        }),
    )

    @admin.action(description="Conferma gli appuntamenti selezionati")
    def mark_as_confirmed(self, request, queryset):
        # Aggiorna rapidamente gli appuntamenti ancora da confermare.
        queryset.filter(status=Appointment.STATUS_PENDING).update(
            status=Appointment.STATUS_CONFIRMED
        )

    @admin.action(description="Segna come completati")
    def mark_as_completed(self, request, queryset):
        # Permette all'admin di chiudere appuntamenti già gestiti.
        queryset.exclude(status=Appointment.STATUS_CANCELLED).update(
            status=Appointment.STATUS_COMPLETED
        )

    @admin.action(description="Annulla gli appuntamenti selezionati")
    def mark_as_cancelled(self, request, queryset):
        # Evita di annullare appuntamenti già completati.
        queryset.exclude(status=Appointment.STATUS_COMPLETED).update(
            status=Appointment.STATUS_CANCELLED
        )