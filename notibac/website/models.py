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
