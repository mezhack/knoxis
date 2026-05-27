# TODO consolidado

Visão flat de tudo que precisa ser feito, agrupado por fase. Use este arquivo como checklist enquanto implementa. Itens marcados `[~]` são opcionais ou de baixa prioridade dentro da fase. Itens com `→ RFu-XXX` apontam para [funcionalidades-futuras.md](../07-futuro/funcionalidades-futuras.md) e **não devem ser feitos** nesta fase 1.

---

## Pendências do planejamento (antes da Fase 0)

- [ ] Validar com o usuário a estrutura proposta (revisão das specs).
- [ ] Decidir nome de domínio para a plataforma (knoxis.app, knoxis.com.br, ...).
- [ ] Decidir provedor de VPS e tamanho inicial.
- [ ] Gerar chave inicial `CPF_HMAC_KEY` (procedimento: openssl rand -hex 32).
- [ ] Definir email de envio (SMTP) para a fase 2+ (recuperação de senha entrará como RFu).

---

## Fase 0 — Fundação

- [ ] Estrutura `backend/` (apps: core, accounts, elections, voting, reports).
- [ ] Estrutura `frontend/` (modules: admin, voter).
- [ ] `docker-compose.yml` (postgres, backend, frontend dev).
- [ ] `pyproject.toml` com Django 5, DRF, psycopg, argon2-cffi, django-cors-headers, django-axes, django-ratelimit, structlog, pytest-django, ruff, black.
- [ ] `package.json` com React 18, react-router-dom 6, @tanstack/react-query, zustand, tailwindcss, @headlessui/react, react-hook-form, zod, date-fns, vitest, @testing-library/react.
- [ ] Settings split: `base.py`, `dev.py`, `prod.py`.
- [ ] Locale `pt-BR`, timezone `America/Sao_Paulo`.
- [ ] Argon2 como hasher primário em `PASSWORD_HASHERS`.
- [ ] `/api/v1/healthz` (DRF view simples).
- [ ] CI: lint (ruff, eslint), pytest, vitest, double-migrate check.
- [ ] `.env.example` documentando `SECRET_KEY`, `CPF_HMAC_KEY`, `DATABASE_URL`, `ALLOWED_HOSTS`.

---

## Fase 1 — Contas e organizações

- [ ] Modelo `User` (AbstractBaseUser custom — `email` como USERNAME_FIELD).
- [ ] Modelo `Organization` (`name`, `slug`, `city`, `state`).
- [ ] Modelo `OrganizationMember` (`organization`, `user`, `role`).
- [ ] Migration inicial — verificar idempotência.
- [ ] Mixin `TenantScopedViewSet` em `apps/core/mixins.py`.
- [ ] Permission `IsOrganizationMember` em `apps/core/permissions.py`.
- [ ] Endpoint `POST /admin/auth/signup` (cria User + Organization + Member owner).
- [ ] Endpoint `POST /admin/auth/login` (django.contrib.auth, axes).
- [ ] Endpoint `POST /admin/auth/logout`.
- [ ] Endpoint `GET /admin/me`.
- [ ] Endpoint `GET /csrf`.
- [ ] Settings: `SESSION_COOKIE_HTTPONLY`, `_SECURE`, `_SAMESITE`, `_AGE`. CSRF idem.
- [ ] `django-axes`: 5 falhas / 30min cooloff, tracking por username+ip.
- [ ] Frontend: lib `api.ts` com fetch + cookie + CSRF header automático.
- [ ] Frontend: páginas LoginPage, SignupPage, OrgChoosePage (placeholder), HomePage admin.
- [ ] Frontend: hook `useAuth` lendo `/admin/me`.
- [ ] Testes: signup feliz; login feliz; login com senha errada; lockout após 5 falhas; cross-tenant baseline (User A → 404 em recurso de Org B).
- [ ] Auditoria: log de signup e login (sucesso e falha sem senha).

---

## Fase 2 — Configuração de eleição

- [ ] Modelo `Election` (status, final_rule, max_escrutinios, ...).
- [ ] Modelo `Position` (election, name, vacancies, display_order).
- [ ] Modelo `Candidate` (position, name, display_order).
- [ ] Modelo `Voter` (election, name, cpf_hash, cpf_last2).
- [ ] Utilitário `apps/core/cpf.py`: `normalize`, `is_valid`, `hash`, `mask`, `last2`.
- [ ] Endpoint CRUD `/admin/elections`.
- [ ] Endpoint CRUD `/admin/elections/{id}/positions`.
- [ ] Endpoint CRUD `/admin/positions/{id}/candidates`.
- [ ] Endpoint `POST /admin/elections/{id}/voters/import` (multipart CSV).
- [ ] Endpoint `GET /admin/elections/{id}/voters` paginado, mascarado.
- [ ] Endpoint `DELETE /admin/voters/{id}`.
- [ ] Endpoint `POST /admin/elections/{id}/start` com validação de pré-requisitos.
- [ ] Endpoint `POST /admin/elections/{id}/cancel`.
- [ ] Validação no serializer: bloquear edição conforme `status` (regras em RN-7 / RF-015).
- [ ] Frontend: ElectionListPage, ElectionFormPage, ElectionDashboardPage (placeholder).
- [ ] Frontend: componente de upload CSV com preview de erros.
- [ ] Auditoria: criar/editar eleição, importar lista (sem CPFs no payload).
- [ ] Testes: CRUD; import com casos: csv ok, csv duplicados, csv inválidos, csv vazio, csv sem header; start com pré-req faltando; multi-tenant em todos os viewsets novos.

---

## Fase 3 — Votação básica (1 escrutínio)

- [ ] Modelo `Escrutinio` (election, number, is_final, status).
- [ ] Modelo `EscrutinioPosition` (escrutinio, position, vacancies_remaining).
- [ ] Modelo `EscrutinioCandidate` (escrutinio, position, candidate).
- [ ] Modelo `BallotSession` (escrutinio, voter, token, expires_at, used_at).
- [ ] Modelo `VoterAttendance` (escrutinio, voter, voted_at).
- [ ] Modelo `Vote` (escrutinio, position, candidate, created_at) — **sem voter_id**.
- [ ] Migration: índice único parcial em `escrutinios(election) WHERE status='aberto'`.
- [ ] Migration: índice único parcial em `ballot_sessions(escrutinio, voter) WHERE used_at IS NULL`.
- [ ] Migration: índice em `votes(escrutinio, candidate)`.
- [ ] Migration: truncamento de `votes.created_at` ao minuto (trigger ou na lógica).
- [ ] Endpoint `POST /admin/escrutinios/{id}/open` cria snapshots (positions, candidates).
- [ ] Endpoint `GET /public/elections/{slug}` (estado público).
- [ ] Endpoint `POST /public/elections/{slug}/identify` com rate limit.
- [ ] Endpoint `POST /public/ballot/submit` com transação SELECT FOR UPDATE.
- [ ] Cookie `ballot_session` httpOnly/Secure/SameSite/Path=/api/v1/public/ballot.
- [ ] Validação de cédula: número de marcações por cargo == vagas.
- [ ] Frontend cabine: ElectionEntryPage (CPF), BallotPage, ConfirmationPage.
- [ ] Frontend cabine — **mobile-first**:
  - [ ] Fonte base 16px (`html { font-size: 16px }`) para evitar zoom iOS no foco de input.
  - [ ] Input de CPF com `inputmode="numeric"`, `autocomplete="off"`, máscara `000.000.000-00` via JS.
  - [ ] Cada cargo em seção própria com contador `sticky top-0`.
  - [ ] Botão "Confirmar voto" `sticky bottom-0` com sombra superior.
  - [ ] Áreas tocáveis ≥ 44x44px em todos os checkboxes/labels e botões.
  - [ ] Tela de revisão como página cheia (sem modal sobreposto).
  - [ ] Screenshots em 320, 375, 412, 768, 1440 px anexados ao PR.
  - [ ] Verificação manual em Safari iOS real (ou emulador) e Chrome Android.
- [ ] Frontend admin: tela de iniciar escrutínio.
- [ ] Teste de introspecção: schema da `votes` não tem voter_id, cpf_hash, ballot_session_id.
- [ ] Teste: dois submits concorrentes da mesma sessão → um vence, um falha (409).
- [ ] Teste: CPF não cadastrado → 404; CPF que já votou → 409; cédula com nº errado → 400.
- [ ] Teste: validação de CPF (verificadores, CPFs notoriamente inválidos).
- [ ] Rate limit verificado em testes (mock do timer).

---

## Fase 4 — Múltiplos escrutínios e apuração

- [ ] Modelo `ElectionResult` (escrutinio, position, candidate, votes_count, was_elected, tie_at_cutoff, tie_resolution).
- [ ] `apps/voting/apurador.py` com `apurar(escrutinio) -> ResultadoApuracao` — função pura.
- [ ] Endpoint `POST /admin/escrutinios/{id}/close` (transação atômica + grava `election_results`).
- [ ] Endpoint `POST /admin/elections/{id}/escrutinios` (próximo, herda remanescentes).
- [ ] Endpoint `PATCH /admin/escrutinios/{id}` (toggle `is_final` enquanto preparing).
- [ ] Endpoint `POST /admin/escrutinios/{id}/positions/{pos}/resolve-tie`.
- [ ] Lógica `final_rule=max_count`: ao criar escrutínio cujo `number == max_escrutinios`, setar `is_final=true` automaticamente.
- [ ] Lógica de transição `election.status -> encerrada` quando todas vagas preenchidas.
- [ ] Frontend admin: EscrutinioResultadoPage com destaque de eleitos.
- [ ] Frontend admin: tela de criar próximo escrutínio (com info "ainda restam X vagas em Y cargos").
- [ ] Frontend admin: tela de resolução de empate.
- [ ] Testes do apurador (unitários, sem DB) cobrindo todos os cenários de RN-2 / RN-3.
- [ ] Testes integração: ciclo completo de 3 escrutínios em uma eleição.
- [ ] Teste: tentar abrir próximo escrutínio com empate pendente → 409.
- [ ] Teste: contagem zera entre escrutínios.

---

## Fase 5 — Parciais e relatórios

- [ ] Endpoint `GET /admin/escrutinios/{id}/parciais` com ETag baseado em `(escrutinio.status, count_votes)`.
- [ ] Endpoint `GET /admin/escrutinios/{id}/relatorio`.
- [ ] Endpoint `GET /admin/elections/{id}/relatorios` (lista resumo).
- [ ] Frontend admin: EscrutinioParciaisPage (rota dedicada, polling 3s, "abrir em nova aba").
- [ ] Frontend admin: RelatorioImpressoPage com CSS print otimizado.
- [ ] Botão "Imprimir" disparando `window.print()`.
- [ ] Cálculo de abstenção no endpoint de relatório.
- [ ] Audit logs para `escrutinio.open` e `escrutinio.close`.
- [ ] Testes: parciais sem cookie de admin → 401; ETag retorna 304; abstenção calculada corretamente.
- [ ] Smoke test manual de impressão em A4.

---

## Fase 6 — Polimento e hardening

- [ ] Dockerfile multi-stage do frontend (build com Vite, serve com nginx).
- [ ] Dockerfile do backend (Gunicorn + entrypoint.sh com migrate).
- [ ] `nginx.conf` final: TLS, HSTS, CSP, X-Frame-Options, rate limit zones para login e identify, gzip, redirect HTTP→HTTPS.
- [ ] `docker-compose.prod.yml` separado.
- [ ] `infra/README.md`: roteiro de deploy, certbot, backup `pg_dump`, variáveis de ambiente, restore.
- [ ] Comando `seed_dev` (criar 1 org + 1 organizador + 1 eleição com candidatos + 50 votantes fictícios).
- [ ] Página 404 amigável.
- [ ] Logo / branding minimalista da plataforma.
- [ ] Smoke E2E via Playwright cobrindo fluxo completo (incluindo um run com viewport mobile 375x812).
- [ ] Lighthouse a11y > 95 em todas as páginas da cabine do eleitor.
- [ ] Lighthouse mobile (Performance + Best Practices) > 90 na cabine do eleitor com throttling 4G.
- [ ] Cross-browser manual: Safari iOS, Chrome Android, Firefox Android, Chrome desktop, Firefox desktop, Safari desktop.
- [ ] `docs/usuario/manual-organizador.md` (entra nesta fase).

---

## Itens futuros (não fazer agora)

- Lista de presença por CPF → RFu-001
- 2FA TOTP → RFu-002
- Convites de organizadores via email → RFu-003
- Faturamento / planos → RFu-004
- Personalização visual por organização → RFu-005
- PDF server-side de relatório → RFu-006
- Trilha de auditoria visível na UI → RFu-007
- Recuperação de senha por email (fluxo self-service) → backlog técnico
- Internacionalização (pt-PT, en) → backlog
- App mobile do eleitor com QR code de identidade → backlog
