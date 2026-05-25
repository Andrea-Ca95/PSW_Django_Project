from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.utils import timezone

from .models import Appointment


class CustomerSignUpForm(UserCreationForm):
    # Campi aggiuntivi rispetto alla registrazione standard di Django.
    first_name = forms.CharField(max_length=150, required=True, label="Nome")
    last_name = forms.CharField(max_length=150, required=True, label="Cognome")
    email = forms.EmailField(required=True, label="Email")
    phone = forms.CharField(max_length=30, required=False, label="Telefono")

    class Meta:
        model = User
        fields = (
            "first_name",
            "last_name",
            "email",
            "phone",
            "username",
            "password1",
            "password2",
        )

    def clean_email(self):
        # Evita registrazioni duplicate con la stessa email.
        email = self.cleaned_data["email"]

        if User.objects.filter(email=email).exists():
            raise forms.ValidationError("Esiste già un utente con questa email.")

        return email


class ProfessionalChoiceField(forms.ModelChoiceField):
    def label_from_instance(self, obj):
        # Mostra nome e cognome del professionista invece del solo username.
        full_name = obj.get_full_name()
        return full_name if full_name else obj.username


class AppointmentCreateForm(forms.ModelForm):
    operator = ProfessionalChoiceField(
        queryset=User.objects.none(),
        label="Professionista",
        empty_label="Seleziona un professionista",
    )

    date = forms.DateField(
        label="Data",
        widget=forms.DateInput(attrs={"type": "date"}),
    )

    start_time = forms.TimeField(
        label="Ora",
        widget=forms.TimeInput(attrs={"type": "time"}),
    )

    class Meta:
        model = Appointment
        fields = ("operator", "date", "start_time", "notes")
        labels = {
            "notes": "Note",
        }
        widgets = {
            "notes": forms.Textarea(attrs={"rows": 4}),
        }

    def __init__(self, *args, **kwargs):
        # Il servizio arriva dalla view e serve per filtrare i professionisti.
        self.service = kwargs.pop("service", None)
        super().__init__(*args, **kwargs)

        if self.service:
            self.fields["operator"].queryset = User.objects.filter(
                professional_profile__services=self.service
            ).order_by("last_name", "first_name").distinct()

    def clean(self):
        cleaned_data = super().clean()

        operator = cleaned_data.get("operator")
        date = cleaned_data.get("date")
        start_time = cleaned_data.get("start_time")

        if not date or not start_time:
            return cleaned_data

        today = timezone.localdate()
        current_time = timezone.localtime().time()

        # Controllo lato form per evitare appuntamenti nel passato.
        if date < today:
            raise forms.ValidationError("Non puoi prenotare un appuntamento nel passato.")

        if date == today and start_time <= current_time:
            raise forms.ValidationError("Non puoi prenotare un orario già passato.")

        if operator:
            busy_slot = Appointment.objects.filter(
                operator=operator,
                date=date,
                start_time=start_time,
                status__in=[
                    Appointment.STATUS_PENDING,
                    Appointment.STATUS_CONFIRMED,
                ],
            ).exists()

            # Evita doppie prenotazioni attive sullo stesso professionista.
            if busy_slot:
                raise forms.ValidationError(
                    "Il professionista è già occupato in questo giorno e orario."
                )

        return cleaned_data