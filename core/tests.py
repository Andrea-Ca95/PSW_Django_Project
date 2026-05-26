from datetime import timedelta

from django.contrib.auth.models import Group, Permission, User
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from .models import (
    Appointment,
    CustomerProfile,
    ProfessionalProfile,
    Service,
    ServiceCategory,
)


class AppuntoBaseTestCase(TestCase):
    def setUp(self):
        # Gruppi usati dai test per simulare i ruoli dell'applicazione.
        self.customer_group = Group.objects.create(name="Cliente")
        self.professional_group = Group.objects.create(name="Professionista")

        customer_permission = Permission.objects.get(
            codename="can_access_customer_area"
        )
        professional_permission = Permission.objects.get(
            codename="can_access_professional_area"
        )
        manage_appointments_permission = Permission.objects.get(
            codename="can_manage_appointments"
        )

        self.customer_group.permissions.add(customer_permission)
        self.professional_group.permissions.add(
            professional_permission,
            manage_appointments_permission,
        )

        # Utente cliente.
        self.customer = User.objects.create_user(
            username="cliente_test",
            password="ClienteTest2026!",
            first_name="Cliente",
            last_name="Test",
            email="cliente_test@appunto.local",
        )
        self.customer.groups.add(self.customer_group)

        CustomerProfile.objects.create(
            user=self.customer,
            phone="3330000000",
        )

        # Utente professionista.
        self.professional = User.objects.create_user(
            username="professionista_test",
            password="ProfessionistaTest2026!",
            first_name="Professionista",
            last_name="Test",
            email="professionista_test@appunto.local",
        )
        self.professional.groups.add(self.professional_group)

        self.category = ServiceCategory.objects.create(
            name="Consulenza",
            description="Categoria di test.",
        )

        self.service = Service.objects.create(
            category=self.category,
            name="Consulenza amministrativa",
            description="Servizio di test per pratiche amministrative.",
            duration_minutes=45,
            price=40,
            is_active=True,
        )

        self.professional_profile = ProfessionalProfile.objects.create(
            user=self.professional,
            phone="0100000000",
            bio="Profilo professionista di test.",
        )
        self.professional_profile.services.add(self.service)

        # Appuntamento futuro usato nei test delle dashboard.
        self.future_date = timezone.localdate() + timedelta(days=7)

        self.appointment = Appointment.objects.create(
            customer=self.customer,
            operator=self.professional,
            service=self.service,
            date=self.future_date,
            start_time="10:30",
            status=Appointment.STATUS_PENDING,
            notes="Appuntamento di test.",
        )


class PublicPagesTests(AppuntoBaseTestCase):
    def test_home_page_loads(self):
        # La home deve essere pubblica e raggiungibile senza login.
        response = self.client.get(reverse("index"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Appunto")
        self.assertContains(response, "Visite in questa sessione")

    def test_service_list_loads(self):
        # La lista servizi deve mostrare i servizi attivi.
        response = self.client.get(reverse("service-list"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.service.name)

    def test_service_detail_loads(self):
        # Il dettaglio servizio deve mostrare dati del servizio e professionisti associati.
        response = self.client.get(
            reverse("service-detail", args=[self.service.id])
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.service.name)
        self.assertContains(response, self.professional.get_full_name())


class PermissionTests(AppuntoBaseTestCase):
    def test_customer_can_access_customer_dashboard(self):
        # Un cliente autenticato deve accedere alla propria area cliente.
        self.client.login(
            username="cliente_test",
            password="ClienteTest2026!",
        )

        response = self.client.get(reverse("customer-dashboard"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Area cliente")
        self.assertContains(response, self.service.name)

    def test_customer_cannot_access_professional_dashboard(self):
        # Un cliente non deve poter accedere all'area professionista.
        self.client.login(
            username="cliente_test",
            password="ClienteTest2026!",
        )

        response = self.client.get(reverse("professional-dashboard"))

        self.assertEqual(response.status_code, 403)

    def test_professional_can_access_professional_dashboard(self):
        # Un professionista autenticato deve vedere gli appuntamenti assegnati.
        self.client.login(
            username="professionista_test",
            password="ProfessionistaTest2026!",
        )

        response = self.client.get(reverse("professional-dashboard"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Area professionista")
        self.assertContains(response, self.service.name)


class AppointmentTests(AppuntoBaseTestCase):
    def test_customer_can_create_appointment(self):
        # Il cliente può creare una nuova prenotazione su un servizio attivo.
        self.client.login(
            username="cliente_test",
            password="ClienteTest2026!",
        )

        new_date = timezone.localdate() + timedelta(days=10)

        response = self.client.post(
            reverse("appointment-create", args=[self.service.id]),
            {
                "operator": self.professional.id,
                "date": new_date,
                "start_time": "15:00",
                "notes": "Nuova prenotazione di test.",
            },
        )

        self.assertEqual(response.status_code, 302)

        appointment_exists = Appointment.objects.filter(
            customer=self.customer,
            operator=self.professional,
            service=self.service,
            date=new_date,
            start_time="15:00",
        ).exists()

        self.assertTrue(appointment_exists)

    def test_customer_can_cancel_own_appointment(self):
        # Il cliente può annullare solo una propria prenotazione ancora gestibile.
        self.client.login(
            username="cliente_test",
            password="ClienteTest2026!",
        )

        response = self.client.post(
            reverse("appointment-cancel", args=[self.appointment.id])
        )

        self.assertEqual(response.status_code, 302)

        self.appointment.refresh_from_db()
        self.assertEqual(
            self.appointment.status,
            Appointment.STATUS_CANCELLED,
        )

    def test_professional_can_confirm_appointment(self):
        # Il professionista può confermare un appuntamento assegnato.
        self.client.login(
            username="professionista_test",
            password="ProfessionistaTest2026!",
        )

        response = self.client.post(
            reverse(
                "professional-update-appointment-status",
                args=[self.appointment.id],
            ),
            {
                "action": "confirm",
            },
        )

        self.assertEqual(response.status_code, 302)

        self.appointment.refresh_from_db()
        self.assertEqual(
            self.appointment.status,
            Appointment.STATUS_CONFIRMED,
        )