# Backend

## Stack

- Python 3.12
- Django 5.x
- Django REST Framework (DRF)
- psycopg 3
- Argon2 (`django-argon2-hasher` via `argon2-cffi`)
- `django-cors-headers` (apenas origens próprias)
- `django-axes` para bloqueio de login por força bruta
- `python-dotenv` para variáveis de ambiente em dev
- Pytest + pytest-django para testes
- Ruff + Black para lint/format

## Organização de apps

```
backend/
├── manage.py
├── pyproject.toml
├── knoxis/                  # projeto Django (settings, urls, wsgi, asgi)
│   ├── settings/
│   │   ├── base.py
│   │   ├── dev.py
│   │   └── prod.py
│   ├── urls.py
│   └── wsgi.py
├── apps/
│   ├── core/                # utilidades transversais
│   │   ├── cpf.py           # validação, hash, máscara
│   │   ├── mixins.py        # TenantScopedQuerySet, TenantScopedViewSet
│   │   └── permissions.py   # IsOrganizationMember, IsOwner, etc.
│   ├── accounts/            # User, Organization, OrganizationMember
│   │   ├── models.py
│   │   ├── views.py
│   │   ├── serializers.py
│   │   └── urls.py
│   ├── elections/           # Election, Position, Candidate, Voter
│   │   └── ...
│   ├── voting/              # Escrutinio, BallotSession, Vote, VoterAttendance, Apurar
│   │   ├── models.py
│   │   ├── apurador.py      # função pura: dado (votos, vagas, is_final) → eleitos/empates
│   │   ├── views.py
│   │   └── ...
│   └── reports/             # endpoints e agregações para relatórios
└── tests/
    ├── unit/
    ├── integration/
    └── conftest.py
```

## Padrões

### Multi-tenant
- Todo `ViewSet` de domínio herda de `TenantScopedViewSet` (definido em `apps/core/mixins.py`).
- O mixin sobrescreve `get_queryset()` para filtrar por `organization_id = request.user.current_organization_id`.
- Toda criação injeta `organization_id` automaticamente; ignorando qualquer valor enviado pelo cliente.

### Serializers
- DRF ModelSerializer para CRUD básico.
- Serializers de domínio (apuração, parciais) são plain `Serializer` com `to_representation` explícito.
- Validação de regras de negócio no serializer (`validate_*` e `validate`), não no view.

### Endpoints públicos vs autenticados
- Rotas sob `/api/v1/public/...` são acessadas pelo eleitor — sem login.
- Rotas sob `/api/v1/admin/...` exigem sessão de organizador (`IsAuthenticated` + `IsOrganizationMember`).
- Rate limit por IP usando `django-ratelimit` (decorator nas views públicas).

### Transações
- Submissão de voto: `transaction.atomic()` + `select_for_update()` na `ballot_session` para evitar double-spend em concorrência.
- Encerramento de escrutínio: `transaction.atomic()` em torno de toda a apuração.

### Funções de domínio puras
- `apps/voting/apurador.py` define `apurar(escrutinio: Escrutinio) -> ResultadoApuracao` como função pura: lê do BD, calcula, retorna estrutura, não escreve.
- A view chama `apurar()` e depois persiste o resultado em `transaction.atomic()`. Testes unitários cobrem o apurador sem tocar no BD via fixtures.

### Configuração
- Settings divididos em `base.py` (comum), `dev.py` (DEBUG, sqlite opcional), `prod.py` (Postgres, ALLOWED_HOSTS strict, cookies seguros).
- Variáveis sensíveis (`SECRET_KEY`, `CPF_HMAC_KEY`, `DATABASE_URL`) carregadas de env vars. Documentar em `.env.example`.

### Logs
- `structlog` com formato JSON em produção, plain em dev.
- Middleware adiciona `request_id` (UUID) por requisição, propagado em todos os logs daquele request.
- Logger nunca recebe `cpf` cru; um helper `mascarar_cpf(cpf)` é usado obrigatoriamente. Lint rule via Ruff (`flake8-bugbear` custom check ou code review).

### Migrations
- Geradas via `python manage.py makemigrations`.
- Toda nova migration **deve ser revisada manualmente** para idempotência (ver [ADR-004](../03-decisoes/adr-004-migrations-idempotentes.md)).
- Migrations de dados (`RunPython`) sempre com `reverse_code` definido (mesmo que `noop`) e check de existência antes de inserir/atualizar.

## Testes

- **Unitários** (`tests/unit/`): funções puras (apurador, validador de CPF, hash), serializers isolados.
- **Integração** (`tests/integration/`): viewsets com DB de teste, fluxos completos (criar eleição → abrir escrutínio → votar → encerrar → apurar → relatório).
- **Multi-tenant**: testes explícitos verificam que User A não enxerga dados da Organização B.
- **Segurança**: testes verificam que coluna `voter_id` NÃO existe na tabela `votes` (introspecção). Verifica que log de auditoria não vaza CPF.
- Cobertura mínima: 80% em `apps/voting` (núcleo crítico).

## Dependências externas

Mínimas. Lista final em `pyproject.toml` quando entrar a Fase 0.

## CORS

- Em produção, frontend e backend ficam atrás do mesmo Nginx (mesmo origem). CORS não necessário.
- Em dev, `django-cors-headers` libera `http://localhost:5173` (porta padrão do Vite) com credenciais.
