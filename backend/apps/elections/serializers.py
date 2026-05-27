import csv
import io

from rest_framework import serializers

from apps.core import cpf as cpf_utils

from .models import Candidate, Election, Position, Voter


class PositionSerializer(serializers.ModelSerializer):
    candidates_count = serializers.SerializerMethodField()

    class Meta:
        model = Position
        fields = ["id", "name", "vacancies", "display_order", "candidates_count"]

    def get_candidates_count(self, obj):
        return obj.candidates.count()


class CandidateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Candidate
        fields = ["id", "name", "display_order"]


class ElectionListSerializer(serializers.ModelSerializer):
    positions_count = serializers.SerializerMethodField()
    voters_count = serializers.SerializerMethodField()
    current_escrutinio_number = serializers.SerializerMethodField()

    class Meta:
        model = Election
        fields = [
            "id",
            "name",
            "status",
            "scheduled_for",
            "final_rule",
            "max_escrutinios",
            "positions_count",
            "voters_count",
            "current_escrutinio_number",
        ]

    def get_positions_count(self, obj):
        return obj.positions.count()

    def get_voters_count(self, obj):
        return obj.voters.count()

    def get_current_escrutinio_number(self, obj):
        esc = obj.escrutinios.filter(status="aberto").first()
        return esc.number if esc else None


class ElectionDetailSerializer(serializers.ModelSerializer):
    positions = PositionSerializer(many=True, read_only=True)
    voters_count = serializers.SerializerMethodField()
    current_escrutinio_number = serializers.SerializerMethodField()

    class Meta:
        model = Election
        fields = [
            "id",
            "name",
            "description",
            "status",
            "scheduled_for",
            "final_rule",
            "max_escrutinios",
            "started_at",
            "ended_at",
            "positions",
            "voters_count",
            "current_escrutinio_number",
        ]

    def get_voters_count(self, obj):
        return obj.voters.count()

    def get_current_escrutinio_number(self, obj):
        esc = obj.escrutinios.filter(status="aberto").first()
        return esc.number if esc else None


class ElectionCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Election
        fields = ["name", "description", "scheduled_for", "final_rule", "max_escrutinios"]

    def validate(self, data):
        if data.get("final_rule") == "max_count" and not data.get("max_escrutinios"):
            raise serializers.ValidationError(
                {"max_escrutinios": "Obrigatório quando final_rule é max_count."}
            )
        return data


class ElectionPatchSerializer(serializers.ModelSerializer):
    class Meta:
        model = Election
        fields = ["name", "description", "scheduled_for", "final_rule", "max_escrutinios"]

    def validate(self, data):
        instance = self.instance
        if instance and instance.status in ("em_andamento",):
            allowed = {"description", "max_escrutinios"}
            forbidden = set(data.keys()) - allowed
            if forbidden:
                raise serializers.ValidationError(
                    f"Com eleição em andamento, só é permitido editar: descrição e max_escrutinios. Campos inválidos: {', '.join(forbidden)}"
                )
        if instance and instance.status in ("encerrada", "cancelada"):
            raise serializers.ValidationError("Eleição encerrada ou cancelada não pode ser editada.")
        return data


class VoterImportSerializer(serializers.Serializer):
    file = serializers.FileField()

    def validate_file(self, value):
        if not value.name.endswith(".csv"):
            raise serializers.ValidationError("Apenas arquivos .csv são aceitos.")
        return value

    def import_voters(self, election) -> dict:
        file = self.validated_data["file"]
        content = file.read().decode("utf-8", errors="replace")
        reader = csv.DictReader(io.StringIO(content))

        if not reader.fieldnames or "cpf" not in reader.fieldnames or "nome" not in reader.fieldnames:
            raise serializers.ValidationError({"file": "CSV deve ter colunas 'cpf' e 'nome'."})

        imported = 0
        skipped_duplicate = 0
        skipped_invalid = 0
        errors = []

        existing_hashes = set(
            Voter.objects.filter(election=election).values_list("cpf_hash", flat=True)
        )

        for i, row in enumerate(reader, start=2):
            raw_cpf = (row.get("cpf") or "").strip()
            name = (row.get("nome") or "").strip()

            if not cpf_utils.is_valid(raw_cpf):
                skipped_invalid += 1
                errors.append(
                    {"line": i, "reason": "CPF inválido", "value_last2": cpf_utils.last2(raw_cpf) if len(cpf_utils.normalize(raw_cpf)) >= 2 else "??"}
                )
                continue

            h = cpf_utils.hash_cpf(raw_cpf)

            if h in existing_hashes:
                skipped_duplicate += 1
                errors.append({"line": i, "reason": "duplicado", "value_last2": cpf_utils.last2(raw_cpf)})
                continue

            Voter.objects.create(
                organization=election.organization,
                election=election,
                name=name or "Sem nome",
                cpf_hash=h,
                cpf_last2=cpf_utils.last2(raw_cpf),
            )
            existing_hashes.add(h)
            imported += 1

        return {
            "imported": imported,
            "skipped_duplicate": skipped_duplicate,
            "skipped_invalid": skipped_invalid,
            "errors": errors,
        }


class VoterListSerializer(serializers.ModelSerializer):
    cpf_masked = serializers.SerializerMethodField()

    class Meta:
        model = Voter
        fields = ["id", "name", "cpf_masked"]

    def get_cpf_masked(self, obj):
        return f"***.***.***-{obj.cpf_last2}"
