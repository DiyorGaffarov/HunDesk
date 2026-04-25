from django.urls import path

from accounts import views

app_name = "accounts"

urlpatterns = [
    path("set-language/", views.set_language_view, name="set-language"),
    path("login/", views.login_view, name="login"),
    path("logout/", views.logout_view, name="logout"),
    path("users/", views.user_list, name="user-list"),
    path("users/create/", views.user_create, name="user-create"),
    path("users/<int:pk>/edit/", views.user_update, name="user-edit"),
    path("users/<int:pk>/delete/", views.user_delete, name="user-delete"),
    path("profile/", views.profile_view, name="profile"),
    path("profile/edit/", views.profile_update, name="profile-edit"),
]
