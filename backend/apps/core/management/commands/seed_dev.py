"""
Cria dados fictícios para desenvolvimento local.
Não roda em produção (exige DEBUG=True ou env var SEED_DEV=1).
"""
import os
import random

from django.conf import settings
from django.core.management.base import BaseCommand
from django.db import transaction

from apps.accounts.models import Organization, OrganizationMember, User
from apps.core import cpf as cpf_utils
from apps.elections.models import Candidate, Election, Position, Voter


NOMES = [
    "João Paulo", "Pedro Henrique", "André Luis", "Marcos Silva", "Carlos Eduardo",
    "Roberto Oliveira", "Fernando Souza", "Rafael Ferreira", "Lucas Pereira", "Guilherme Costa",
    "Mateus Rodrigues", "Felipe Santos", "Eduardo Lima", "Thiago Alves", "Bruno Martins",
    "Leandro Barbosa", "Renato Carvalho", "Fábio Nascimento", "Alexandre Rocha", "Sérgio Mendes",
    "Paulo Ribeiro", "Ricardo Gomes", "Marcelo Araújo", "Rodrigo Cardoso", "Alberto Correia",
    "Henrique Moreira", "Antônio Dias", "Cláudio Teixeira", "Ronaldo Pinto", "Wagner Cunha",
    "Isaías Costa", "Ezequiel Ferreira", "Elias Santos", "Davi Rodrigues", "Josué Oliveira",
    "Moisés Lima", "Abraão Alves", "Noé Martins", "Jonas Barbosa", "Jeremias Carvalho",
    "Isaías Nascimento", "Ezra Rocha", "Neemias Mendes", "Malaquias Ribeiro", "Habacuque Gomes",
    "Oséias Araújo", "Amós Cardoso", "Miquéias Correia", "Naum Moreira", "Sofonias Dias",
]


def gerar_cpf_valido() -> str:
    while True:
        nums = [random.randint(0, 9) for _ in range(9)]
        d1 = sum((10 - i) * v for i, v in enumerate(nums)) % 11
        d1 = 0 if d1 < 2 else 11 - d1
        nums.append(d1)
        d2 = sum((11 - i) * v for i, v in enumerate(nums)) % 11
        d2 = 0 if d2 < 2 else 11 - d2
        nums.append(d2)
        cpf = "".join(str(n) for n in nums)
        if cpf_utils.is_valid(cpf):
            return cpf


class Command(BaseCommand):
    help = "Cria dados fictícios para desenvolvimento"

    def handle(self, *args, **options):
        if not settings.DEBUG and not os.environ.get("SEED_DEV"):
            self.stderr.write("seed_dev só roda com DEBUG=True ou SEED_DEV=1")
            return

        with transaction.atomic():
            user, created = User.objects.get_or_create(
                email="admin@knoxis.local",
                defaults={"name": "Admin Knoxis"},
            )
            if created:
                user.set_password(os.environ.get("SEED_PASSWORD", "knoxis-dev-senha-123"))
                user.save()
                self.stdout.write(f"Usuário criado: admin@knoxis.local")
            else:
                self.stdout.write("Usuário já existia.")

            org, _ = Organization.objects.get_or_create(
                slug="igreja-teste",
                defaults={"name": "Igreja Presbiteriana de Teste", "city": "São Paulo", "state": "SP"},
            )
            OrganizationMember.objects.get_or_create(
                organization=org, user=user, defaults={"role": "owner"}
            )

            election, created = Election.objects.get_or_create(
                organization=org,
                name="Eleição de Oficiais 2026",
                defaults={
                    "description": "Eleição de presbíteros e diáconos para o exercício 2026.",
                    "status": "rascunho",
                    "final_rule": "max_count",
                    "max_escrutinios": 3,
                    "created_by": user,
                },
            )
            if created:
                self.stdout.write("Eleição criada.")

            presbitero, _ = Position.objects.get_or_create(
                election=election, name="Presbítero",
                defaults={"organization": org, "vacancies": 3, "display_order": 1},
            )
            diacono, _ = Position.objects.get_or_create(
                election=election, name="Diácono",
                defaults={"organization": org, "vacancies": 2, "display_order": 2},
            )

            presbiteros = ["Irmão Joaquim", "Irmão Marcos", "Irmão Paulo", "Irmão Tiago", "Irmão Pedro"]
            for i, nome in enumerate(presbiteros):
                Candidate.objects.get_or_create(
                    position=presbitero, name=nome,
                    defaults={"organization": org, "election": election, "display_order": i},
                )

            diaconos = ["Irmão Filipe", "Irmão André", "Irmão Barnabé", "Irmão Silas"]
            for i, nome in enumerate(diaconos):
                Candidate.objects.get_or_create(
                    position=diacono, name=nome,
                    defaults={"organization": org, "election": election, "display_order": i},
                )

            existing_hashes = set(Voter.objects.filter(election=election).values_list("cpf_hash", flat=True))
            added = 0
            used_names = set()
            for nome in NOMES:
                if nome in used_names:
                    continue
                used_names.add(nome)
                cpf = gerar_cpf_valido()
                h = cpf_utils.hash_cpf(cpf)
                if h not in existing_hashes:
                    Voter.objects.create(
                        organization=org,
                        election=election,
                        name=nome,
                        cpf_hash=h,
                        cpf_last2=cpf_utils.last2(cpf),
                    )
                    existing_hashes.add(h)
                    added += 1

            self.stdout.write(f"{added} votantes adicionados.")
            self.stdout.write(self.style.SUCCESS("seed_dev concluído."))
