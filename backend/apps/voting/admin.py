from django.contrib import admin

from .models import BallotSession, ElectionResult, Escrutinio, Vote, VoterAttendance


@admin.register(Escrutinio)
class EscrutinioAdmin(admin.ModelAdmin):
    list_display = ["election", "number", "status", "is_final", "total_voters"]
    list_filter = ["status"]


@admin.register(VoterAttendance)
class VoterAttendanceAdmin(admin.ModelAdmin):
    list_display = ["escrutinio", "voter", "voted_at"]


@admin.register(ElectionResult)
class ElectionResultAdmin(admin.ModelAdmin):
    list_display = ["escrutinio", "position", "candidate", "votes_count", "was_elected"]
