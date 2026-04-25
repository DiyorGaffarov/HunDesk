from django.urls import path

from dashboard import views

app_name = "dashboard"

urlpatterns = [
    path("", views.home, name="home"),
    path("dashboard/admin/", views.admin_dashboard, name="admin-dashboard"),
    path("dashboard/editor/", views.editor_dashboard, name="editor-dashboard"),
    path("dashboard/user/", views.user_dashboard, name="user-dashboard"),
]
