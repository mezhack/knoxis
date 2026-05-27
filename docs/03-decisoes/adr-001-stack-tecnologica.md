# ADR-001 — Stack tecnológica

**Status:** accepted
**Data:** 2026-05-26

## Contexto

Knoxis começa atendendo uma igreja, mas a visão de produto é multi-tenant: cada igreja é um cliente com seu organizador, seu rol de membros, seu histórico de eleições. Isso impõe necessidades de:

- Autenticação robusta com múltiplos usuários
- Painel administrativo (utilidade interna durante operação)
- ORM forte para multi-tenant com queries seguras por padrão
- Migrations confiáveis e idempotentes
- Boa ergonomia para construção rápida de CRUDs e relatórios

O backend foi explicitamente decidido como Python; falta escolher framework. Frontend será React + Vite. Banco será PostgreSQL.

## Decisão

- **Backend:** Python 3.12 + **Django 5.x** + Django REST Framework (DRF)
- **Frontend:** React 18 + TypeScript + Vite
- **Banco:** PostgreSQL 16

## Justificativa

### Por que Django (em vez de FastAPI ou Flask)?

- **Multi-tenant maduro:** ORM + middleware permitem padrões de scoping limpos. FastAPI exigiria reinventar com SQLAlchemy + dependências.
- **Admin embutido:** acelera operações de suporte e debug em produção (super-admin da plataforma).
- **Auth e segurança batteries-included:** Argon2, session, CSRF, password validators, signing — tudo testado. FastAPI exigiria montar.
- **Migrations idempotentes nativas:** o sistema de migrations do Django é o estado-da-arte; idempotência adicional é uma camada fina por cima.
- **DRF maduro para a API REST consumida pelo React:** browsable API ajuda em dev, serializers cobrem 90% dos casos.
- **Crescimento de produto:** quando vier faturamento, planos, convites, dashboards internos, Django entrega tudo isso com menos código.

### O que perdemos vs FastAPI

- Async first-class — não é necessidade real aqui (volume modesto, queries simples).
- OpenAPI automático mais rico — DRF tem `drf-spectacular`, suficiente.
- "Modernidade" percebida — irrelevante para o produto.

### Por que React + Vite (em vez de Next.js / Remix)?

- SPA serve bem dois apps distintos (admin e cabine do eleitor) sem SSR complicado.
- Vite tem DX excelente, build rápido, sem o peso do framework.
- Sem necessidade de SEO (sistema interno de votação).
- Deploy é mais simples: pasta estática + nginx.

### Por que PostgreSQL (não havia alternativa)

- Confiabilidade, JSONB, índices parciais, constraints expressivas.
- Já era a escolha do usuário.

## Consequências

### Positivas
- Aceleração na construção de CRUDs.
- Padrões claros para multi-tenant scoping.
- Admin embutido reduz necessidade de tooling externo no início.
- Stack amplamente conhecida, mais fácil contratar/colaborar.

### Negativas
- Django é menos "leve" que FastAPI — tempo de startup maior, mais dependências. Aceitável.
- O acoplamento DRF ↔ Django dificulta migrar parte da API depois. Aceitável dado o escopo.

## Alternativas consideradas

### FastAPI + SQLAlchemy + Alembic
- Mais leve. Async nativo. Comunidade em alta.
- Rejeitado: produto requer admin, multi-tenant, auth, migrations — todos os "extras" que Django entrega prontos. O ganho de "leveza" não compensa o overhead de construir esses pilares.

### Flask + extensões
- Pior dos dois mundos: minimalista demais para o escopo, sem padrões fortes.
- Rejeitado.

### Next.js full-stack
- Frontend + API juntos.
- Rejeitado: o time/usuário escolheu Python para backend. Next.js full-stack desviaria dessa decisão.
