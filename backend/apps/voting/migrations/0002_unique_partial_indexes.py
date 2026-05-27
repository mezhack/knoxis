"""
Adiciona índices únicos parciais:
- escrutinios(election_id) WHERE status='aberto' — garante 1 escrutínio aberto por eleição.
- ballot_sessions(escrutinio_id, voter_id) WHERE used_at IS NULL — sessão ativa única por voter.
Idempotente: usa CREATE UNIQUE INDEX IF NOT EXISTS.
"""
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("voting", "0001_initial"),
    ]

    operations = [
        migrations.RunSQL(
            sql="""
            CREATE UNIQUE INDEX IF NOT EXISTS voting_escrutinios_one_aberto_per_election
            ON escrutinios(election_id)
            WHERE status = 'aberto';
            """,
            reverse_sql="DROP INDEX IF EXISTS voting_escrutinios_one_aberto_per_election;",
        ),
        migrations.RunSQL(
            sql="""
            CREATE UNIQUE INDEX IF NOT EXISTS voting_ballot_sessions_active_per_voter
            ON ballot_sessions(escrutinio_id, voter_id)
            WHERE used_at IS NULL;
            """,
            reverse_sql="DROP INDEX IF EXISTS voting_ballot_sessions_active_per_voter;",
        ),
    ]
