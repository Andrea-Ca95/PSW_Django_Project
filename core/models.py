from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.db import models
from django.urls import reverse
from django.utils import timezone


class ServiceCategory(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(max_length=500, blank=True)

    class Meta:
        ordering = ["name"]
        verbose_name = "Categoria servizio"
        verbose_name_plural = "Categorie servizi"

    def __str__(self):
        return self.name


class Service(models.Model):
    category = models.ForeignKey(
        ServiceCategory,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="services",
    )
    name = models.CharField(max_length=150, unique=True)
    description = models.TextField(max_length=1000)
    duration_minutes = models.PositiveIntegerField(
        validators=[MinValueValidator(15)],
        help_text="Durata minima: 15 minuti",
    )
    price = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        validators=[MinValueValidator(0)],
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["name"]
        verbose_name = "Servizio"
        verbose_name_plural = "Servizi"
        permissions = (
            ("can_manage_services", "Can manage services"),
        )

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        # Verrà usato nei link alla pagina dettaglio del servizio.
        return reverse("service-detail", args=[str(self.id)])


class ProfessionalProfile(models.Model):
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name="professional_profile",
    )
    phone = models.CharField(max_length=30, blank=True)
    bio = models.TextField(max_length=800, blank=True)
    services = models.ManyToManyField(
        Service,
        related_name="professionals",
        blank=True,
    )

    class Meta:
        ordering = ["user__last_name", "user__first_name"]
        verbose_name = "Profilo professionista"
        verbose_name_plural = "Profili professionisti"

    def __str__(self):
        full_name = self.user.get_full_name()
        return full_name if full_name else self.user.username


class CustomerProfile(models.Model):
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name="customer_profile",
    )
    phone = models.CharField(max_length=30, blank=True)

    class Meta:
        ordering = ["user__last_name", "user__first_name"]
        verbose_name = "Profilo cliente"
        verbose_name_plural = "Profili clienti"

    def __str__(self):
        full_name = self.user.get_full_name()
        return full_name if full_name else self.user.username


class Appointment(models.Model):
    STATUS_PENDING = "pending"
    STATUS_CONFIRMED = "confirmed"
    STATUS_CANCELLED = "cancelled"
    STATUS_COMPLETED = "completed"

    STATUS_CHOICES = (
        (STATUS_PENDING, "In attesa"),
        (STATUS_CONFIRMED, "Confermato"),
        (STATUS_CANCELLED, "Annullato"),
        (STATUS_COMPLETED, "Completato"),
    )

    customer = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="customer_appointments",
    )
    operator = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="professional_appointments",
    )
    service = models.ForeignKey(
        Service,
        on_delete=models.RESTRICT,
        related_name="appointments",
    )
    date = models.DateField()
    start_time = models.TimeField()
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default=STATUS_PENDING,
    )
    notes = models.TextField(max_length=500, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["date", "start_time"]
        verbose_name = "Appuntamento"
        verbose_name_plural = "Appuntamenti"
        constraints = [
            models.UniqueConstraint(
                fields=["operator", "date", "start_time"],
                condition=models.Q(status__in=["pending", "confirmed"]),
                name="unique_active_operator_slot",
            )
        ]
        permissions = (
            ("can_access_customer_area", "Can access customer area"),
            ("can_access_professional_area", "Can access professional area"),
            ("can_manage_appointments", "Can manage appointments"),
        )

    def __str__(self):
        return f"{self.service} - {self.customer} - {self.date} {self.start_time}"

    def clean(self):
        # Evita prenotazioni attive nel passato.
        today = timezone.localdate()
        current_time = timezone.localtime().time()

        is_active_booking = self.status in [
            self.STATUS_PENDING,
            self.STATUS_CONFIRMED,
        ]

        if is_active_booking:
            if self.date < today:
                raise ValidationError({
                    "date": "Non puoi prenotare un appuntamento nel passato."
                })

            if self.date == today and self.start_time <= current_time:
                raise ValidationError({
                    "start_time": "Non puoi prenotare un orario già passato."
                })

        # Un servizio disattivato non deve essere prenotabile.
        if self.service and not self.service.is_active:
            raise ValidationError({
                "service": "Questo servizio non è attualmente prenotabile."
            })

        # Il professionista scelto deve offrire il servizio selezionato.
        if self.operator_id and self.service_id:
            if not hasattr(self.operator, "professional_profile"):
                raise ValidationError({
                    "operator": "L'utente selezionato non è un professionista."
                })

            offers_service = self.operator.professional_profile.services.filter(
                id=self.service_id
            ).exists()

            if not offers_service:
                raise ValidationError({
                    "operator": "Il professionista selezionato non offre questo servizio."
                })

    def save(self, *args, **kwargs):
        # Forza le validazioni anche quando il dato viene salvato da codice.
        self.full_clean()
        super().save(*args, **kwargs)

    @property
    def is_past(self):
        today = timezone.localdate()
        current_time = timezone.localtime().time()

        return self.date < today or (
            self.date == today and self.start_time < current_time
        )

    def can_be_cancelled_by_customer(self):
        # Il cliente può annullare solo appuntamenti ancora gestibili.
        return self.status in [
            self.STATUS_PENDING,
            self.STATUS_CONFIRMED,
        ] and not self.is_past

    def get_absolute_url(self):
        # Verrà usato nella pagina dettaglio appuntamento.
        return reverse("appointment-detail", args=[str(self.id)])