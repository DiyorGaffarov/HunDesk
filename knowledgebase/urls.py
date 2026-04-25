from django.urls import path

from knowledgebase import views

app_name = "knowledgebase"

urlpatterns = [
    path("", views.tutorial_list, name="tutorial-list"),
    path("create/", views.tutorial_create, name="tutorial-create"),
    path("<int:pk>/", views.tutorial_detail, name="tutorial-detail"),
    path("<int:pk>/edit/", views.tutorial_update, name="tutorial-edit"),
    path("<int:pk>/delete/", views.tutorial_delete, name="tutorial-delete"),
]
