# Fases de desenvolvimento

Cada fase termina com um sistema funcional ponta-a-ponta dentro de seu escopo, com critérios de aceitação verificáveis. Nenhuma fase começa antes da anterior ser validada. **Zero regressão entre fases**.

## Princípios das fases

- **Vertical slicing:** cada fase entrega valor visível (UI + backend + BD), não camadas isoladas.
- **Testes de aceitação obrigatórios:** cada fase define seus testes antes da implementação.
- **Doc atualizada no mesmo PR:** se o contrato/regra mudar, doc muda junto.
- **Migrations idempotentes** em todas as fases (ver [ADR-004](../03-decisoes/adr-004-migrations-idempotentes.md)).

---

## Fase 0 — Fundação

**Objetivo:** infra e setup mínimo para todas as fases seguintes.

**Entregas:**
- Estrutura de pastas `backend/` e `frontend/` conforme [arquitetura](../02-arquitetura/).
- Backend: projeto Django + DRF inicializado, `settings/{base,dev,prod}.py`, `pyproject.toml` com deps fixadas.
- Frontend: projeto Vite + React + TS, Tailwind configurado, React Router montado, TanStack Query instalado.
- Banco: container Postgres no `docker-compose.yml`. Migration inicial do Django (auth, sessions).
- Endpoint `/api/v1/healthz` retornando 200.
- Frontend renderiza tela vazia "Knoxis — em construção" e chama healthz.
- Configuração de Argon2 como hasher principal.
- Lint/format (Ruff + Black, ESLint + Prettier) rodando.
- Script `make dev` ou equivalente sobe tudo localmente.

**Critérios de aceitação:**
- [ ] `docker compose up` sobe os 3 containers sem erro.
- [ ] `curl localhost/api/v1/healthz` retorna 200.
- [ ] Frontend em `localhost:5173` (dev) bate no backend e mostra "ok".
- [ ] `python manage.py migrate` roda 2x sem erro nem mudança de estado.
- [ ] CI roda lint + testes (sem testes ainda; placeholder).

---

## Fase 1 — Contas e organizações

**Objetivo:** organizador cria conta, loga, cria/edita sua organização.

**Entregas:**
- Modelo `User` customizado + `Organization` + `OrganizationMember`.
- Endpoints: signup, login, logout, /me, /csrf.
- Mixin `TenantScopedViewSet` e `current_organization` resolver baseado na sessão.
- `django-axes` configurado para login.
- Frontend: páginas de signup, login, painel raiz com "minhas organizações".
- Testes de cross-tenant baseline (criar 2 orgs e validar isolamento — ainda que com pouca coisa pra isolar).

**Critérios de aceitação:**
- [ ] HU-O-01 e HU-O-02 atendidas.
- [ ] 5 falhas de login a partir do mesmo IP+username → bloqueio 30min.
- [ ] Argon2id hash em senha (verificável via shell).
- [ ] Cookie de sessão httpOnly + Secure (em dev: Secure desligado).
- [ ] CSRF token funcionando em mutações.
- [ ] Teste: User A não consegue ver Organization B.

---

## Fase 2 — Configuração de eleição

**Objetivo:** organizador cria eleição completa (cargos, candidatos, votantes, regras) até deixá-la `pronta`.

**Entregas:**
- Modelos `Election`, `Position`, `Candidate`, `Voter`.
- Endpoints CRUD admin para tudo acima.
- Importador de CSV de votantes com:
  - Validação de CPF (formato, verificadores).
  - Hash HMAC-SHA256 conforme [ADR-007](../03-decisoes/adr-007-armazenamento-cpf.md).
  - Relatório de import (importados / duplicados / inválidos).
- Validador de pré-requisitos pra `start`.
- Frontend: telas de criar eleição, editar cargos/vagas, adicionar candidatos, upload de CSV.
- Auditoria: `audit_log` para criar/editar eleição, importar lista.

**Critérios de aceitação:**
- [ ] HU-O-03 a HU-O-07 atendidas.
- [ ] CPF nunca aparece em log nem em response.
- [ ] Import com CSV malformado (sem colunas) retorna erro claro.
- [ ] Import com 1 CPF duplicado em duas linhas: importa 1, reporta 1 duplicado.
- [ ] Tentar `start` com `candidates < vacancies` retorna 422 com lista de pendências.
- [ ] Eleição em `em_andamento` recusa edição de vagas (apenas `description` etc).

---

## Fase 3 — Votação básica (1 escrutínio)

**Objetivo:** eleitor consegue votar usando CPF e ver a confirmação. Escrutínio pode ser aberto, mas não há apuração nem múltiplas rodadas ainda.

**Entregas:**
- Modelos `Escrutinio`, `EscrutinioPosition`, `EscrutinioCandidate`, `BallotSession`, `VoterAttendance`, `Vote`.
- Endpoints públicos: `GET /public/elections/{slug}`, `POST /public/elections/{slug}/identify`, `POST /public/ballot/submit`.
- Endpoint admin: `POST /escrutinios/{id}/open`.
- Cookie `ballot_session` httpOnly/Secure/SameSite, expiração 10min.
- Frontend cabine do eleitor: entrada de CPF, cédula, confirmação.
- Frontend admin: tela de "iniciar escrutínio".
- Teste de introspecção do schema validando que `votes` não tem `voter_id`.
- Rate limit `identify` e `auth/login`.

**Critérios de aceitação:**
- [ ] HU-E-01 a HU-E-04 atendidas para 1 escrutínio.
- [ ] CPF não cadastrado → 404 com mensagem clara.
- [ ] CPF que já votou → 409 com mensagem clara.
- [ ] Submeter cédula com nº errado de marcações → 400.
- [ ] Submeter mesma cédula duas vezes em paralelo → uma vence, outra falha (concurrency test).
- [ ] `votes` no banco não tem coluna identificando eleitor (verificado por introspecção).
- [ ] Truncamento de `votes.created_at` ao minuto verificável.
- [ ] CSP, HSTS, cookies seguros em produção.
- [ ] **Cabine do eleitor renderiza corretamente em 320px, 375px, 412px, 768px e 1440px** (screenshots anexados ao PR de fechamento da fase).
- [ ] **Áreas tocáveis ≥ 44x44px** em todos os controles da cabine (verificação manual).
- [ ] **Sem zoom indesejado** ao focar inputs no iOS (verificado em Safari iOS real ou emulador).
- [ ] **Contador de marcações fica visível** durante toda a rolagem da cédula em mobile.
- [ ] **Botão "Confirmar voto" sticky** no rodapé em mobile, acima do conteúdo, com sombra superior.

---

## Fase 4 — Múltiplos escrutínios e apuração

**Objetivo:** ciclo completo: abrir, votar, encerrar, apurar, abrir próximo, repetir até preencher vagas.

**Entregas:**
- Função pura `apurador.apurar(escrutinio) -> ResultadoApuracao` em `apps/voting/apurador.py`.
- Endpoint `POST /escrutinios/{id}/close` com transação atômica e gravação de `election_results`.
- Detecção de empate na linha de corte.
- Endpoint para criar escrutínio seguinte herdando remanescentes.
- Configuração e respeito a `final_rule` (manual / max_count).
- Lógica do escrutínio final (mais votados sem limiar).
- Endpoint de resolução de empate.
- Transição automática de `election.status` para `encerrada` quando todas vagas preenchidas.
- Frontend admin: telas de encerrar escrutínio, ver resultados destacando eleitos, marcar próximo, resolver empate.

**Critérios de aceitação:**
- [ ] HU-O-08, HU-O-10, HU-O-11, HU-O-12, HU-O-14 atendidas.
- [ ] HU-E-05 atendida (eleitor vota em escrutínios sucessivos).
- [ ] Testes unitários do `apurador.apurar` cobrem cenários da [regras-de-negocio.md](../01-especificacoes/regras-de-negocio.md): exato limiar, mais qualificados que vagas, empate no corte, escrutínio final, empate no final.
- [ ] Tentar abrir 2º escrutínio com empate pendente → 409.
- [ ] Tentar abrir 2 escrutínios simultâneos na mesma eleição → 409.
- [ ] `final_rule=max_count` com `max_escrutinios=3` marca o 3º como `is_final` automaticamente.

---

## Fase 5 — Parciais e relatórios

**Objetivo:** organizador acompanha contagem em tempo real (privado), e gera relatório impressível.

**Entregas:**
- Endpoint `GET /escrutinios/{id}/parciais` com ETag.
- Frontend admin: página `/escrutinios/{id}/parciais` (link em "abrir em nova aba"), com polling 3s.
- Rota protegida por auth — sem cookie de sessão, 401.
- Endpoint `GET /escrutinios/{id}/relatorio`.
- Página de relatório impressível com `@media print` CSS.
- Cálculo de abstenção conforme RN-4.
- Audit logs para `escrutinio.open` e `escrutinio.close`.

**Critérios de aceitação:**
- [ ] HU-O-09, HU-O-13 atendidas.
- [ ] Parciais não vazam em nenhuma rota pública.
- [ ] ETag retorna 304 quando não houve novos votos.
- [ ] Página de relatório imprime corretamente em A4 (validar manualmente em navegador).
- [ ] Abstenção aparece a partir do 2º escrutínio com cálculo correto.

---

## Fase 6 — Polimento e hardening

**Objetivo:** sistema pronto para produção em VPS pública.

**Entregas:**
- Dockerfile multi-stage para frontend (build + nginx).
- Dockerfile do backend com gunicorn e entrypoint que roda migrate.
- `nginx.conf` com TLS, headers de segurança, rate limit zones.
- Documentação `infra/README.md` para deploy: env vars, certbot, backup.
- Script de seed para desenvolvimento.
- Página de erro 404 amigável (eleição inexistente etc).
- Acessibilidade revisada (Lighthouse a11y > 95 no fluxo do eleitor).
- Smoke test ponta-a-ponta automatizado (Playwright contra docker compose).
- Manual do organizador (`docs/usuario/manual-organizador.md` — entrar nesta fase).

**Critérios de aceitação:**
- [ ] Deploy em VPS staging funcional, cobrindo um ciclo completo de eleição com dados de teste.
- [ ] Lighthouse a11y > 95 na cabine do eleitor.
- [ ] Smoke test passa local e em CI.
- [ ] Headers de segurança verificados via `curl -I`.
- [ ] **Lighthouse mobile (Performance + Best Practices) > 90 na cabine do eleitor** em 4G simulado.
- [ ] **Validação cruzada de navegador**: cabine testada em Safari iOS, Chrome Android, Firefox Android, Chrome desktop, Firefox desktop. Bugs encontrados documentados ou corrigidos.

---

## Sobre não-regressão

A cada fase, antes do PR final ser aprovado:

1. Rodar todos os testes das fases anteriores. Tudo passa.
2. Smoke test manual: fluxo da fase anterior continua funcionando.
3. Schema do banco: alterações são additivas. Renomear/dropar exige justificativa explícita no ADR.
4. Contratos da API: campos podem ser adicionados; remover/renomear exige nova versão (`v2`) ou deprecation period.
