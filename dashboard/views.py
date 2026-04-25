from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.shortcuts import redirect, render

from accounts.models import User
from accounts.permissions import ensure_department_assignment
from departments.models import Department
from knowledgebase.models import ReadHistory, Tutorial


@login_required
def home(request):
    if request.user.role == User.Role.ADMIN:
        return redirect("dashboard:admin-dashboard")
    if request.user.role == User.Role.EDITOR:
        return redirect("dashboard:editor-dashboard")
    return redirect("dashboard:user-dashboard")


@login_required
def admin_dashboard(request):
    if request.user.role != User.Role.ADMIN:
        raise PermissionDenied
    context = {
        "total_departments": Department.objects.count(),
        "total_users": User.objects.count(),
        "total_editors": User.objects.filter(role=User.Role.EDITOR).count(),
        "total_tutorials": Tutorial.objects.count(),
        "latest_tutorials": Tutorial.objects.select_related("department")
        .defer("content", "description", "video_file", "video_caption", "video_url")
        .order_by("-created_at")[:6],
    }
    return render(request, "dashboard/admin_dashboard.html", context)


@login_required
def editor_dashboard(request):
    if request.user.role != User.Role.EDITOR:
        raise PermissionDenied
    ensure_department_assignment(request.user)

    dept = request.user.department
    tutorials_qs = Tutorial.objects.filter(department=dept).select_related("created_by").defer(
        "content",
        "description",
        "video_file",
        "video_caption",
        "video_url",
    )
    users_qs = User.objects.filter(department=dept, role=User.Role.USER)
    context = {
        "department": dept,
        "total_tutorials": tutorials_qs.count(),
        "total_users": users_qs.count(),
        "recent_tutorials": tutorials_qs.order_by("-created_at")[:8],
    }
    return render(request, "dashboard/editor_dashboard.html", context)


@login_required
def user_dashboard(request):
    if request.user.role != User.Role.USER:
        raise PermissionDenied
    ensure_department_assignment(request.user)

    tutorials = Tutorial.objects.select_related("department", "created_by").defer(
        "content",
        "description",
        "video_file",
        "video_caption",
        "video_url",
    ).filter(
        department=request.user.department,
        is_published=True,
    ).order_by("-updated_at")
    recent_history = (
        ReadHistory.objects.select_related("tutorial", "tutorial__department").defer(
            "tutorial__content",
            "tutorial__description",
            "tutorial__video_file",
            "tutorial__video_caption",
            "tutorial__video_url",
        )
        .filter(user=request.user)
        .order_by("-read_at")[:8]
    )
    context = {
        "tutorials": tutorials[:10],
        "recent_history": recent_history,
    }
    return render(request, "dashboard/user_dashboard.html", context)

# Create your views here.
