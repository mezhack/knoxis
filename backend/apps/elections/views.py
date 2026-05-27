import structlog
from django.utils import timezone
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.viewsets import ModelViewSet

from apps.core.mixins import TenantScopedViewSet
from apps.core.permissions import IsOrganizationMember, IsOrganizationOwner

from .models import Candidate, Election, Position, Voter
from .serializers import (
    CandidateSerializer,
    ElectionCreateSerializer,
    ElectionDetailSerializer,
    ElectionListSerializer,
    ElectionPatchSerializer,
    PositionSerializer,
    VoterImportSerializer,
    VoterListSerializer,
)

logger = structlog.get_logger()


class ElectionViewSet(TenantScopedViewSet, ModelViewSet):
    permission_classes = [IsOrganizationMember]

    def get_queryset(self):
        return super().get_queryset().prefetch_related("positions", "voters")

    def get_queryset(self):
        org = self.request.current_organization
        return Election.objects.filter(organization=org).prefetch_related("positions", "voters", "escrutinios")

    def get_serializer_class(self):
        if self.action == "list":
            return ElectionListSerializer
        if self.action in ("create",):
            return ElectionCreateSerializer
        if self.action in ("partial_update", "update"):
            return ElectionPatchSerializer
        return ElectionDetailSerializer

    def perform_create(self, serializer):
        org = self.request.current_organization
        serializer.save(
            organization=org,
            created_by=self.request.user,
        )
        logger.info("election.created", org_id=org.id, user_id=self.request.user.id)

    @action(detail=True, methods=["post"], url_path="start")
    def start(self, request, pk=None):
        election = self.get_object()
        issues = election.check_ready()
        if issues:
            return Response(
                {"type": "unprocessable", "status": 422, "fields": {"requisitos": issues}},
                status=422,
            )
        if election.status != "pronta" and election.status != "rascunho":
            return Response({"detail": "Eleição não está pronta para iniciar."}, status=409)

        election.status = "em_andamento"
        election.started_at = timezone.now()
        election.save()

        # Cria o primeiro escrutínio
        from apps.voting.models import Escrutinio
        esc = Escrutinio.objects.create(
            organization=election.organization,
            election=election,
            number=1,
            is_final=(election.final_rule == "max_count" and election.max_escrutinios == 1),
        )

        logger.info("election.started", election_id=election.id, user_id=request.user.id)
        return Response(ElectionDetailSerializer(election).data)

    @action(detail=True, methods=["post"], url_path="cancel")
    def cancel(self, request, pk=None):
        election = self.get_object()
        if election.status in ("encerrada", "cancelada"):
            return Response({"detail": "Eleição já está em estado terminal."}, status=409)
        if request.data.get("confirm") != "CANCELAR":
            return Response({"detail": "Confirmação necessária: envie {\"confirm\": \"CANCELAR\"}."}, status=400)
        election.status = "cancelada"
        election.ended_at = timezone.now()
        election.save()
        logger.info("election.cancelled", election_id=election.id, user_id=request.user.id)
        return Response({"status": "cancelada"})


class PositionViewSet(TenantScopedViewSet, ModelViewSet):
    permission_classes = [IsOrganizationMember]
    serializer_class = PositionSerializer

    def get_queryset(self):
        org = self.request.current_organization
        election_id = self.kwargs.get("election_pk")
        qs = Position.objects.filter(organization=org)
        if election_id:
            qs = qs.filter(election_id=election_id)
        return qs

    def perform_create(self, serializer):
        org = self.request.current_organization
        election_id = self.kwargs["election_pk"]
        election = Election.objects.get(pk=election_id, organization=org)
        serializer.save(organization=org, election=election)


class CandidateViewSet(TenantScopedViewSet, ModelViewSet):
    permission_classes = [IsOrganizationMember]
    serializer_class = CandidateSerializer

    def get_queryset(self):
        org = self.request.current_organization
        position_id = self.kwargs.get("position_pk")
        qs = Candidate.objects.filter(organization=org)
        if position_id:
            qs = qs.filter(position_id=position_id)
        return qs

    def perform_create(self, serializer):
        org = self.request.current_organization
        position_id = self.kwargs["position_pk"]
        position = Position.objects.get(pk=position_id, organization=org)
        serializer.save(organization=org, position=position, election=position.election)


class VoterPagination(PageNumberPagination):
    page_size = 50


class VoterImportView(APIView):
    permission_classes = [IsOrganizationMember]

    def post(self, request, election_pk):
        org = request.current_organization
        election = Election.objects.get(pk=election_pk, organization=org)

        if election.status in ("em_andamento", "encerrada", "cancelada"):
            return Response({"detail": "Não é possível importar votantes neste estado."}, status=409)

        serializer = VoterImportSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=400)

        result = serializer.import_voters(election)
        logger.info(
            "election.voters.imported",
            election_id=election.id,
            imported=result["imported"],
            skipped=result["skipped_duplicate"] + result["skipped_invalid"],
        )
        return Response(result)


class VoterListView(APIView):
    permission_classes = [IsOrganizationMember]

    def get(self, request, election_pk):
        org = request.current_organization
        voters = Voter.objects.filter(election_id=election_pk, organization=org)
        paginator = VoterPagination()
        page = paginator.paginate_queryset(voters, request)
        serializer = VoterListSerializer(page, many=True)
        return paginator.get_paginated_response(serializer.data)


class VoterDeleteView(APIView):
    permission_classes = [IsOrganizationMember]

    def delete(self, request, pk):
        org = request.current_organization
        voter = Voter.objects.get(pk=pk, organization=org)
        if voter.election.status in ("em_andamento", "encerrada"):
            return Response({"detail": "Não é possível remover votante com eleição em andamento."}, status=409)
        voter.delete()
        return Response(status=204)
