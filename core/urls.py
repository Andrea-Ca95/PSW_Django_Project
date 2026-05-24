from django.urls import path

from . import views


# URL gestiti dall'app core.
urlpatterns = [
    # Home pubblica di Appunto.
    path("", views.index, name="index"),
]