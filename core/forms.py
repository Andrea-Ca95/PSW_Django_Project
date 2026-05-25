from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User


class CustomerSignUpForm(UserCreationForm):
    # Campi aggiuntivi rispetto alla registrazione base di Django.
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