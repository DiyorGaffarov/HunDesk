from django.contrib import messages
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.core.paginator import Paginator
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import translate_url
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.http import require_POST
from django.conf import settings
from django.utils.translation import check_for_language
from django.utils.translation import gettext_lazy as _

from accounts.forms import (
    AdminUserCreateForm,
    AdminUserUpdateForm,
    EditorManagedUserUpdateForm,
    EditorUserCreateForm,
    LoginForm,
    ProfileUpdateForm,
)
from accounts.models import User
from accounts.permissions import (
    can_editor_manage_user,
    can_editor_view_user,
    ensure_department_assignment,
)

USERS_PER_PAGE = 20


@require_POST
def set_language_view(request):
    lang_code = request.POST.get("language")
    next_url = request.POST.get("next") or request.META.get("HTTP_REFERER") or "/"

    if not url_has_allowed_host_and_scheme(
        url=next_url,
        allowed_hosts={request.get_host()},
        require_https=request.is_secure(),
    ):
        next_url = "/"

    if lang_code and check_for_language(lang_code):
        translated_next_url = translate_url(next_url, lang_code) or next_url
        response = redirect(translated_next_url)
        response.set_cookie(
            settings.LANGUAGE_COOKIE_NAME,
            lang_code,
            max_age=settings.LANGUAGE_COOKIE_AGE,
            path=settings.LANGUAGE_COOKIE_PATH,
            domain=settings.LANGUAGE_COOKIE_DOMAIN,
            secure=settings.LANGUAGE_COOKIE_SECURE,
            httponly=settings.LANGUAGE_COOKIE_HTTPONLY,
            samesite=settings.LANGUAGE_COOKIE_SAMESITE,
        )
        return response

    return redirect(next_url)


def login_view(request):
    if request.user.is_authenticated:
        return redirect("dashboard:home")
    form = LoginForm(request, data=request.POST or None)
    if request.method == "POST" and form.is_valid():
        login(request, form.get_user())
        return redirect("dashboard:home")
    return render(request, "accounts/login.html", {"form": form})


@login_required
@require_POST
def logout_view(request):
    logout(request)
    return redirect("accounts:login")


@login_required
def user_list(request):
    if request.user.role == User.Role.ADMIN:
        users = User.objects.select_related("department").all()
    elif request.user.role == User.Role.EDITOR:
        ensure_department_assignment(request.user)
        users = User.objects.select_related("department").filter(department=request.user.department)
    else:
        raise PermissionDenied

    q = request.GET.get("q", "").strip()
    if q:
        users = users.filter(
            Q(username__icontains=q)
            | Q(full_name__icontains=q)
            | Q(email__icontains=q)
            | Q(department__name__icontains=q)
        )
    users = users.order_by("username")
    page_obj = Paginator(users, USERS_PER_PAGE).get_page(request.GET.get("page"))

    return render(
        request,
        "accounts/user_list.html",
        {
            "users": page_obj,
            "page_obj": page_obj,
            "query": q,
        },
    )


@login_required
def user_detail(request, pk: int):
    target_user = get_object_or_404(User.objects.select_related("department"), pk=pk)

    if request.user.role == User.Role.ADMIN:
        pass
    elif can_editor_view_user(request.user, target_user):
        pass
    else:
        raise PermissionDenied

    from knowledgebase.models import ReadHistory

    history = (
        ReadHistory.objects.select_related("tutorial", "tutorial__department")
        .defer(
            "tutorial__content",
            "tutorial__description",
            "tutorial__video_file",
            "tutorial__video_caption",
            "tutorial__video_url",
        )
        .filter(user=target_user)
        .order_by("-read_at")[:30]
    )
    can_edit_user = request.user.role == User.Role.ADMIN or can_editor_manage_user(request.user, target_user)
    return render(
        request,
        "accounts/user_detail.html",
        {
            "target_user": target_user,
            "history": history,
            "can_edit_user": can_edit_user,
        },
    )


@login_required
def user_create(request):
    if request.user.role == User.Role.ADMIN:
        form = AdminUserCreateForm(request.POST or None, request.FILES or None)
    elif request.user.role == User.Role.EDITOR:
        ensure_department_assignment(request.user)
        form = EditorUserCreateForm(
            request.POST or None,
            request.FILES or None,
            department=request.user.department,
        )
    else:
        raise PermissionDenied

    if request.method == "POST" and form.is_valid():
        user = form.save()
        messages.success(request, _("User '%(name)s' created successfully.") % {"name": user.username})
        return redirect("accounts:user-list")

    return render(
        request,
        "accounts/user_form.html",
        {"form": form, "is_create": True},
    )


@login_required
def user_update(request, pk: int):
    target_user = get_object_or_404(User, pk=pk)

    if request.user.role == User.Role.ADMIN:
        form = AdminUserUpdateForm(
            request.POST or None,
            request.FILES or None,
            instance=target_user,
        )
    elif can_editor_manage_user(request.user, target_user):
        form = EditorManagedUserUpdateForm(
            request.POST or None,
            request.FILES or None,
            instance=target_user,
        )
    else:
        raise PermissionDenied

    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, _("User updated successfully."))
        return redirect("accounts:user-list")

    return render(
        request,
        "accounts/user_form.html",
        {"form": form, "is_create": False, "target_user": target_user},
    )


@login_required
def user_delete(request, pk: int):
    target_user = get_object_or_404(User, pk=pk)
    if request.user.id == target_user.id:
        messages.error(request, _("You cannot delete your own account."))
        return redirect("accounts:user-list")

    if request.user.role == User.Role.ADMIN:
        pass
    elif can_editor_manage_user(request.user, target_user):
        pass
    else:
        raise PermissionDenied

    if request.method == "POST":
        username = target_user.username
        target_user.delete()
        messages.success(request, _("User '%(name)s' deleted successfully.") % {"name": username})
        return redirect("accounts:user-list")
    return render(
        request,
        "accounts/user_confirm_delete.html",
        {"target_user": target_user},
    )


@login_required
def profile_view(request):
    from knowledgebase.models import ReadHistory

    history = (
        ReadHistory.objects.select_related("tutorial", "tutorial__department")
        .defer(
            "tutorial__content",
            "tutorial__description",
            "tutorial__video_file",
            "tutorial__video_caption",
            "tutorial__video_url",
        )
        .filter(user=request.user)
        .order_by("-read_at")[:15]
    )
    return render(request, "accounts/profile.html", {"history": history})


@login_required
def profile_update(request):
    if request.user.role in {User.Role.EDITOR, User.Role.USER} and not request.user.department_id:
        messages.error(request, _("Your account is missing a department. Contact an administrator."))
        return redirect("accounts:profile")

    form = ProfileUpdateForm(request.POST or None, request.FILES or None, instance=request.user)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, _("Profile updated successfully."))
        return redirect("accounts:profile")
    return render(request, "accounts/profile_edit.html", {"form": form})

# Create your views here.
