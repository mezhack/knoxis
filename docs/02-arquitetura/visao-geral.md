# Arquitetura — visão geral

## Diagrama lógico

```
┌─────────────────────────────────────────────────────────────────┐
│                          Internet                                │
└──────────────────────────────┬──────────────────────────────────┘
                               │ HTTPS (443)
                       ┌───────▼────────┐
                       │     Nginx       │   TLS, gzip, rate-limit, redirect HTTP→HTTPS
                       └───┬───────┬─────┘
              /api/*       │       │      /* (SPA estática)
                     ┌─────▼──┐ ┌──▼─────────────┐
                     │ Django │ │ Static (React) │
                     │ Gunicorn│ │ Vite build     │
                     └────┬────┘ └────────────────┘
                          │
                  ┌───────▼────────┐
                  │  PostgreSQL 16  │
                  └─────────────────┘
```

Sem Redis na fase inicial. Ver [ADR-006](../03-decisoes/adr-006-sem-redis-fase-inicial.md). Polling de parciais cabe direto no Postgres.

## Componentes

### Nginx (reverse proxy + static)
- Termina TLS (Let's Encrypt via certbot, fora do escopo do código).
- Serve build estático do React em `/`.
- Repassa `/api/*` e `/admin/*` ao Gunicorn.
- Aplica rate limiting (limit_req zones para login e validação CPF).
- Cabeçalhos de segurança: HSTS, X-Content-Type-Options, X-Frame-Options, Content-Security-Policy.

### Django + DRF (Gunicorn)
- API REST sob `/api/v1/`.
- Sessão Django com cookie httpOnly para autenticação de organizadores.
- Django Admin sob `/admin/` para super-admin da plataforma (acesso restrito por IP no Nginx + superuser local).
- Apps Django propostos:
  - `accounts` — usuários, organizações, organization_members
  - `elections` — eleições, cargos, candidatos, votantes
  - `voting` — escrutínios, sessões de cédula, votos, presença, apuração
  - `reports` — agregações e renderização de relatórios
  - `core` — utilitários transversais (hash CPF, máscaras, mixins multi-tenant)

### PostgreSQL 16
- Schema único `public` com todas as tabelas.
- Multi-tenancy via coluna `organization_id` em todas as tabelas de domínio (não usamos schema-per-tenant; ver [ADR-008](../03-decisoes/adr-008-multi-tenant-row-level.md)).
- Constraints e índices garantem invariantes (ex.: um voter_id por escrutínio na `voter_attendance`).

### Frontend (React + Vite + TypeScript)
- SPA servida pelo Nginx como estático.
- Comunicação com API via fetch + cookies (sessão Django).
- TanStack Query para estado de servidor (cache, refetch, polling de parciais).
- React Router para navegação.
- Sem framework de UI pesado; componentes simples + Tailwind (proposta — ver [ADR-009](../03-decisoes/adr-009-stack-frontend.md)).
- Dois "apps" lógicos no mesmo bundle:
  - Painel do organizador (login obrigatório)
  - Cabine do eleitor (URL pública por eleição)

## Fluxos críticos

### Fluxo 1 — Voto secreto

```
Eleitor (browser)         Backend (Django)        PostgreSQL
     │                          │                       │
     ├── POST /api/v1/public/elections/{id}/identify ──►│
     │   { cpf }                │                       │
     │                          │                       │
     │                          ├── SELECT voter ───────►
     │                          │   WHERE cpf_hash = ?  │
     │                          │   AND election_id = ? │
     │                          │◄── voter ─────────────│
     │                          │                       │
     │                          ├── SELECT attendance ──►
     │                          │   WHERE voter_id = ?  │
     │                          │   AND escrutinio = ?  │
     │                          │◄── (nada) ────────────│
     │                          │                       │
     │                          ├── INSERT ballot_session ►
     │                          │   (escrutinio, voter, token, expira) │
     │                          │                       │
     │◄── 200 { session_token,  │                       │
     │       ballot_schema }    │                       │
     │                          │                       │
     ├── POST /api/v1/public/ballot ──────────────────► │
     │   Cookie: session_token  │                       │
     │   { choices: [...] }     │                       │
     │                          │                       │
     │                          ├── BEGIN TRANSACTION ──►
     │                          ├── SELECT ballot_session FOR UPDATE ►
     │                          │   (verifica não-usada, não-expirada)│
     │                          ├── SELECT escrutinio (verifica aberto)
     │                          ├── UPDATE ballot_session SET used_at = NOW() │
     │                          ├── INSERT voter_attendance ────────►
     │                          │   (escrutinio, voter_id, voted_at)│
     │                          ├── INSERT votes (N linhas, SEM voter_id) ──► │
     │                          ├── COMMIT ─────────────►
     │◄── 200 { ok: true } ─────│                       │
```

Invariante: `votes` tem apenas `(escrutinio_id, position_id, candidate_id)` — nenhuma coluna identifica o eleitor.

### Fluxo 2 — Parciais

```
Organizador (browser)     Backend                  PostgreSQL
     │                       │                          │
     ├── GET /api/v1/elections/{id}/escrutinios/{n}/parciais ►│
     │  (session admin)      │                          │
     │                       ├── SELECT agg by position ►
     │                       │  SUM(votes) GROUP BY     │
     │                       │  candidate, position     │
     │                       │◄── linhas agregadas ─────│
     │◄── { positions: [...] }                          │
     │                       │                          │
   (TanStack Query refetch a cada 3s)
```

ETag baseado em `(escrutinio.updated_at, COUNT(votes) WHERE escrutinio_id = ?)` para evitar payload repetido.

### Fluxo 3 — Encerramento de escrutínio (apuração)

```
Organizador                Backend                    PostgreSQL
     │                          │                          │
     ├── POST /api/v1/escrutinios/{id}/encerrar ─────────►│
     │                          ├── BEGIN ─────────────────►
     │                          ├── UPDATE escrutinio SET status='encerrado', closed_at=NOW() │
     │                          ├── Para cada cargo:       │
     │                          │   - COUNT votantes do escrutínio │
     │                          │   - Calcular limiar      │
     │                          │   - Selecionar eleitos   │
     │                          │   - INSERT election_results (escrutinio, cargo, candidato, votos, eleito, empate_corte) │
     │                          ├── Se todas vagas preenchidas: UPDATE eleicao SET status='encerrada' │
     │                          ├── COMMIT ────────────────►
     │◄── { resultados, empates? } ─────                   │
```

## Decisões transversais

- **Sem WebSocket nem SSE na fase 1.** Polling resolve as parciais. Ver [ADR-003](../03-decisoes/adr-003-parciais-em-tempo-real.md).
- **Sem Celery/Redis.** Importação de CSV roda sincronamente; relatórios são consultas SQL.
- **Sem object storage externo.** Fotos de candidatos (futuro) ficam em `media/` no volume Docker.
- **Locale `pt-BR`, timezone `America/Sao_Paulo`.**
