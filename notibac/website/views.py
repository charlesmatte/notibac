import random
import re
import string

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from .models import PhoneNumber

MAX_PHONE_NUMBERS = 3


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
    context = {
        "phone_numbers": phone_numbers,
        "phone_count": phone_numbers.count(),
        "max_phones": MAX_PHONE_NUMBERS,
        "can_add_phone": phone_numbers.count() < MAX_PHONE_NUMBERS,
    }
    return render(request, "account.html", context)


@login_required
@require_POST
def add_phone(request):
    phone_input = request.POST.get("phone_number", "").strip()
    normalized = normalize_canadian_phone(phone_input)

    if not normalized:
        messages.error(
            request, "Format invalide. Utilisez un numéro canadien (ex: 514-555-1234)."
        )
        return redirect("account")

    user_phones = request.user.phone_numbers.all()
    if user_phones.count() >= MAX_PHONE_NUMBERS:
        messages.error(request, f"Vous ne pouvez pas ajouter plus de {MAX_PHONE_NUMBERS} numéros.")
        return redirect("account")

    if user_phones.filter(phone_number=normalized).exists():
        messages.error(request, "Ce numéro est déjà enregistré.")
        return redirect("account")

    is_first_phone = not user_phones.exists()
    PhoneNumber.objects.create(
        user=request.user,
        phone_number=normalized,
        is_primary=is_first_phone,
        verification_code=generate_verification_code(),
    )

    messages.success(request, "Numéro ajouté. Un code de vérification sera envoyé.")
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
