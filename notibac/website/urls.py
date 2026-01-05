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
    path(
        "account/phone/<int:phone_id>/verify/",
        views.verify_phone,
        name="verify_phone",
    ),
    path(
        "account/phone/<int:phone_id>/resend-code/",
        views.resend_code,
        name="resend_code",
    ),
    # Notification preferences
    path("notifications/", views.notifications_list, name="notifications_list"),
    path("notifications/add/", views.notification_add, name="notification_add"),
    path(
        "notifications/<int:pk>/edit/",
        views.notification_edit,
        name="notification_edit",
    ),
    path(
        "notifications/<int:pk>/delete/",
        views.notification_delete,
        name="notification_delete",
    ),
    path(
        "notifications/<int:pk>/toggle/",
        views.notification_toggle,
        name="notification_toggle",
    ),
]
