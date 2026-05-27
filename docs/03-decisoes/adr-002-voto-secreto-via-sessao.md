# ADR-002 — Voto secreto via sessão de cédula efêmera e invariante de schema

**Status:** accepted
**Data:** 2026-05-26

## Contexto

O voto precisa ser secreto: o sistema não pode permitir, em nenhuma circunstância, recuperar qual candidato um determinado eleitor (CPF) escolheu. Ao mesmo tempo:

- Precisamos validar que o votante é membro (CPF na lista).
- Precisamos impedir voto duplo no mesmo escrutínio.
- Precisamos saber quantos eleitores votaram (para cálculo de maioria simples e de abstenção).

A naïveté de armazenar `(voter_id, candidate_id)` quebra o sigilo. Soluções criptográficas pesadas (ZK proofs, mix nets) são overkill para o escopo.

## Decisão

**Separar identidade e voto em duas tabelas, sem chave estrangeira entre elas:**

1. `voter_attendance(escrutinio_id, voter_id, voted_at)` — registra que o eleitor votou. Tem `voter_id`. Não tem nada do voto.
2. `votes(escrutinio_id, position_id, candidate_id, created_at)` — registra o voto. **Não tem `voter_id`. Não tem `cpf`. Não tem `ballot_session_id`.**

**Ligar as duas com uma sessão efêmera, que é destruída no instante da submissão:**

1. Eleitor valida CPF → backend cria `ballot_session(escrutinio_id, voter_id, token, expires_at, used_at=NULL)`.
2. Backend devolve `token` em cookie httpOnly.
3. Eleitor submete a cédula com o cookie.
4. Backend, em uma única transação:
   - `SELECT FOR UPDATE` na `ballot_session` por token.
   - Verifica `used_at IS NULL`, `expires_at > NOW()`, escrutínio aberto.
   - `UPDATE ballot_sessions SET used_at = NOW() WHERE id = ?`
   - `INSERT INTO voter_attendance (escrutinio_id, voter_id, voted_at)`
   - `INSERT INTO votes (escrutinio_id, position_id, candidate_id)` — N linhas, **sem voter_id**.
   - `COMMIT`.
5. A linha de `ballot_sessions` permanece (com `used_at` preenchido) para fins de auditoria — mas **não** tem o conteúdo do voto e não há FK do voto pra ela.

## Invariante reforçada

A tabela `votes` **nunca** terá colunas que identifiquem o eleitor. Isso é codificado em:

- Modelo Django: `Vote` não declara `voter` nem `ballot_session`.
- Teste de introspecção do schema: percorre `information_schema.columns` da tabela `votes` e falha se aparecer qualquer coluna fora do conjunto permitido.
- Checklist de PR (ver [seguranca.md](../02-arquitetura/seguranca.md)).

## Timestamp de voto

`votes.created_at` é gravado com **truncamento ao minuto** (`DATE_TRUNC('minute', NOW())`). Isso reduz a correlação temporal com `voter_attendance.voted_at`, que mantemos com timestamp completo para auditoria de comparecimento. Em assembleias com fluxo de votação concentrado, o truncamento + a ausência de FK torna a correlação prática difícil mas não impossível em escrutínios muito pequenos (limitação documentada em [seguranca.md](../02-arquitetura/seguranca.md)).

## Consequências

### Positivas
- Sigilo verificável por schema: olhando as tabelas, fica claro que ligar voto a eleitor é impossível sem outros sinais (logs, ordem temporal aproximada).
- Implementação simples, sem dependência criptográfica.
- Anti-duplo-voto preservado por constraint única em `voter_attendance(escrutinio_id, voter_id)`.
- Reabertura de votação em escrutínio seguinte é natural — basta novo `voter_attendance` para o novo `escrutinio_id`.

### Negativas
- Correlação temporal residual em escrutínios muito pequenos (poucos votantes, intervalo longo entre votos). Mitigamos com truncamento e instrução organizacional, não eliminamos completamente. Aceitável.
- Sessão efêmera precisa de cuidado em concorrência (SELECT FOR UPDATE).
- Atacante com acesso a logs pode tentar correlacionar request_id de identificação com request_id de submissão. Mitigação: middleware emite IDs aleatórios e independentes; CPF nunca aparece no segundo request.

## Alternativas consideradas

### Armazenar voto junto com voter_id, prometendo não consultar
Rejeitado: confiança baseada em política, não em estrutura. Quebrado por root, por bug, por subpoena.

### Voto cifrado com chave dupla (eleição encerrada → revela)
- Eleitor cifra com chave pública da eleição; backend descifra ao encerrar.
- Rejeitado: precisaria de tooling extra no cliente, complica UX, e atacante com root pega tudo igual.

### Misturar timestamp arbitrariamente
- Embaralhar `created_at` ao inserir.
- Rejeitado: complica auditoria sem ganho significativo em assembleias pequenas. Truncar ao minuto é simples e suficiente para o threat model.

### Mix net / shuffle de votos
- Conceitualmente ideal.
- Rejeitado: complexidade desproporcional ao escopo (igreja, ~centenas de votos).
