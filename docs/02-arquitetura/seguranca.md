# Segurança

## Modelo de ameaças

### Atacantes considerados

1. **Voto duplo:** eleitor tenta votar duas vezes no mesmo escrutínio.
2. **Voto não-autorizado:** alguém sem CPF na lista tenta votar.
3. **Quebra de sigilo do voto:** investigador (interno ou externo) tenta correlacionar CPF com conteúdo do voto.
4. **Manipulação de contagem:** atacante tenta inflar votos de candidato preferido.
5. **Vazamento cross-tenant:** organizador da igreja A enxerga eleição da igreja B.
6. **Sequestro de sessão de organizador:** atacante captura cookie e age como organizador.
7. **Força bruta de senha:** atacante tenta logar repetidamente.
8. **Força bruta de CPF:** atacante tenta diversos CPFs para identificar membros.
9. **Vazamento de CPF em logs / DB dump.**

### Fora do escopo (mas anotado)

- Adversários com acesso ao servidor (root, dump do banco). Mitigação parcial via hash de CPF e Argon2 em senhas, mas root acesso compromete tudo. Boa prática de infra (firewall, SSH-key only, fail2ban) é responsabilidade da operação.
- Adversários físicos durante a assembleia (alguém olhando a tela do eleitor). Mitigação organizacional (cabine), não técnica.

## Controles

### Autenticação de organizador
- **Senha:** Argon2id (parâmetros padrão do Django). Política mínima: 12 caracteres, sem senhas comuns (lista do Django + lista própria opcional).
- **Sessão:** cookie httpOnly + Secure + SameSite=Lax. Expiração 8h de inatividade.
- **CSRF:** token obrigatório para todas as mutações (`X-CSRFToken` header).
- **Brute force:** `django-axes` bloqueia IP após 5 falhas em 15min por 30min. Logs alertam padrão suspeito.

### Voto secreto (invariante de schema)
- Tabela `votes` não tem coluna identificando eleitor. Verificado por teste de introspecção.
- Tabela `voter_attendance` registra que o eleitor votou, mas não o conteúdo do voto.
- Timestamps em `votes` truncados ao **minuto** para reduzir correlação temporal entre `voter_attendance.voted_at` e `votes.created_at`. Em escrutínios pequenos isso ainda permite correlação por proximidade temporal; ver "Limitações conhecidas" abaixo.
- Logs do servidor não correlacionam request_id de validação CPF com request_id de submissão. O cookie de `ballot_session` carrega um token opaco que não revela o voter.

### Anti-replay de cédula
- Tabela `ballot_sessions` com `used_at` e `expires_at`. Submissão usa `SELECT FOR UPDATE` para impedir duas submissões concorrentes da mesma sessão.

### Anti força-bruta de CPF
- Rate limit por IP (10 tentativas / 5min) na rota de identificação do eleitor.
- Respostas constantes em tempo (não vazar via timing se CPF está no rol). Validamos sempre o algoritmo do CPF antes de consultar o BD.
- Sem mensagem distinguindo "CPF não cadastrado" de "CPF inválido"? **Sim, distinguimos**, porque a UX é prioridade na assembleia — atacante já assume que a lista é finita de membros da igreja. O risco residual é considerado aceitável.

### Multi-tenant
- Mixin obrigatório `TenantScopedViewSet` filtra todas as queries por `organization_id` do usuário logado.
- Testes de cobertura específica: criar 2 orgs, tentar acessar recursos da outra → expect 404.
- Auditoria periódica de novos viewsets para confirmar uso do mixin.

### Armazenamento de CPF
- Coluna `cpf_hash` = HMAC-SHA256(CPF_normalizado, chave em env). Determinístico para matching.
- Coluna `cpf_last4` (string 2 dígitos do CPF, antes do verificador) para exibição mascarada.
- Nome do votante armazenado em claro (necessário para listas administrativas).
- Sem coluna `cpf` em claro em lugar nenhum.
- Ver [ADR-007](../03-decisoes/adr-007-armazenamento-cpf.md).

### Headers HTTP (Nginx)
- `Strict-Transport-Security: max-age=31536000; includeSubDomains`
- `X-Content-Type-Options: nosniff`
- `X-Frame-Options: DENY`
- `Referrer-Policy: same-origin`
- `Content-Security-Policy: default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self' data:;`
  - Inline style permitido por causa do Tailwind/print CSS; pode ser tightened com nonce em fase futura.

### TLS
- Apenas TLS 1.2+ habilitado no Nginx.
- HSTS preload opcional após validação inicial.

### Logs
- Estruturados em JSON. Cada request com `request_id`, `user_id` (se autenticado), `org_id`, `route`, `status`.
- **Nunca** logar: CPF cru, conteúdo de votos, tokens de sessão (apenas hash dos primeiros 8 caracteres se necessário para correlação).
- Helper `mascarar_cpf()` obrigatório; verificação por revisão e regra de lint que sinaliza uso de `cpf` em chamadas de logger (lint custom — backlog).

### Auditoria
- Tabela `audit_log` com: id, organization_id, user_id, action, target_type, target_id, payload (jsonb redacted), created_at.
- Ações registradas: criar/editar eleição, abrir/encerrar escrutínio, encerrar eleição, resolver empate, importar lista de votantes (com contagem, sem CPFs).
- Não há rota pública para auditoria nesta fase; consulta direta no BD ou Django admin.

## Limitações conhecidas (registradas, aceitas)

1. **Correlação temporal CPF↔voto em escrutínio pequeno.** Se 5 pessoas votam em 1h, observador com acesso a logs pode correlacionar `voter_attendance.voted_at` (próximo do `voted_at` cru) com `votes.created_at` (minuto). Mitigamos truncando ao minuto e separando tabelas, mas em assembleias muito pequenas o sigilo é estatístico, não absoluto. Aviso documentado nas notas do organizador.

2. **Acesso a root do servidor compromete tudo.** Aplicação não cifra dados em repouso além de hash de CPF e senha. Backup do banco contém dados pessoais (nome + cpf_hash). Mitigação organizacional (acesso restrito, criptografia de disco no provedor).

3. **Atacante com acesso ao código pode adulterar a apuração antes do encerramento.** Mitigação por code review, deploy auditável, logs de auditoria, e processo de ata cruzando totais.

4. **Sem 2FA na fase 1.** Senha + sessão é o único fator. 2FA TOTP em RFu-002.

5. **CSP permite 'unsafe-inline' em styles.** Aceitável na fase 1 por causa de Tailwind generation e print CSS; tightening em fase futura.

## Checklist de revisão de cada PR

- [ ] Não adicionei coluna que liga eleitor ao voto?
- [ ] Filtrei por `organization_id` em toda query nova de organizador?
- [ ] CPF mascarado em qualquer log/erro novo?
- [ ] Endpoint público novo tem rate limit?
- [ ] Migration é idempotente?
- [ ] Mudança em contrato público veio com atualização da doc?
