from django.urls import path

from .views_public import ElectionByIdPublicView, ElectionPublicView, IdentifyView, SubmitBallotView

urlpatterns = [
    path("elections/<slug:slug>", ElectionPublicView.as_view()),
    path("elections-by-id/<int:pk>", ElectionByIdPublicView.as_view()),
    path("elections/<slug:slug>/identify", IdentifyView.as_view()),
    path("ballot/submit", SubmitBallotView.as_view()),
]
