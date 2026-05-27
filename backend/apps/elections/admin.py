from django.contrib import admin

from .models import Candidate, Election, Position, Voter


@admin.register(Election)
class ElectionAdmin(admin.ModelAdmin):
    list_display = ["name", "organization", "status", "scheduled_for"]
    list_filter = ["status", "organization"]
    search_fields = ["name"]


@admin.register(Position)
class PositionAdmin(admin.ModelAdmin):
    list_display = ["name", "election", "vacancies"]


@admin.register(Candidate)
class CandidateAdmin(admin.ModelAdmin):
    list_display = ["name", "position", "election"]


@admin.register(Voter)
class VoterAdmin(admin.ModelAdmin):
    list_display = ["name", "election", "cpf_last2"]
