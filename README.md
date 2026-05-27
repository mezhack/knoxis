# Knoxis

Plataforma de votação para igrejas conduzirem eleições internas de forma segura, auditável e em conformidade com seus editais.

O caso de uso inicial é a eleição de presbíteros e diáconos na Igreja Presbiteriana do Brasil (IPB), seguindo a tradição de cédula única, voto secreto e múltiplos escrutínios por maioria simples.

## Estado atual

Em fase de planejamento. Este repositório contém **apenas documentação** — nenhum código de aplicação foi escrito ainda. O desenvolvimento seguirá o formato SDD (Specs Driven Development): especificações primeiro, implementação progressiva em fases testáveis individualmente.

## Onde começar

- [docs/00-visao-geral.md](docs/00-visao-geral.md) — problema, escopo e visão geral
- [docs/01-especificacoes/](docs/01-especificacoes/) — requisitos, regras de negócio, histórias de usuário, glossário
- [docs/02-arquitetura/](docs/02-arquitetura/) — visão arquitetural por camada
- [docs/03-decisoes/](docs/03-decisoes/) — ADRs (Architecture Decision Records)
- [docs/04-modelo-de-dados/schema.md](docs/04-modelo-de-dados/schema.md) — modelo de dados
- [docs/05-api/contratos.md](docs/05-api/contratos.md) — contratos REST
- [docs/06-roadmap/fases.md](docs/06-roadmap/fases.md) — plano de fases
- [docs/06-roadmap/todo.md](docs/06-roadmap/todo.md) — TODO consolidado
- [docs/07-futuro/funcionalidades-futuras.md](docs/07-futuro/funcionalidades-futuras.md) — backlog de fase 2+

## Stack (proposta — ver ADR-001)

- Backend: Python 3.12 + Django 5 + Django REST Framework
- Frontend: React 18 + Vite + TypeScript
- Banco: PostgreSQL 16
- Sem Redis na fase inicial (ver ADR-006)

## Princípios inegociáveis

1. **Zero regressões.** Cada fase preserva o que foi entregue antes.
2. **Migrations idempotentes.** Rodar duas vezes não quebra (ver ADR-004).
3. **Documentação é fonte de verdade.** Contratos mudaram? Doc atualiza no mesmo commit.
4. **Voto secreto verificável.** Identidade e conteúdo do voto nunca podem ser ligados após o registro.
