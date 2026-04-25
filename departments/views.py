from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.translation import gettext_lazy as _

from accounts.models import User
from departments.forms import DepartmentForm
from departments.models import Department


def _ensure_admin(user: User) -> None:
    if not user.is_authenticated or user.role != User.Role.ADMIN:
        raise PermissionDenied


@login_required
def department_list(request):
    _ensure_admin(request.user)
    departments = Department.objects.all()
    return render(
        request,
        "departments/department_list.html",
        {"departments": departments},
    )


@login_required
def department_create(request):
    _ensure_admin(request.user)
    form = DepartmentForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, _("Department created successfully."))
        return redirect("departments:list")
    return render(request, "departments/department_form.html", {"form": form, "is_create": True})


@login_required
def department_update(request, pk: int):
    _ensure_admin(request.user)
    department = get_object_or_404(Department, pk=pk)
    form = DepartmentForm(request.POST or None, instance=department)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, _("Department updated successfully."))
        return redirect("departments:list")
    return render(request, "departments/department_form.html", {"form": form, "is_create": False})


@login_required
def department_delete(request, pk: int):
    _ensure_admin(request.user)
    department = get_object_or_404(Department, pk=pk)
    if request.method == "POST":
        department.delete()
        messages.success(request, _("Department deleted successfully."))
        return redirect("departments:list")
    return render(
        request,
        "departments/department_confirm_delete.html",
        {"department": department},
    )

# Create your views here.
