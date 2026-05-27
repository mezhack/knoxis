# Banco de dados

## Engine

PostgreSQL 16. Schema único `public`. Sem extensões obrigatórias além das nativas; `pgcrypto` é opcional e não é dependência.

## Multi-tenancy

**Estratégia:** row-level com coluna `organization_id` em todas as tabelas de domínio.

Não usamos schema-per-tenant porque:
- Operacionalmente mais simples (uma migration corre para tudo).
- Migrations idempotentes valem para todos os tenants ao mesmo tempo.
- Tenant count esperado é baixo (dezenas a centenas), e o overhead de schema-per-tenant não compensa.

Trade-off: vazamento cross-tenant é responsabilidade da camada de aplicação (mixin `TenantScopedViewSet`). Mitigamos com testes específicos e revisão.

Ver [ADR-008](../03-decisoes/adr-008-multi-tenant-row-level.md).

## Invariantes do schema

### Voto secreto
A tabela `votes` **não tem** coluna `voter_id` nem `cpf_hash`. Esta restrição é verificada por um teste de introspecção que falha se a coluna for adicionada.

### Um voto por eleitor por escrutínio
Constraint única em `voter_attendance(escrutinio_id, voter_id)`.

### Um escrutínio aberto por eleição
Index único parcial em `escrutinios(election_id) WHERE status = 'aberto'`.

### Vagas e candidatos consistentes
Check constraint em `positions(vacancies > 0)`. Validação aplicacional (não DB) para `candidates_count >= vacancies` antes de iniciar eleição.

## Convenções

- Snake_case em nomes de tabela e coluna.
- Pluralizar tabelas (`elections`, `votes`).
- Chaves primárias: `id BIGSERIAL` (Django default `BigAutoField`).
- Timestamps padrão: `created_at`, `updated_at` (Django auto). Para eventos específicos: `opened_at`, `closed_at`, `voted_at`, etc.
- Soft delete não é usado nesta fase (`DELETE` físico em testes; entidades de domínio não são deletadas em produção — apenas marcadas em estados terminais).
- `organization_id` é sempre coluna `NOT NULL` quando a entidade pertence a uma organização.

## Índices

Definidos diretamente nos modelos Django via `Meta.indexes`. Casos críticos:

- `voters(election_id, cpf_hash)` — lookup do eleitor durante validação. **Único** (CPF não pode repetir na mesma eleição).
- `votes(escrutinio_id, position_id)` — agregação para parciais e apuração.
- `votes(escrutinio_id, candidate_id)` — contagem por candidato.
- `voter_attendance(escrutinio_id, voter_id)` — único; verificação de duplo voto.
- `ballot_sessions(token)` — único; lookup durante submissão.
- `ballot_sessions(escrutinio_id, voter_id)` — único parcial onde `used_at IS NULL`, para impedir abrir múltiplas sessões simultâneas.

## Migrations

- Apenas Django migrations. Sem ferramentas paralelas tipo Alembic.
- Cada migration é revisada para idempotência manualmente; checklist em [ADR-004](../03-decisoes/adr-004-migrations-idempotentes.md).
- Migrations rodam automaticamente em `docker compose up` via entrypoint do container backend.
- Em produção, migrations rodam antes do Gunicorn iniciar (script `entrypoint.sh`).

## Seed de desenvolvimento

- Comando management custom `seed_dev` cria: 1 organização "Igreja Teste", 1 organizador (`admin@knoxis.local` / senha em env), 1 eleição em rascunho com 2 cargos, alguns candidatos e ~50 votantes fictícios.
- Não roda em produção (check de DEBUG ou env var explícita).

## Backup

- Configuração de infra, não de aplicação. Documentar em `infra/README.md` (criado na Fase 0): `pg_dump` agendado via cron no host, retenção 14 dias, destino fora do servidor (S3-compatible).
- Restore validado periodicamente (procedimento documentado, não automatizado nesta fase).

## Performance

- Volumes esperados são modestos (centenas de votantes, dezenas de candidatos, dezenas de votos por escrutínio).
- Sem necessidade de particionamento.
- Connection pooling no Django padrão (5–10 conexões com Gunicorn 2–4 workers).
- `EXPLAIN ANALYZE` nas queries de parciais e apuração antes do release de cada fase.
