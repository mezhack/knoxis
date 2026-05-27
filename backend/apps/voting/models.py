import secrets

from django.db import models
from django.utils import timezone

from apps.accounts.models import Organization
from apps.elections.models import Candidate, Election, Position, Voter

ESCRUTINIO_STATUS = [
    ("preparando", "Preparando"),
    ("aberto", "Aberto"),
    ("encerrado", "Encerrado"),
]


class Escrutinio(models.Model):
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE)
    organization_id: int
    election = models.ForeignKey(Election, on_delete=models.CASCADE, related_name="escrutinios")
    number = models.IntegerField()
    is_final = models.BooleanField(default=False)
    status = models.CharField(max_length=12, choices=ESCRUTINIO_STATUS, default="preparando")
    opened_at = models.DateTimeField(blank=True, null=True)
    closed_at = models.DateTimeField(blank=True, null=True)
    total_voters = models.IntegerField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "escrutinios"
        unique_together = [("election", "number")]
        ordering = ["number"]

    def __str__(self):
        return f"Escrutínio {self.number} — {self.election.name}"


class EscrutinioPosition(models.Model):
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE)
    organization_id: int
    escrutinio = models.ForeignKey(Escrutinio, on_delete=models.CASCADE, related_name="positions")
    position = models.ForeignKey(Position, on_delete=models.RESTRICT, related_name="escrutinio_positions")
    vacancies_remaining = models.IntegerField()

    class Meta:
        db_table = "escrutinio_positions"
        unique_together = [("escrutinio", "position")]
        constraints = [
            models.CheckConstraint(
                condition=models.Q(vacancies_remaining__gte=0),
                name="escrutinio_positions_vacancies_gte_0",
            )
        ]


class EscrutinioCandidate(models.Model):
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE)
    organization_id: int
    escrutinio = models.ForeignKey(Escrutinio, on_delete=models.CASCADE, related_name="candidates")
    position = models.ForeignKey(Position, on_delete=models.RESTRICT)
    candidate = models.ForeignKey(Candidate, on_delete=models.RESTRICT, related_name="escrutinio_entries")

    class Meta:
        db_table = "escrutinio_candidates"
        unique_together = [("escrutinio", "candidate")]


class BallotSession(models.Model):
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE)
    organization_id: int
    escrutinio = models.ForeignKey(Escrutinio, on_delete=models.CASCADE, related_name="ballot_sessions")
    voter = models.ForeignKey(Voter, on_delete=models.RESTRICT, related_name="ballot_sessions")
    token = models.CharField(max_length=64, unique=True)
    expires_at = models.DateTimeField()
    used_at = models.DateTimeField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "ballot_sessions"

    @classmethod
    def create_for_voter(cls, escrutinio, voter):
        token = secrets.token_hex(32)
        expires_at = timezone.now() + timezone.timedelta(minutes=10)
        return cls.objects.create(
            organization=escrutinio.organization,
            escrutinio=escrutinio,
            voter=voter,
            token=token,
            expires_at=expires_at,
        )

    def is_valid(self):
        return self.used_at is None and timezone.now() < self.expires_at


class VoterAttendance(models.Model):
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE)
    organization_id: int
    escrutinio = models.ForeignKey(Escrutinio, on_delete=models.CASCADE, related_name="attendances")
    voter = models.ForeignKey(Voter, on_delete=models.RESTRICT, related_name="attendances")
    voted_at = models.DateTimeField(default=timezone.now)

    class Meta:
        db_table = "voter_attendance"
        unique_together = [("escrutinio", "voter")]


class Vote(models.Model):
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE)
    organization_id: int
    escrutinio = models.ForeignKey(Escrutinio, on_delete=models.RESTRICT, related_name="votes")
    position = models.ForeignKey(Position, on_delete=models.RESTRICT)
    candidate = models.ForeignKey(Candidate, on_delete=models.RESTRICT, related_name="votes")
    created_at = models.DateTimeField()

    class Meta:
        db_table = "votes"
        indexes = [
            models.Index(fields=["escrutinio", "candidate"]),
            models.Index(fields=["escrutinio", "position"]),
        ]


class ElectionResult(models.Model):
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE)
    organization_id: int
    election = models.ForeignKey(Election, on_delete=models.CASCADE, related_name="results")
    escrutinio = models.ForeignKey(Escrutinio, on_delete=models.CASCADE, related_name="results")
    position = models.ForeignKey(Position, on_delete=models.RESTRICT)
    candidate = models.ForeignKey(Candidate, on_delete=models.RESTRICT)
    votes_count = models.IntegerField()
    was_elected = models.BooleanField(default=False)
    tie_at_cutoff = models.BooleanField(default=False)
    tie_resolution = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "election_results"
        unique_together = [("escrutinio", "candidate")]
        constraints = [
            models.CheckConstraint(
                condition=models.Q(votes_count__gte=0), name="election_results_votes_count_gte_0"
            )
        ]
