from django.urls import path

from . import views

urlpatterns = [
    path("", views.home, name="home"),
    path("about/", views.about, name="about"),
    path("account/", views.account, name="account"),
    path("account/phone/add/", views.add_phone, name="add_phone"),
    path(
        "account/phone/<int:phone_id>/delete/", views.delete_phone, name="delete_phone"
    ),
    path(
        "account/phone/<int:phone_id>/set-primary/",
        views.set_primary_phone,
        name="set_primary_phone",
    ),
]
