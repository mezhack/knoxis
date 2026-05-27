# ADRs — Architecture Decision Records

Decisões de arquitetura registradas em ordem cronológica. Cada ADR é imutável após "aceito" — alterações geram um novo ADR que substitui (status `supersedes` / `superseded by`).

## Formato

Cada ADR tem:
- **Status:** proposed | accepted | superseded
- **Contexto:** o problema e as forças em jogo
- **Decisão:** o que foi decidido
- **Consequências:** o que ganhamos e o que abrimos mão
- **Alternativas consideradas:** opções rejeitadas e por quê

## Índice

| ID | Título | Status |
|---|---|---|
| [ADR-001](adr-001-stack-tecnologica.md) | Stack tecnológica: Django + DRF, React+Vite, PostgreSQL | accepted |
| [ADR-002](adr-002-voto-secreto-via-sessao.md) | Voto secreto via sessão de cédula efêmera + invariante de schema | accepted |
| [ADR-003](adr-003-parciais-em-tempo-real.md) | Parciais em tempo real via polling, sem WebSocket/SSE | accepted |
| [ADR-004](adr-004-migrations-idempotentes.md) | Migrations idempotentes obrigatórias | accepted |
| [ADR-005](adr-005-autenticacao-admin.md) | Autenticação de organizador via sessão httpOnly + Argon2id + CSRF | accepted |
| [ADR-006](adr-006-sem-redis-fase-inicial.md) | Sem Redis na fase inicial | accepted |
| [ADR-007](adr-007-armazenamento-cpf.md) | Armazenamento de CPF: hash HMAC determinístico, sem texto claro | accepted |
| [ADR-008](adr-008-multi-tenant-row-level.md) | Multi-tenant via row-level (organization_id em todas as tabelas) | accepted |
| [ADR-009](adr-009-stack-frontend.md) | Stack frontend: TanStack Query + Tailwind + React Hook Form | accepted |
