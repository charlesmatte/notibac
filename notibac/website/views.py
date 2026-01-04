import random
import re
import string
from datetime import timedelta

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST

from .models import PhoneNumber
from .services import send_verification_sms

MAX_PHONE_NUMBERS = 3
CODE_EXPIRATION_MINUTES = 10
RESEND_COOLDOWN_SECONDS = 60


def normalize_canadian_phone(phone):
    """Normalize various Canadian phone formats to +1XXXXXXXXXX"""
    digits = re.sub(r"\D", "", phone)
    if len(digits) == 10:
        return f"+1{digits}"
    elif len(digits) == 11 and digits.startswith("1"):
        return f"+{digits}"
    return None


def generate_verification_code():
    """Generate a 6-digit verification code"""
    return "".join(random.choices(string.digits, k=6))


def home(request):
    return render(request, "home.html")


def about(request):
    return render(request, "about.html")


@login_required
def account(request):
    if request.method == "POST":
        user = request.user
        user.first_name = request.POST.get("first_name", "").strip()
        user.last_name = request.POST.get("last_name", "").strip()
        user.save()
        messages.success(request, "Vos informations ont été mises à jour.")
        return redirect("account")

    phone_numbers = request.user.phone_numbers.all()
    verify_phone_id = request.session.pop("verify_phone_id", None)
    context = {
        "phone_numbers": phone_numbers,
        "phone_count": phone_numbers.count(),
        "max_phones": MAX_PHONE_NUMBERS,
        "can_add_phone": phone_numbers.count() < MAX_PHONE_NUMBERS,
        "verify_phone_id": verify_phone_id,
    }
    return render(request, "account.html", context)


def _validate_new_phone(request, phone_input):
    """Validate phone input for adding a new phone number.

    Returns (normalized_phone, user_phones) on success, or (None, None) if validation fails.
    Sets appropriate error message on failure.
    """
    normalized = normalize_canadian_phone(phone_input)
    if not normalized:
        messages.error(
            request, "Format invalide. Utilisez un numéro canadien (ex: 514-555-1234)."
        )
        return None, None

    user_phones = request.user.phone_numbers.all()
    if user_phones.count() >= MAX_PHONE_NUMBERS:
        messages.error(request, f"Vous ne pouvez pas ajouter plus de {MAX_PHONE_NUMBERS} numéros.")
        return None, None

    if user_phones.filter(phone_number=normalized).exists():
        messages.error(request, "Ce numéro est déjà enregistré.")
        return None, None

    return normalized, user_phones


def _create_phone_with_verification(user, normalized, user_phones):
    """Create a new phone number record with verification code."""
    code = generate_verification_code()
    phone = PhoneNumber.objects.create(
        user=user,
        phone_number=normalized,
        is_primary=not user_phones.exists(),
        verification_code=code,
        code_sent_at=timezone.now(),
    )
    return phone, code


@login_required
@require_POST
def add_phone(request):
    phone_input = request.POST.get("phone_number", "").strip()

    normalized, user_phones = _validate_new_phone(request, phone_input)
    if not normalized:
        return redirect("account")

    phone, code = _create_phone_with_verification(request.user, normalized, user_phones)

    if send_verification_sms(normalized, code):
        messages.success(request, "Numéro ajouté. Un code de vérification a été envoyé par SMS.")
    else:
        messages.warning(request, "Numéro ajouté mais l'envoi du SMS a échoué. Réessayez plus tard.")

    request.session["verify_phone_id"] = phone.id
    return redirect("account")


@login_required
@require_POST
def delete_phone(request, phone_id):
    phone = get_object_or_404(PhoneNumber, id=phone_id, user=request.user)
    was_primary = phone.is_primary
    phone.delete()

    if was_primary:
        remaining = request.user.phone_numbers.first()
        if remaining:
            remaining.is_primary = True
            remaining.save()

    messages.success(request, "Numéro supprimé.")
    return redirect("account")


@login_required
@require_POST
def set_primary_phone(request, phone_id):
    phone = get_object_or_404(PhoneNumber, id=phone_id, user=request.user)

    request.user.phone_numbers.update(is_primary=False)
    phone.is_primary = True
    phone.save()

    messages.success(request, "Numéro principal mis à jour.")
    return redirect("account")


@login_required
@require_POST
def verify_phone(request, phone_id):
    phone = get_object_or_404(PhoneNumber, id=phone_id, user=request.user)

    if phone.is_verified:
        messages.info(request, "Ce numéro est déjà vérifié.")
        return redirect("account")

    code = request.POST.get("code", "").strip()

    if not phone.verification_code:
        messages.error(request, "Aucun code de vérification. Demandez un nouveau code.")
        return redirect("account")

    if phone.code_sent_at:
        expiration_time = phone.code_sent_at + timedelta(minutes=CODE_EXPIRATION_MINUTES)
        if timezone.now() > expiration_time:
            messages.error(request, "Le code a expiré. Demandez un nouveau code.")
            return redirect("account")

    if code == phone.verification_code:
        phone.is_verified = True
        phone.verification_code = None
        phone.code_sent_at = None
        phone.save()
        messages.success(request, "Numéro vérifié avec succès!")
    else:
        messages.error(request, "Code incorrect. Veuillez réessayer.")

    return redirect("account")


@login_required
@require_POST
def resend_code(request, phone_id):
    phone = get_object_or_404(PhoneNumber, id=phone_id, user=request.user)

    if phone.is_verified:
        messages.info(request, "Ce numéro est déjà vérifié.")
        return redirect("account")

    if phone.code_sent_at:
        cooldown_end = phone.code_sent_at + timedelta(seconds=RESEND_COOLDOWN_SECONDS)
        if timezone.now() < cooldown_end:
            remaining = (cooldown_end - timezone.now()).seconds
            messages.error(request, f"Veuillez attendre {remaining} secondes avant de renvoyer un code.")
            return redirect("account")

    code = generate_verification_code()
    phone.verification_code = code
    phone.code_sent_at = timezone.now()
    phone.save()

    if send_verification_sms(phone.phone_number, code):
        messages.success(request, "Un nouveau code a été envoyé.")
    else:
        messages.error(request, "Échec de l'envoi du SMS. Réessayez plus tard.")

    return redirect("account")
