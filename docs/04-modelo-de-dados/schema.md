# Modelo de dados

Schema lógico do PostgreSQL. Nomes finais podem diferir levemente quando os modelos Django gerarem as migrations, mas a estrutura semântica e as invariantes são esta.

Convenções:
- Todas as tabelas têm `id BIGSERIAL PRIMARY KEY`, `created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()`, `updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()` (omitidos abaixo, exceto quando relevantes).
- `organization_id BIGINT NOT NULL` em toda tabela de domínio (ver [ADR-008](../03-decisoes/adr-008-multi-tenant-row-level.md)).
- FKs com `ON DELETE` explicitado por relação.

## Diagrama (lógico)

```
organizations
   │
   ├── organization_members ─── users
   │
   └── elections
         ├── positions
         │     └── candidates
         │
         ├── voters
         │
         └── escrutinios
               ├── escrutinio_candidates  (snapshot dos elegíveis no escrutínio)
               ├── escrutinio_positions   (snapshot de vagas remanescentes por cargo)
               ├── ballot_sessions  ──┐
               ├── voter_attendance ──┤  (têm voter_id; SEM voto)
               ├── votes              │  (NÃO TEM voter_id)
               └── election_results   │  (resultado consolidado da apuração)
                                      │
                              (sem FK entre attendance e vote)
```

## Tabelas

### `users`
Usuários da plataforma (organizadores). Modelo customizado de `User` do Django.

| Coluna | Tipo | Constraints | Notas |
|---|---|---|---|
| id | BIGSERIAL | PK | |
| email | citext | UNIQUE NOT NULL | case-insensitive |
| name | TEXT | NOT NULL | |
| password_hash | TEXT | NOT NULL | Argon2id, gerenciado pelo Django |
| is_active | BOOLEAN | NOT NULL DEFAULT TRUE | |
| is_staff | BOOLEAN | NOT NULL DEFAULT FALSE | super-admin via Django admin |
| last_login | TIMESTAMPTZ | NULL | |
| created_at, updated_at | TIMESTAMPTZ | NOT NULL | |

### `organizations`
Tenant — uma igreja.

| Coluna | Tipo | Constraints | Notas |
|---|---|---|---|
| id | BIGSERIAL | PK | |
| name | TEXT | NOT NULL | "Igreja Presbiteriana de Cidade" |
| slug | TEXT | UNIQUE NOT NULL | usado em URLs públicas |
| city | TEXT | NULL | |
| state | CHAR(2) | NULL | UF |
| created_at, updated_at | TIMESTAMPTZ | NOT NULL | |

### `organization_members`
Vínculo de usuário a organização (com papel).

| Coluna | Tipo | Constraints | Notas |
|---|---|---|---|
| id | BIGSERIAL | PK | |
| organization_id | BIGINT | FK → organizations(id) ON DELETE CASCADE | |
| user_id | BIGINT | FK → users(id) ON DELETE CASCADE | |
| role | TEXT | NOT NULL CHECK (role IN ('owner','admin','viewer')) | |
| created_at | TIMESTAMPTZ | NOT NULL | |

**Constraint única:** `(organization_id, user_id)` — um usuário tem um único papel por organização.

### `elections`
Eleição. Pertence a uma organização.

| Coluna | Tipo | Constraints | Notas |
|---|---|---|---|
| id | BIGSERIAL | PK | |
| organization_id | BIGINT | FK → organizations(id) ON DELETE CASCADE NOT NULL | |
| name | TEXT | NOT NULL | "Eleição de oficiais 2026" |
| description | TEXT | NULL | |
| scheduled_for | DATE | NULL | data prevista |
| status | TEXT | NOT NULL DEFAULT 'rascunho' CHECK (status IN ('rascunho','pronta','em_andamento','encerrada','cancelada')) | |
| final_rule | TEXT | NOT NULL CHECK (final_rule IN ('manual','max_count')) | |
| max_escrutinios | INTEGER | NULL CHECK (max_escrutinios IS NULL OR max_escrutinios >= 1) | usado quando final_rule='max_count' |
| started_at | TIMESTAMPTZ | NULL | quando entrou em em_andamento |
| ended_at | TIMESTAMPTZ | NULL | |
| created_by | BIGINT | FK → users(id) | |

**Índices:** `(organization_id, status)`, `(organization_id, scheduled_for)`.

### `positions`
Cargo dentro de uma eleição.

| Coluna | Tipo | Constraints | Notas |
|---|---|---|---|
| id | BIGSERIAL | PK | |
| organization_id | BIGINT | FK NOT NULL | redundância para queries diretas |
| election_id | BIGINT | FK → elections(id) ON DELETE CASCADE NOT NULL | |
| name | TEXT | NOT NULL | "Presbítero", "Diácono" |
| vacancies | INTEGER | NOT NULL CHECK (vacancies >= 1) | vagas originais (não muda) |
| display_order | INTEGER | NOT NULL DEFAULT 0 | |

**Constraint única:** `(election_id, name)`.

### `candidates`
Candidato a um cargo dentro de uma eleição.

| Coluna | Tipo | Constraints | Notas |
|---|---|---|---|
| id | BIGSERIAL | PK | |
| organization_id | BIGINT | FK NOT NULL | |
| election_id | BIGINT | FK → elections(id) ON DELETE CASCADE NOT NULL | redundância |
| position_id | BIGINT | FK → positions(id) ON DELETE CASCADE NOT NULL | |
| name | TEXT | NOT NULL | nome completo |
| display_order | INTEGER | NOT NULL DEFAULT 0 | |

**Constraint única:** `(position_id, name)`.

### `voters`
Lista de eleitores aptos a votar nesta eleição (rol de membros importado).

| Coluna | Tipo | Constraints | Notas |
|---|---|---|---|
| id | BIGSERIAL | PK | |
| organization_id | BIGINT | FK NOT NULL | |
| election_id | BIGINT | FK → elections(id) ON DELETE CASCADE NOT NULL | |
| name | TEXT | NOT NULL | nome do membro |
| cpf_hash | CHAR(64) | NOT NULL | HMAC-SHA256 hex — ver [ADR-007](../03-decisoes/adr-007-armazenamento-cpf.md) |
| cpf_last2 | CHAR(2) | NOT NULL | últimos 2 dígitos para exibição |

**Constraint única:** `(election_id, cpf_hash)` — impede CPF duplicado na mesma eleição.
**Índice:** `(election_id, cpf_hash)` — lookup principal.

### `escrutinios`
Rodada de votação. Eleição pode ter várias.

| Coluna | Tipo | Constraints | Notas |
|---|---|---|---|
| id | BIGSERIAL | PK | |
| organization_id | BIGINT | FK NOT NULL | |
| election_id | BIGINT | FK → elections(id) ON DELETE CASCADE NOT NULL | |
| number | INTEGER | NOT NULL CHECK (number >= 1) | 1, 2, 3, ... |
| is_final | BOOLEAN | NOT NULL DEFAULT FALSE | |
| status | TEXT | NOT NULL DEFAULT 'preparando' CHECK (status IN ('preparando','aberto','encerrado')) | |
| opened_at | TIMESTAMPTZ | NULL | |
| closed_at | TIMESTAMPTZ | NULL | |
| total_voters | INTEGER | NULL | preenchido ao encerrar |

**Constraint única:** `(election_id, number)`.
**Índice único parcial:** `CREATE UNIQUE INDEX ... ON escrutinios(election_id) WHERE status = 'aberto';` — só um escrutínio aberto por eleição.

### `escrutinio_positions`
Snapshot de vagas remanescentes por cargo no escrutínio (fixadas na abertura).

| Coluna | Tipo | Constraints | Notas |
|---|---|---|---|
| id | BIGSERIAL | PK | |
| organization_id | BIGINT | FK NOT NULL | |
| escrutinio_id | BIGINT | FK → escrutinios(id) ON DELETE CASCADE NOT NULL | |
| position_id | BIGINT | FK → positions(id) ON DELETE RESTRICT NOT NULL | |
| vacancies_remaining | INTEGER | NOT NULL CHECK (vacancies_remaining >= 0) | |

**Constraint única:** `(escrutinio_id, position_id)`.

### `escrutinio_candidates`
Candidatos elegíveis no escrutínio (snapshot na abertura).

| Coluna | Tipo | Constraints | Notas |
|---|---|---|---|
| id | BIGSERIAL | PK | |
| organization_id | BIGINT | FK NOT NULL | |
| escrutinio_id | BIGINT | FK → escrutinios(id) ON DELETE CASCADE NOT NULL | |
| position_id | BIGINT | FK → positions(id) ON DELETE RESTRICT NOT NULL | |
| candidate_id | BIGINT | FK → candidates(id) ON DELETE RESTRICT NOT NULL | |

**Constraint única:** `(escrutinio_id, candidate_id)`.

### `ballot_sessions`
Sessão efêmera entre validação de CPF e submissão da cédula.

| Coluna | Tipo | Constraints | Notas |
|---|---|---|---|
| id | BIGSERIAL | PK | |
| organization_id | BIGINT | FK NOT NULL | |
| escrutinio_id | BIGINT | FK → escrutinios(id) ON DELETE CASCADE NOT NULL | |
| voter_id | BIGINT | FK → voters(id) ON DELETE RESTRICT NOT NULL | |
| token | CHAR(64) | NOT NULL | aleatório URL-safe, 64 hex |
| expires_at | TIMESTAMPTZ | NOT NULL | NOW() + 10min |
| used_at | TIMESTAMPTZ | NULL | preenchido na submissão |

**Constraint única:** `token` (UNIQUE).
**Índice único parcial:** `CREATE UNIQUE INDEX ... ON ballot_sessions(escrutinio_id, voter_id) WHERE used_at IS NULL;` — impede emitir múltiplas sessões abertas simultâneas para o mesmo voter no mesmo escrutínio.

### `voter_attendance`
Registro de que um eleitor votou em um escrutínio. **Sem conteúdo do voto.**

| Coluna | Tipo | Constraints | Notas |
|---|---|---|---|
| id | BIGSERIAL | PK | |
| organization_id | BIGINT | FK NOT NULL | |
| escrutinio_id | BIGINT | FK → escrutinios(id) ON DELETE CASCADE NOT NULL | |
| voter_id | BIGINT | FK → voters(id) ON DELETE RESTRICT NOT NULL | |
| voted_at | TIMESTAMPTZ | NOT NULL DEFAULT NOW() | timestamp completo |

**Constraint única:** `(escrutinio_id, voter_id)` — bloqueia voto duplo.

### `votes`
Voto anônimo. **Não tem voter_id, cpf, ballot_session_id.**

| Coluna | Tipo | Constraints | Notas |
|---|---|---|---|
| id | BIGSERIAL | PK | |
| organization_id | BIGINT | FK NOT NULL | |
| escrutinio_id | BIGINT | FK → escrutinios(id) ON DELETE RESTRICT NOT NULL | |
| position_id | BIGINT | FK → positions(id) ON DELETE RESTRICT NOT NULL | |
| candidate_id | BIGINT | FK → candidates(id) ON DELETE RESTRICT NOT NULL | |
| created_at | TIMESTAMPTZ | NOT NULL | truncado ao minuto via trigger ou na inserção (ver [ADR-002](../03-decisoes/adr-002-voto-secreto-via-sessao.md)) |

**Sem constraint única envolvendo voter ou session — porque essas colunas não existem.**
**Índices:**
- `(escrutinio_id, candidate_id)` — agregação para parciais/apuração.
- `(escrutinio_id, position_id)` — totais por cargo.

**Teste de invariante:** existe teste de introspecção que falha se `votes` ganhar coluna que identifique eleitor.

### `election_results`
Resultado consolidado da apuração, escrutínio a escrutínio.

| Coluna | Tipo | Constraints | Notas |
|---|---|---|---|
| id | BIGSERIAL | PK | |
| organization_id | BIGINT | FK NOT NULL | |
| election_id | BIGINT | FK → elections(id) ON DELETE CASCADE NOT NULL | |
| escrutinio_id | BIGINT | FK → escrutinios(id) ON DELETE CASCADE NOT NULL | |
| position_id | BIGINT | FK → positions(id) ON DELETE RESTRICT NOT NULL | |
| candidate_id | BIGINT | FK → candidates(id) ON DELETE RESTRICT NOT NULL | |
| votes_count | INTEGER | NOT NULL CHECK (votes_count >= 0) | |
| was_elected | BOOLEAN | NOT NULL DEFAULT FALSE | |
| tie_at_cutoff | BOOLEAN | NOT NULL DEFAULT FALSE | |
| tie_resolution | TEXT | NULL | nota textual da resolução manual |

**Constraint única:** `(escrutinio_id, candidate_id)`.

### `audit_log`
Trilha de auditoria de ações administrativas.

| Coluna | Tipo | Constraints | Notas |
|---|---|---|---|
| id | BIGSERIAL | PK | |
| organization_id | BIGINT | FK NULL | NULL para ações da plataforma |
| user_id | BIGINT | FK → users(id) ON DELETE SET NULL | |
| action | TEXT | NOT NULL | "election.created", "escrutinio.closed", ... |
| target_type | TEXT | NULL | |
| target_id | BIGINT | NULL | |
| payload | JSONB | NOT NULL DEFAULT '{}' | dados antes/depois, redacted |
| ip_address | INET | NULL | |
| created_at | TIMESTAMPTZ | NOT NULL DEFAULT NOW() | |

**Índices:** `(organization_id, created_at DESC)`.

## Invariantes resumidas

| Invariante | Como é garantida |
|---|---|
| Voto secreto: votes sem voter | Schema; teste de introspecção. |
| Um voto por eleitor por escrutínio | `UNIQUE (escrutinio_id, voter_id)` em voter_attendance. |
| Um escrutínio aberto por eleição | Índice único parcial em escrutinios WHERE status='aberto'. |
| Sessão ativa única por voter+escrutinio | Índice único parcial em ballot_sessions WHERE used_at IS NULL. |
| CPF único por eleição | `UNIQUE (election_id, cpf_hash)` em voters. |
| Multi-tenant scoping | `organization_id` em toda tabela + mixin obrigatório na aplicação. |
| Cargo com pelo menos 1 vaga | `CHECK (vacancies >= 1)`. |
| Apuração reproduzível | Função pura `apurador.apurar()`; `election_results` é cache consolidado. |
