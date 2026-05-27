# Contratos de API

Versão: `/api/v1/`. Todos os endpoints retornam JSON. Erros seguem RFC 7807 (Problem Details) simplificado.

## Convenções

### Formato de erro
```json
{
  "type": "validation_error",
  "title": "Dados inválidos",
  "status": 400,
  "detail": "CPF inválido.",
  "fields": {
    "cpf": ["formato inválido"]
  }
}
```

### Status codes
- `200` OK
- `201` Created
- `204` No Content
- `304` Not Modified (parciais com ETag)
- `400` Validation
- `401` Unauthenticated
- `403` Forbidden / Permission
- `404` Not Found (inclui acesso cross-tenant)
- `409` Conflict (ex.: tentar abrir escrutínio com outro aberto)
- `422` Unprocessable (regra de negócio)
- `429` Too Many Requests
- `500` Server error

### Autenticação
- Rotas sob `/api/v1/admin/*`: sessão Django via cookie + CSRF token em `X-CSRFToken`.
- Rotas sob `/api/v1/public/*`: sem login; algumas usam cookie `ballot_session` (definido após validação de CPF).
- `/api/v1/csrf` retorna o cookie CSRF; chamada no bootstrap do SPA.

### Multi-tenant
- A sessão do organizador define a "organização atual" (`request.current_organization`). Endpoints admin filtram automaticamente. Tentar acessar recurso de outra organização retorna 404 (não 403, para não revelar existência).

### Rate limiting
- `POST /admin/auth/login`: 5 / 15min / IP.
- `POST /public/elections/{slug}/identify`: 10 / 5min / IP.
- `POST /public/ballot/submit`: 1 / sessão (constraint de uso único).

---

## Endpoints — Autenticação e conta

### `POST /api/v1/admin/auth/signup`
Cria conta + organização (caso inicial).

**Body:**
```json
{
  "name": "João Pedro",
  "email": "joao@igreja.com",
  "password": "...",
  "organization": {
    "name": "Igreja Presbiteriana de Cidade",
    "slug": "ipb-cidade",
    "city": "Cidade",
    "state": "SP"
  }
}
```
**Response 201:**
```json
{ "user": { "id": 1, "name": "...", "email": "..." }, "organization": { "id": 1, "slug": "ipb-cidade" } }
```
Faz auto-login (cookie de sessão setado).

### `POST /api/v1/admin/auth/login`
**Body:** `{ "email": "...", "password": "..." }`
**Response 200:** `{ "user": {...}, "organizations": [{...}] }`

### `POST /api/v1/admin/auth/logout`
**Response 204.**

### `GET /api/v1/admin/me`
Retorna usuário logado + organização atual + papel. Usado no bootstrap do SPA.

**Response 200:**
```json
{
  "user": { "id": 1, "name": "João", "email": "..." },
  "current_organization": { "id": 1, "slug": "ipb-cidade", "name": "..." },
  "role": "owner"
}
```

### `GET /api/v1/csrf`
**Response 204** com `Set-Cookie: csrftoken=...`.

---

## Endpoints — Eleições (admin)

### `GET /api/v1/admin/elections`
Lista eleições da organização atual.

**Response 200:**
```json
{
  "items": [
    {
      "id": 1,
      "name": "Eleição de oficiais 2026",
      "status": "rascunho",
      "scheduled_for": "2026-06-15",
      "positions_count": 2,
      "voters_count": 0,
      "current_escrutinio_number": null
    }
  ]
}
```

### `POST /api/v1/admin/elections`
**Body:**
```json
{
  "name": "Eleição de oficiais 2026",
  "description": "Conforme edital nº X",
  "scheduled_for": "2026-06-15",
  "final_rule": "max_count",
  "max_escrutinios": 3
}
```
**Response 201:** election object.

### `GET /api/v1/admin/elections/{id}`
Retorna eleição com cargos, candidatos (resumo), e contadores.

### `PATCH /api/v1/admin/elections/{id}`
Edita campos da eleição. Restrições por estado:
- `rascunho` / `pronta`: tudo editável.
- `em_andamento`: apenas `description` e ampliar `max_escrutinios`.
- `encerrada` / `cancelada`: nada editável.

### `POST /api/v1/admin/elections/{id}/start`
Transita para `em_andamento` e cria 1º escrutínio em `preparando`.
**422** se pré-requisitos não atendidos (retorna lista de pendências em `fields.requisitos`).

### `POST /api/v1/admin/elections/{id}/cancel`
Cancela eleição (exige confirmação no payload):
**Body:** `{ "confirm": "CANCELAR" }`
**409** se eleição já encerrada.

---

## Endpoints — Cargos e candidatos

### `POST /api/v1/admin/elections/{id}/positions`
**Body:** `{ "name": "Presbítero", "vacancies": 4 }`

### `PATCH /api/v1/admin/positions/{id}` / `DELETE /api/v1/admin/positions/{id}`
Edições restritas pelo estado da eleição (ver `PATCH /elections/{id}`).

### `POST /api/v1/admin/positions/{id}/candidates`
**Body:** `{ "name": "Fulano de Tal" }`

### `PATCH /api/v1/admin/candidates/{id}` / `DELETE /api/v1/admin/candidates/{id}`

---

## Endpoints — Lista de votantes

### `POST /api/v1/admin/elections/{id}/voters/import`
**Body (multipart):** arquivo CSV com cabeçalho `cpf,nome`.

**Response 200:**
```json
{
  "imported": 87,
  "skipped_duplicate": 3,
  "skipped_invalid": 2,
  "errors": [
    { "line": 14, "reason": "CPF inválido", "value_last2": "99" },
    { "line": 27, "reason": "duplicado", "value_last2": "12" }
  ]
}
```

### `GET /api/v1/admin/elections/{id}/voters`
Lista paginada com `name` e `cpf_masked` (`***.***.***-XX`).

### `DELETE /api/v1/admin/voters/{id}`
Remove um votante (apenas com eleição em `rascunho` ou `pronta`).

---

## Endpoints — Escrutínios

### `GET /api/v1/admin/elections/{id}/escrutinios`
Lista todos os escrutínios da eleição.

### `GET /api/v1/admin/escrutinios/{id}`
Detalhe com posições, candidatos elegíveis, status, contagem de votos atual (se aberto, contagem agregada para o organizador).

### `POST /api/v1/admin/escrutinios/{id}/open`
Abre o escrutínio. Calcula snapshot de elegíveis e vagas remanescentes.
**409** se já existe outro aberto.

### `POST /api/v1/admin/escrutinios/{id}/close`
Encerra e roda apuração.
**Body:** `{ "confirm": true }`
**Response 200:**
```json
{
  "escrutinio": { "id": 1, "status": "encerrado", "total_voters": 60 },
  "results": [
    {
      "position": { "id": 10, "name": "Presbítero" },
      "vacancies": 4,
      "threshold": 31,
      "candidates": [
        { "id": 100, "name": "A", "votes": 50, "elected": true, "tie_at_cutoff": false },
        { "id": 101, "name": "B", "votes": 45, "elected": true, "tie_at_cutoff": false },
        { "id": 102, "name": "C", "votes": 32, "elected": true, "tie_at_cutoff": false },
        { "id": 103, "name": "D", "votes": 28, "elected": false, "tie_at_cutoff": false }
      ],
      "remaining_vacancies": 1,
      "tie_pending": false
    }
  ],
  "election_status": "em_andamento"
}
```

### `POST /api/v1/admin/elections/{id}/escrutinios`
Cria próximo escrutínio (em `preparando`), herdando candidatos remanescentes.
**Body:** `{ "is_final": false }`

### `PATCH /api/v1/admin/escrutinios/{id}`
Altera `is_final` enquanto `preparando`.

### `GET /api/v1/admin/escrutinios/{id}/parciais`
Contagem em tempo real durante escrutínio aberto.
**Headers:** `If-None-Match: <etag>` opcional.
**Response 200 (ou 304):**
```json
{
  "etag": "v60-a8c2d1",
  "voters_so_far": 60,
  "positions": [
    {
      "position": { "id": 10, "name": "Presbítero", "vacancies_remaining": 4 },
      "candidates": [
        { "id": 100, "name": "A", "votes": 50 },
        { "id": 101, "name": "B", "votes": 45 }
      ]
    }
  ]
}
```
Acesso apenas autenticado.

### `POST /api/v1/admin/escrutinios/{id}/positions/{position_id}/resolve-tie`
Resolve empate na linha de corte registrado durante apuração.
**Body:**
```json
{
  "action": "elect_candidate",
  "candidate_id": 102,
  "note": "Empate resolvido por sorteio na assembleia, ata fls. 12."
}
```
Ações possíveis:
- `elect_candidate` (+ `candidate_id`): elege um e marca o outro como remanescente.
- `defer_to_next` (+ `note`): leva ambos ao próximo escrutínio.
- `elect_both` (+ `note`): registra ambos como eleitos (requer ajuste de vagas — exige flag `vacancies_adjusted: true`).

**Response 200** com snapshot atualizado.

---

## Endpoints — Relatórios

### `GET /api/v1/admin/elections/{id}/relatorios`
Lista escrutínios encerrados com sumário (votantes, abstenção, eleitos).

### `GET /api/v1/admin/escrutinios/{id}/relatorio`
Dados estruturados para a página impressível.

**Response 200:**
```json
{
  "election": { "id": 1, "name": "...", "organization": { "name": "...", "city": "...", "state": "..." } },
  "escrutinio": { "id": 5, "number": 2, "is_final": false, "opened_at": "...", "closed_at": "..." },
  "totals": { "voters": 55, "previous_voters": 60, "abstention": 5 },
  "positions": [
    {
      "position": { "id": 10, "name": "Presbítero" },
      "vacancies_in_round": 1,
      "threshold": 28,
      "candidates": [
        { "id": 102, "name": "C", "votes": 30, "elected": true },
        { "id": 103, "name": "D", "votes": 25, "elected": false }
      ]
    }
  ]
}
```

---

## Endpoints — Cabine do eleitor (público)

### `GET /api/v1/public/elections/{slug}`
Retorna estado da eleição na URL pública (sem dados sensíveis).

**Response 200:**
```json
{
  "election": { "name": "...", "organization_name": "...", "status": "em_andamento" },
  "current_escrutinio": { "number": 2, "status": "aberto" }
}
```
Ou se nada aberto:
```json
{
  "election": { ... },
  "current_escrutinio": null,
  "message": "Não há escrutínio aberto no momento."
}
```

### `POST /api/v1/public/elections/{slug}/identify`
**Body:** `{ "cpf": "123.456.789-09" }`
**Response 200:**
```json
{
  "ballot": {
    "escrutinio_number": 2,
    "positions": [
      {
        "id": 10,
        "name": "Presbítero",
        "vacancies": 1,
        "candidates": [
          { "id": 102, "name": "C" },
          { "id": 103, "name": "D" }
        ]
      }
    ]
  }
}
```
+ `Set-Cookie: ballot_session=<token>; HttpOnly; Secure; SameSite=Lax; Max-Age=600; Path=/api/v1/public/ballot`

**400** CPF inválido.
**404** CPF não localizado.
**409** já votou neste escrutínio.

### `POST /api/v1/public/ballot/submit`
Requer cookie `ballot_session`. CSRF token também (mesmo sendo público — para evitar submission por terceiros via CSRF).
**Body:**
```json
{
  "choices": [
    { "position_id": 10, "candidate_ids": [102] },
    { "position_id": 11, "candidate_ids": [200, 201, 202, 203, 204] }
  ]
}
```
**Response 200:** `{ "ok": true, "message": "Voto registrado com sucesso." }`
**400** quantidade de marcações diferente das vagas do cargo.
**409** sessão expirada / já usada / escrutínio encerrou.

---

## Endpoints — Utilitários

### `GET /api/v1/healthz`
Healthcheck simples — `200 OK` com `{"status":"ok"}`.

### `GET /api/v1/version`
Retorna versão do build e commit hash (útil para suporte).
