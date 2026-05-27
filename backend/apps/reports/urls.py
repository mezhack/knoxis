from django.urls import path

from .views import RelatorioDetailView, RelatorioListView

urlpatterns = [
    path("elections/<int:election_pk>/relatorios", RelatorioListView.as_view()),
    path("escrutinios/<int:pk>/relatorio", RelatorioDetailView.as_view()),
]
