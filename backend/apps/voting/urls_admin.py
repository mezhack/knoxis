from django.urls import path

from .views_admin import (
    EscrutinioCloseView,
    EscrutinioDetailView,
    EscrutinioListView,
    EscrutinioOpenView,
    EscrutinioParciaisView,
    ResolveTieView,
)

urlpatterns = [
    path("elections/<int:election_pk>/escrutinios", EscrutinioListView.as_view()),
    path("escrutinios/<int:pk>", EscrutinioDetailView.as_view()),
    path("escrutinios/<int:pk>/open", EscrutinioOpenView.as_view()),
    path("escrutinios/<int:pk>/close", EscrutinioCloseView.as_view()),
    path("escrutinios/<int:pk>/parciais", EscrutinioParciaisView.as_view()),
    path("escrutinios/<int:pk>/positions/<int:position_pk>/resolve-tie", ResolveTieView.as_view()),
]
