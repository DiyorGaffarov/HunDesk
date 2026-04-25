from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.translation import gettext_lazy as _
from django.views.decorators.http import require_POST

from accounts.models import User
from accounts.permissions import can_manage_tutorial
from knowledgebase.forms import (
    MAX_TUTORIAL_IMAGES,
    MAX_TUTORIAL_VIDEO_URLS,
    TutorialForm,
    TutorialImageFormSet,
    TutorialVideoFormSet,
)
from knowledgebase.models import ReadHistory, Tutorial


def _has_active_video_urls(video_formset) -> bool:
    for item in video_formset.cleaned_data:
        if not item or item.get("DELETE"):
            continue
        if (item.get("video_url") or "").strip():
            return True
    return False


def _can_view_tutorial(user: User, tutorial: Tutorial) -> bool:
    if user.role == User.Role.ADMIN:
        return True
    if user.role == User.Role.EDITOR:
        return user.department_id == tutorial.department_id
    if user.role == User.Role.USER:
        return user.department_id == tutorial.department_id and tutorial.is_published
    return False


@login_required
def tutorial_list(request):
    tutorials = Tutorial.objects.select_related("department", "created_by")
    if request.user.role == User.Role.ADMIN:
        pass
    elif request.user.role == User.Role.EDITOR:
        tutorials = tutorials.filter(department=request.user.department)
    else:
        tutorials = tutorials.filter(department=request.user.department, is_published=True)

    q = request.GET.get("q", "").strip()
    if q:
        tutorials = tutorials.filter(
            Q(title__icontains=q) | Q(description__icontains=q) | Q(content__icontains=q)
        )

    return render(
        request,
        "knowledgebase/tutorial_list.html",
        {
            "tutorials": tutorials.order_by("-updated_at"),
            "query": q,
        },
    )


@login_required
def tutorial_detail(request, pk: int):
    tutorial = get_object_or_404(
        Tutorial.objects.select_related("department", "created_by").prefetch_related("images", "video_links"),
        pk=pk,
    )
    if not _can_view_tutorial(request.user, tutorial):
        raise PermissionDenied

    is_read = False
    if request.user.role == User.Role.USER:
        is_read = ReadHistory.objects.filter(user=request.user, tutorial=tutorial).exists()

    return render(
        request,
        "knowledgebase/tutorial_detail.html",
        {"tutorial": tutorial, "is_read": is_read},
    )


@login_required
@require_POST
def tutorial_toggle_read(request, pk: int):
    tutorial = get_object_or_404(Tutorial, pk=pk)
    if request.user.role != User.Role.USER:
        raise PermissionDenied
    if not _can_view_tutorial(request.user, tutorial):
        raise PermissionDenied

    read_item = ReadHistory.objects.filter(user=request.user, tutorial=tutorial).first()
    if read_item:
        read_item.delete()
        messages.info(request, _("Marked as unread."))
    else:
        ReadHistory.objects.create(user=request.user, tutorial=tutorial)
        messages.success(request, _("Marked as read."))
    return redirect("knowledgebase:tutorial-detail", pk=pk)


@login_required
def tutorial_create(request):
    if request.user.role not in {User.Role.ADMIN, User.Role.EDITOR}:
        raise PermissionDenied

    form = TutorialForm(request.POST or None, request.FILES or None, current_user=request.user)
    formset = TutorialImageFormSet(
        request.POST or None,
        request.FILES or None,
        prefix="images",
    )
    video_formset = TutorialVideoFormSet(
        request.POST or None,
        prefix="video_urls",
    )

    if request.method == "POST" and form.is_valid() and formset.is_valid() and video_formset.is_valid():
        has_uploaded_video = bool(form.cleaned_data.get("video_file"))
        has_video_urls = _has_active_video_urls(video_formset)
        if has_uploaded_video and has_video_urls:
            form.add_error(None, _("Use either uploaded video or video URLs, not both."))
            return render(
                request,
                "knowledgebase/tutorial_form.html",
                {
                    "form": form,
                    "formset": formset,
                    "video_formset": video_formset,
                    "is_create": True,
                    "max_images": MAX_TUTORIAL_IMAGES,
                    "max_video_urls": MAX_TUTORIAL_VIDEO_URLS,
                },
            )

        tutorial = form.save(commit=False)
        tutorial.created_by = request.user
        if request.user.role == User.Role.EDITOR:
            tutorial.department = request.user.department
        tutorial.video_url = ""
        tutorial.save()
        formset.instance = tutorial
        formset.save()
        video_formset.instance = tutorial
        video_formset.save()
        messages.success(request, _("Tutorial created successfully."))
        return redirect("knowledgebase:tutorial-list")

    return render(
        request,
        "knowledgebase/tutorial_form.html",
        {
            "form": form,
            "formset": formset,
            "video_formset": video_formset,
            "is_create": True,
            "max_images": MAX_TUTORIAL_IMAGES,
            "max_video_urls": MAX_TUTORIAL_VIDEO_URLS,
        },
    )


@login_required
def tutorial_update(request, pk: int):
    tutorial = get_object_or_404(Tutorial, pk=pk)
    if not can_manage_tutorial(request.user, tutorial.department_id):
        raise PermissionDenied

    form = TutorialForm(
        request.POST or None,
        request.FILES or None,
        instance=tutorial,
        current_user=request.user,
    )
    formset = TutorialImageFormSet(
        request.POST or None,
        request.FILES or None,
        instance=tutorial,
        prefix="images",
    )
    video_formset = TutorialVideoFormSet(
        request.POST or None,
        instance=tutorial,
        prefix="video_urls",
    )

    if request.method == "POST" and form.is_valid() and formset.is_valid() and video_formset.is_valid():
        has_uploaded_video = bool(form.cleaned_data.get("video_file")) or (
            bool(tutorial.video_file) and not form.cleaned_data.get("remove_video")
        )
        has_video_urls = _has_active_video_urls(video_formset)
        if has_uploaded_video and has_video_urls:
            form.add_error(None, _("Use either uploaded video or video URLs, not both."))
            return render(
                request,
                "knowledgebase/tutorial_form.html",
                {
                    "form": form,
                    "formset": formset,
                    "video_formset": video_formset,
                    "is_create": False,
                    "tutorial": tutorial,
                    "max_images": MAX_TUTORIAL_IMAGES,
                    "max_video_urls": MAX_TUTORIAL_VIDEO_URLS,
                },
            )

        old_video_file = tutorial.video_file
        tutorial = form.save(commit=False)
        if request.user.role == User.Role.EDITOR:
            tutorial.department = request.user.department
        tutorial.video_url = ""
        if form.cleaned_data.get("remove_video"):
            if old_video_file:
                old_video_file.delete(save=False)
            tutorial.video_file = None
            tutorial.video_caption = ""
        tutorial.save()
        formset.save()
        video_formset.save()
        messages.success(request, _("Tutorial updated successfully."))
        return redirect("knowledgebase:tutorial-list")

    return render(
        request,
        "knowledgebase/tutorial_form.html",
        {
            "form": form,
            "formset": formset,
            "video_formset": video_formset,
            "is_create": False,
            "tutorial": tutorial,
            "max_images": MAX_TUTORIAL_IMAGES,
            "max_video_urls": MAX_TUTORIAL_VIDEO_URLS,
        },
    )


@login_required
def tutorial_delete(request, pk: int):
    tutorial = get_object_or_404(Tutorial, pk=pk)
    if not can_manage_tutorial(request.user, tutorial.department_id):
        raise PermissionDenied
    if request.method == "POST":
        tutorial.delete()
        messages.success(request, _("Tutorial deleted successfully."))
        return redirect("knowledgebase:tutorial-list")
    return render(
        request,
        "knowledgebase/tutorial_confirm_delete.html",
        {"tutorial": tutorial},
    )

# Create your views here.
