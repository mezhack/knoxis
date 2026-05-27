from django.db import models
from django.utils import timezone

from apps.accounts.models import Organization, User

ELECTION_STATUS = [
    ("rascunho", "Rascunho"),
    ("pronta", "Pronta"),
    ("em_andamento", "Em andamento"),
    ("encerrada", "Encerrada"),
    ("cancelada", "Cancelada"),
]

FINAL_RULE = [
    ("manual", "Manual"),
    ("max_count", "Por máximo de escrutínios"),
]


class Election(models.Model):
    organization = models.ForeignKey(
        Organization, on_delete=models.CASCADE, related_name="elections"
    )
    organization_id: int
    name = models.TextField()
    description = models.TextField(blank=True, null=True)
    scheduled_for = models.DateField(blank=True, null=True)
    status = models.CharField(max_length=20, choices=ELECTION_STATUS, default="rascunho")
    final_rule = models.CharField(max_length=10, choices=FINAL_RULE)
    max_escrutinios = models.IntegerField(blank=True, null=True)
    started_at = models.DateTimeField(blank=True, null=True)
    ended_at = models.DateTimeField(blank=True, null=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "elections"
        indexes = [
            models.Index(fields=["organization", "status"]),
            models.Index(fields=["organization", "scheduled_for"]),
        ]

    def __str__(self):
        return self.name

    def check_ready(self) -> list[str]:
        """Retorna lista de pendências para iniciar a eleição."""
        issues = []
        positions = self.positions.all()
        if not positions.exists():
            issues.append("Nenhum cargo cadastrado.")
        for pos in positions:
            if pos.candidates.count() < pos.vacancies:
                issues.append(
                    f"Cargo '{pos.name}': candidatos ({pos.candidates.count()}) < vagas ({pos.vacancies})."
                )
        if not self.voters.exists():
            issues.append("Lista de votantes vazia.")
        if self.final_rule == "max_count" and not self.max_escrutinios:
            issues.append("Número máximo de escrutínios não definido.")
        return issues


class Position(models.Model):
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE)
    organization_id: int
    election = models.ForeignKey(Election, on_delete=models.CASCADE, related_name="positions")
    name = models.TextField()
    vacancies = models.IntegerField()
    display_order = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "positions"
        unique_together = [("election", "name")]
        ordering = ["display_order", "name"]
        constraints = [
            models.CheckConstraint(condition=models.Q(vacancies__gte=1), name="positions_vacancies_gte_1")
        ]

    def __str__(self):
        return f"{self.name} ({self.election.name})"


class Candidate(models.Model):
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE)
    organization_id: int
    election = models.ForeignKey(Election, on_delete=models.CASCADE, related_name="candidates")
    position = models.ForeignKey(Position, on_delete=models.CASCADE, related_name="candidates")
    name = models.TextField()
    display_order = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "candidates"
        unique_together = [("position", "name")]
        ordering = ["display_order", "name"]

    def __str__(self):
        return f"{self.name} ({self.position.name})"


class Voter(models.Model):
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE)
    organization_id: int
    election = models.ForeignKey(Election, on_delete=models.CASCADE, related_name="voters")
    name = models.TextField()
    cpf_hash = models.CharField(max_length=64)
    cpf_last2 = models.CharField(max_length=2)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "voters"
        unique_together = [("election", "cpf_hash")]
        indexes = [models.Index(fields=["election", "cpf_hash"])]

    def __str__(self):
        return f"{self.name} (***-{self.cpf_last2})"
