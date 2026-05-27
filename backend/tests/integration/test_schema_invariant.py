"""
Teste de invariante: a tabela 'votes' não pode ter colunas que identifiquem o eleitor.
"""
import pytest
from django.db import connection


VOTES_ALLOWED_COLUMNS = {
    "id",
    "organization_id",
    "escrutinio_id",
    "position_id",
    "candidate_id",
    "created_at",
}

FORBIDDEN_COLUMNS = {"voter_id", "cpf", "cpf_hash", "ballot_session_id", "user_id", "voter"}


@pytest.mark.django_db
def test_votes_nao_tem_voter_id():
    with connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT column_name
            FROM information_schema.columns
            WHERE table_name = 'votes'
            """
        )
        columns = {row[0] for row in cursor.fetchall()}

    for col in FORBIDDEN_COLUMNS:
        assert col not in columns, f"A tabela 'votes' NÃO deve ter a coluna '{col}'. Invariante de voto secreto violada."

    for col in columns:
        assert col in VOTES_ALLOWED_COLUMNS, f"Coluna inesperada '{col}' em 'votes'. Revisar se não identifica o eleitor."
