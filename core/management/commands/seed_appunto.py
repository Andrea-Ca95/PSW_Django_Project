from datetime import date, time, timedelta

from django.contrib.auth.models import Group, Permission, User
from django.core.management.base import BaseCommand

from core.models import (
    Appointment,
    CustomerProfile,
    ProfessionalProfile,
    Service,
    ServiceCategory,
)


class Command(BaseCommand):
    help = "Crea gruppi, utenti demo e dati iniziali per Appunto"

    def handle(self, *args, **options):
        self.create_groups()
        self.create_users()
        self.create_services()
        self.create_appointments()

        self.stdout.write(self.style.SUCCESS("Dati iniziali creati correttamente."))

    def create_groups(self):
        # Gruppi principali usati per distinguere i ruoli nella web app.
        admin_group, _ = Group.objects.get_or_create(name="Admin")
        professional_group, _ = Group.objects.get_or_create(name="Professionista")
        customer_group, _ = Group.objects.get_or_create(name="Cliente")

        permissions = Permission.objects.filter(content_type__app_label="core")

        customer_permissions = permissions.filter(
            codename__in=["can_access_customer_area"]
        )
        professional_permissions = permissions.filter(
            codename__in=[
                "can_access_professional_area",
                "can_manage_appointments",
            ]
        )
        admin_permissions = permissions.filter(
            codename__in=[
                "can_manage_services",
                "can_manage_appointments",
                "can_access_customer_area",
                "can_access_professional_area",
            ]
        )

        customer_group.permissions.set(customer_permissions)
        professional_group.permissions.set(professional_permissions)
        admin_group.permissions.set(admin_permissions)

    def create_demo_user(
        self,
        username,
        password,
        first_name,
        last_name,
        email,
        group_name,
        is_staff=False,
        is_superuser=False,
    ):
        # Password aggiornata a ogni esecuzione per tenere credenziali demo coerenti.
        user, _ = User.objects.get_or_create(username=username)

        user.first_name = first_name
        user.last_name = last_name
        user.email = email
        user.is_staff = is_staff
        user.is_superuser = is_superuser
        user.set_password(password)
        user.save()

        group = Group.objects.get(name=group_name)
        user.groups.set([group])

        return user

    def create_users(self):
        # Due admin, due professionisti e due clienti: requisito minimo del progetto.
        self.admin1 = self.create_demo_user(
            username="admin1",
            password="Admin2026!",
            first_name="Mario",
            last_name="Rossi",
            email="admin1@appunto.local",
            group_name="Admin",
            is_staff=True,
            is_superuser=True,
        )
        self.admin2 = self.create_demo_user(
            username="admin2",
            password="Admin2026!",
            first_name="Laura",
            last_name="Bianchi",
            email="admin2@appunto.local",
            group_name="Admin",
            is_staff=True,
            is_superuser=True,
        )

        self.professional1 = self.create_demo_user(
            username="professionista1",
            password="Professionista2026!",
            first_name="Giulia",
            last_name="Ferrari",
            email="professionista1@appunto.local",
            group_name="Professionista",
        )
        self.professional2 = self.create_demo_user(
            username="professionista2",
            password="Professionista2026!",
            first_name="Luca",
            last_name="Romano",
            email="professionista2@appunto.local",
            group_name="Professionista",
        )

        self.customer1 = self.create_demo_user(
            username="cliente1",
            password="Cliente2026!",
            first_name="Anna",
            last_name="Verdi",
            email="cliente1@appunto.local",
            group_name="Cliente",
        )
        self.customer2 = self.create_demo_user(
            username="cliente2",
            password="Cliente2026!",
            first_name="Paolo",
            last_name="Neri",
            email="cliente2@appunto.local",
            group_name="Cliente",
        )

        ProfessionalProfile.objects.update_or_create(
            user=self.professional1,
            defaults={
                "phone": "0100000001",
                "bio": "Professionista specializzata in consulenze amministrative e documentali.",
            },
        )
        ProfessionalProfile.objects.update_or_create(
            user=self.professional2,
            defaults={
                "phone": "0100000002",
                "bio": "Professionista specializzato in consulenze tecniche e organizzative.",
            },
        )

        CustomerProfile.objects.update_or_create(
            user=self.customer1,
            defaults={"phone": "3330000001"},
        )
        CustomerProfile.objects.update_or_create(
            user=self.customer2,
            defaults={"phone": "3330000002"},
        )

    def create_services(self):
        consulenza, _ = ServiceCategory.objects.update_or_create(
            name="Consulenza",
            defaults={
                "description": "Servizi di consulenza per pratiche e supporto professionale."
            },
        )
        documenti, _ = ServiceCategory.objects.update_or_create(
            name="Documenti",
            defaults={
                "description": "Servizi dedicati alla revisione e gestione documentale."
            },
        )
        supporto, _ = ServiceCategory.objects.update_or_create(
            name="Supporto tecnico",
            defaults={
                "description": "Servizi di supporto tecnico e organizzativo per clienti privati o aziende."
            },
        )

        self.service_admin, _ = Service.objects.update_or_create(
            name="Consulenza amministrativa",
            defaults={
                "category": consulenza,
                "description": "Appuntamento per ricevere supporto su pratiche amministrative generiche.",
                "duration_minutes": 45,
                "price": 40,
                "is_active": True,
            },
        )
        self.service_docs, _ = Service.objects.update_or_create(
            name="Revisione documenti",
            defaults={
                "category": documenti,
                "description": "Controllo e revisione di documentazione prima della consegna.",
                "duration_minutes": 30,
                "price": 25,
                "is_active": True,
            },
        )
        self.service_tech, _ = Service.objects.update_or_create(
            name="Consulenza tecnica",
            defaults={
                "category": supporto,
                "description": "Supporto per problemi tecnici, organizzativi o informatici di base.",
                "duration_minutes": 60,
                "price": 55,
                "is_active": True,
            },
        )
        self.service_info, _ = Service.objects.update_or_create(
            name="Appuntamento informativo",
            defaults={
                "category": consulenza,
                "description": "Primo incontro conoscitivo per capire il servizio più adatto.",
                "duration_minutes": 20,
                "price": 0,
                "is_active": True,
            },
        )

        # Ogni professionista viene associato solo ai servizi che può svolgere.
        self.professional1.professional_profile.services.set([
            self.service_admin,
            self.service_docs,
            self.service_info,
        ])
        self.professional2.professional_profile.services.set([
            self.service_tech,
            self.service_info,
        ])

    def create_appointments(self):
        tomorrow = date.today() + timedelta(days=1)
        next_week = date.today() + timedelta(days=7)

        # Appuntamenti futuri validi, utili per testare dashboard e permessi.
        Appointment.objects.update_or_create(
            operator=self.professional1,
            date=tomorrow,
            start_time=time(9, 30),
            defaults={
                "customer": self.customer1,
                "service": self.service_admin,
                "status": Appointment.STATUS_PENDING,
                "notes": "Richiesta informazioni su una pratica amministrativa.",
            },
        )

        Appointment.objects.update_or_create(
            operator=self.professional1,
            date=next_week,
            start_time=time(11, 0),
            defaults={
                "customer": self.customer2,
                "service": self.service_docs,
                "status": Appointment.STATUS_CONFIRMED,
                "notes": "Revisione documentazione già preparata dal cliente.",
            },
        )

        Appointment.objects.update_or_create(
            operator=self.professional2,
            date=tomorrow,
            start_time=time(15, 0),
            defaults={
                "customer": self.customer2,
                "service": self.service_tech,
                "status": Appointment.STATUS_PENDING,
                "notes": "Supporto tecnico generico.",
            },
        )