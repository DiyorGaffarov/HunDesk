from django import forms
from django.forms import inlineformset_factory
from django.utils.translation import gettext_lazy as _

from accounts.models import User
from knowledgebase.models import Tutorial, TutorialImage, TutorialVideo

MAX_TUTORIAL_IMAGES = 5
MAX_TUTORIAL_VIDEO_URLS = 5


class TutorialForm(forms.ModelForm):
    remove_video = forms.BooleanField(required=False, widget=forms.HiddenInput())

    class Meta:
        model = Tutorial
        fields = (
            "title",
            "description",
            "content",
            "department",
            "video_file",
            "video_caption",
            "is_published",
        )
        widgets = {
            "description": forms.Textarea(attrs={"rows": 2}),
            "content": forms.Textarea(attrs={"rows": 8}),
            "video_file": forms.FileInput(),
            "video_caption": forms.TextInput(attrs={"placeholder": _("Caption for uploaded video")}),
        }

    def __init__(self, *args, current_user: User = None, **kwargs):
        super().__init__(*args, **kwargs)
        self.current_user = current_user
        self.fields["video_file"].required = False
        self.fields["video_caption"].required = False

        if current_user and current_user.role == User.Role.EDITOR:
            self.fields["department"].queryset = self.fields["department"].queryset.filter(
                pk=current_user.department_id
            )
            self.fields["department"].initial = current_user.department
            self.fields["department"].widget.attrs["readonly"] = True

        self.fields["video_file"].help_text = _("Upload one video file (optional).")
        self.fields["video_caption"].help_text = _("Short caption for uploaded video.")

        self.field_order = [
            "title",
            "description",
            "content",
            "department",
            "video_file",
            "video_caption",
            "remove_video",
            "is_published",
        ]

        for field in self.fields.values():
            if isinstance(field.widget, forms.HiddenInput):
                continue
            css_class = "form-control"
            if isinstance(field.widget, forms.CheckboxInput):
                css_class = "form-check-input"
            existing_class = field.widget.attrs.get("class", "")
            field.widget.attrs["class"] = f"{existing_class} {css_class}".strip()

    def clean_department(self):
        department = self.cleaned_data["department"]
        if self.current_user and self.current_user.role == User.Role.EDITOR:
            return self.current_user.department
        return department

    def clean(self):
        cleaned_data = super().clean()
        remove_video = bool(cleaned_data.get("remove_video"))
        if remove_video:
            cleaned_data["video_file"] = None
            cleaned_data["video_caption"] = ""
        return cleaned_data


class TutorialImageForm(forms.ModelForm):
    class Meta:
        model = TutorialImage
        fields = ("image", "caption")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["image"].widget.attrs["class"] = "form-control"
        self.fields["caption"].widget.attrs["class"] = "form-control"


class TutorialVideoForm(forms.ModelForm):
    class Meta:
        model = TutorialVideo
        fields = ("video_url", "caption")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["video_url"].widget.attrs["class"] = "form-control"
        self.fields["caption"].widget.attrs["class"] = "form-control"
        self.fields["video_url"].widget.attrs["placeholder"] = "https://..."

    def clean_video_url(self):
        value = (self.cleaned_data.get("video_url") or "").strip()
        tokens = [token for token in value.replace(",", " ").split() if token]
        if len(tokens) > 1:
            raise forms.ValidationError(_("Only one video URL is allowed per row."))
        return tokens[0] if tokens else value


TutorialImageFormSet = inlineformset_factory(
    Tutorial,
    TutorialImage,
    form=TutorialImageForm,
    extra=0,
    max_num=MAX_TUTORIAL_IMAGES,
    validate_max=True,
    can_delete=True,
    error_messages={
        "too_many_forms": _("You can add up to %(num)d photos per tutorial."),
    },
)

TutorialVideoFormSet = inlineformset_factory(
    Tutorial,
    TutorialVideo,
    form=TutorialVideoForm,
    extra=0,
    max_num=MAX_TUTORIAL_VIDEO_URLS,
    validate_max=True,
    can_delete=True,
    error_messages={
        "too_many_forms": _("You can add up to %(num)d video URLs per tutorial."),
    },
)
