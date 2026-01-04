from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render


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
    return render(request, "account.html")
