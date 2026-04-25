from django.core.exceptions import PermissionDenied

from accounts.models import User


def ensure_admin(user: User) -> None:
    if not user.is_authenticated or user.role != User.Role.ADMIN:
        raise PermissionDenied


def ensure_department_assignment(user: User) -> None:
    if user.role in {User.Role.EDITOR, User.Role.USER} and user.department_id is None:
        raise PermissionDenied


def ensure_admin_or_editor(user: User) -> None:
    if not user.is_authenticated or user.role not in {User.Role.ADMIN, User.Role.EDITOR}:
        raise PermissionDenied


def can_editor_manage_user(editor: User, target: User) -> bool:
    return (
        editor.role == User.Role.EDITOR
        and editor.department_id is not None
        and editor.department_id == target.department_id
        and target.role == User.Role.USER
    )


def can_manage_tutorial(user: User, tutorial_department_id: int) -> bool:
    if user.role == User.Role.ADMIN:
        return True
    if user.role == User.Role.EDITOR and user.department_id == tutorial_department_id:
        return True
    return False
