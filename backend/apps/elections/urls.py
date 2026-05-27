from django.urls import path

from .views import (
    CandidateViewSet,
    ElectionViewSet,
    PositionViewSet,
    VoterDeleteView,
    VoterImportView,
    VoterListView,
)

election_list = ElectionViewSet.as_view({"get": "list", "post": "create"})
election_detail = ElectionViewSet.as_view(
    {"get": "retrieve", "patch": "partial_update", "delete": "destroy"}
)
election_start = ElectionViewSet.as_view({"post": "start"})
election_cancel = ElectionViewSet.as_view({"post": "cancel"})

position_list = PositionViewSet.as_view({"get": "list", "post": "create"})
position_detail = PositionViewSet.as_view(
    {"get": "retrieve", "patch": "partial_update", "delete": "destroy"}
)

candidate_list = CandidateViewSet.as_view({"get": "list", "post": "create"})
candidate_detail = CandidateViewSet.as_view(
    {"get": "retrieve", "patch": "partial_update", "delete": "destroy"}
)

urlpatterns = [
    path("elections", election_list),
    path("elections/<int:pk>", election_detail),
    path("elections/<int:pk>/start", election_start),
    path("elections/<int:pk>/cancel", election_cancel),
    path("elections/<int:election_pk>/positions", position_list),
    path("positions/<int:pk>", position_detail),
    path("positions/<int:position_pk>/candidates", candidate_list),
    path("candidates/<int:pk>", candidate_detail),
    path("elections/<int:election_pk>/voters/import", VoterImportView.as_view()),
    path("elections/<int:election_pk>/voters", VoterListView.as_view()),
    path("voters/<int:pk>", VoterDeleteView.as_view()),
]
