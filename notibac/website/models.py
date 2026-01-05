import datetime
import re

from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.db import models


def validate_canadian_phone(value):
    """Validate Canadian phone number format: +1XXXXXXXXXX"""
    pattern = r"^\+1\d{10}$"
    if not re.match(pattern, value):
        raise ValidationError("Entrez un numéro de téléphone canadien valide.")


class PhoneNumber(models.Model):
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="phone_numbers"
    )
    phone_number = models.CharField(max_length=15, validators=[validate_canadian_phone])
    is_primary = models.BooleanField(default=False)
    is_verified = models.BooleanField(default=False)
    verification_code = models.CharField(max_length=6, blank=True, null=True)
    code_sent_at = models.DateTimeField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("user", "phone_number")
        ordering = ["-is_primary", "-created_at"]

    def __str__(self):
        status = "Principal" if self.is_primary else "Secondaire"
        verified = "Vérifié" if self.is_verified else "Non vérifié"
        return f"{self.phone_number} ({status}, {verified})"


class Sector(models.Model):
    """Waste collection sector definition."""

    code = models.CharField(max_length=20, unique=True)  # "01", "14a", "24-25-26"
    name = models.CharField(max_length=100)  # "Secteur 01", "Secteur 14A - Granada"

    class Meta:
        ordering = ["code"]

    def __str__(self):
        return self.name


class Calendar(models.Model):
    """Collection calendar for a sector/year/compost combination."""

    sector = models.ForeignKey(Sector, on_delete=models.CASCADE, related_name="calendars")
    year = models.IntegerField()
    has_compost = models.BooleanField()

    class Meta:
        unique_together = ("sector", "year", "has_compost")
        ordering = ["sector__code", "year", "-has_compost"]

    def __str__(self):
        compost_str = "avec compost" if self.has_compost else "sans compost"
        return f"{self.sector.name} ({self.year}) - {compost_str}"


class CollectionDate(models.Model):
    """Individual collection event."""

    COLLECTION_TYPES = [
        ("garbage", "Déchets"),
        ("recycling", "Récupération"),
        ("compost", "Compost"),
        ("yard_waste", "Résidus verts"),
        ("christmas_trees", "Arbres de Noël"),
        ("bulky_waste", "Encombrants"),
    ]

    calendar = models.ForeignKey(
        Calendar, on_delete=models.CASCADE, related_name="collection_dates"
    )
    collection_type = models.CharField(max_length=20, choices=COLLECTION_TYPES)
    date = models.DateField()

    class Meta:
        unique_together = ("calendar", "collection_type", "date")
        ordering = ["date", "collection_type"]
        indexes = [models.Index(fields=["date"])]

    def __str__(self):
        return f"{self.get_collection_type_display()} - {self.date}"


class NotificationPreference(models.Model):
    """User notification settings for a specific calendar."""

    TIMING_CHOICES = [
        ("day_before", "La veille"),
        ("day_of", "Le jour même"),
    ]

    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="notification_preferences"
    )
    calendar = models.ForeignKey(
        Calendar, on_delete=models.CASCADE, related_name="notification_preferences"
    )
    phone_number = models.ForeignKey(
        PhoneNumber, on_delete=models.CASCADE, related_name="notification_preferences"
    )
    timing = models.CharField(
        max_length=20, choices=TIMING_CHOICES, default="day_before"
    )
    notification_time = models.TimeField(default=datetime.time(18, 0))

    # Per-type toggles (all True by default)
    notify_garbage = models.BooleanField(default=True)
    notify_recycling = models.BooleanField(default=True)
    notify_compost = models.BooleanField(default=True)
    notify_yard_waste = models.BooleanField(default=True)
    notify_christmas_trees = models.BooleanField(default=True)
    notify_bulky_waste = models.BooleanField(default=True)

    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.user.email} - {self.calendar}"

    def get_enabled_types(self):
        """Return list of enabled collection types."""
        types = []
        if self.notify_garbage:
            types.append("garbage")
        if self.notify_recycling:
            types.append("recycling")
        if self.notify_compost:
            types.append("compost")
        if self.notify_yard_waste:
            types.append("yard_waste")
        if self.notify_christmas_trees:
            types.append("christmas_trees")
        if self.notify_bulky_waste:
            types.append("bulky_waste")
        return types
