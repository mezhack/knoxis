from django.urls import path

from .views_public import ElectionPublicView, IdentifyView, SubmitBallotView

urlpatterns = [
    path("elections/<slug:slug>", ElectionPublicView.as_view()),
    path("elections/<slug:slug>/identify", IdentifyView.as_view()),
    path("ballot/submit", SubmitBallotView.as_view()),
]
