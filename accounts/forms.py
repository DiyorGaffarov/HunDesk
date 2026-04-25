from django import forms
from django.contrib.auth.forms import AuthenticationForm, UserChangeForm, UserCreationForm
from django.utils.translation import gettext_lazy as _

from accounts.models import User


class BootstrapFormMixin:
    def _apply_bootstrap(self):
        for field in self.fields.values():
            css_class = "form-control"
            if isinstance(field.widget, forms.CheckboxInput):
                css_class = "form-check-input"
            field.widget.attrs["class"] = css_class


class LoginForm(AuthenticationForm, BootstrapFormMixin):
    username = forms.CharField(label=_("Username"))
    password = forms.CharField(label=_("Password"), widget=forms.PasswordInput)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._apply_bootstrap()


class AdminUserCreateForm(UserCreationForm, BootstrapFormMixin):
    class Meta:
        model = User
        fields = (
            "username",
            "email",
            "phone_number",
            "full_name",
            "role",
            "department",
            "profile_photo",
            "password1",
            "password2",
        )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._apply_bootstrap()


class EditorUserCreateForm(UserCreationForm, BootstrapFormMixin):
    class Meta:
        model = User
        fields = (
            "username",
            "email",
            "phone_number",
            "full_name",
            "profile_photo",
            "password1",
            "password2",
        )

    def __init__(self, *args, department=None, **kwargs):
        self.department = department
        super().__init__(*args, **kwargs)
        self._apply_bootstrap()

    def save(self, commit=True):
        user = super().save(commit=False)
        user.role = User.Role.USER
        user.department = self.department
        if commit:
            user.save()
        return user


class AdminUserUpdateForm(UserChangeForm, BootstrapFormMixin):
    password = None

    class Meta:
        model = User
        fields = (
            "username",
            "email",
            "phone_number",
            "full_name",
            "role",
            "department",
            "profile_photo",
            "is_active",
        )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._apply_bootstrap()


class EditorManagedUserUpdateForm(forms.ModelForm, BootstrapFormMixin):
    class Meta:
        model = User
        fields = ("email", "phone_number", "full_name", "profile_photo", "is_active")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._apply_bootstrap()


class ProfileUpdateForm(forms.ModelForm, BootstrapFormMixin):
    class Meta:
        model = User
        fields = ("email", "phone_number", "full_name", "profile_photo")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._apply_bootstrap()
