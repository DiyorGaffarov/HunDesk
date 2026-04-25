from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.translation import gettext_lazy as _

from accounts.models import User
from departments.forms import DepartmentForm
from departments.models import Department

DEPARTMENTS_PER_PAGE = 20


def _ensure_admin(user: User) -> None:
    if not user.is_authenticated or user.role != User.Role.ADMIN:
        raise PermissionDenied


@login_required
def department_list(request):
    _ensure_admin(request.user)
    departments = Department.objects.only("id", "name", "description", "created_at").order_by("name")
    page_obj = Paginator(departments, DEPARTMENTS_PER_PAGE).get_page(request.GET.get("page"))
    return render(
        request,
        "departments/department_list.html",
        {"departments": page_obj, "page_obj": page_obj},
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
        related_users_count = department.users.filter(
            role__in=[User.Role.EDITOR, User.Role.USER]
        ).count()
        related_tutorials_count = department.tutorials.count()
        if related_users_count or related_tutorials_count:
            messages.error(
                request,
                _(
                    "Cannot delete this department because it still has %(users)d users and %(tutorials)d tutorials. Reassign them first."
                )
                % {
                    "users": related_users_count,
                    "tutorials": related_tutorials_count,
                },
            )
            return redirect("departments:list")

        department.delete()
        messages.success(request, _("Department deleted successfully."))
        return redirect("departments:list")
    return render(
        request,
        "departments/department_confirm_delete.html",
        {"department": department},
    )

# Create your views here.
