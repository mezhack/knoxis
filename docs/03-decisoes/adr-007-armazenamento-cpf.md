# ADR-007 — Armazenamento de CPF

**Status:** accepted
**Data:** 2026-05-26

## Contexto

CPF é dado pessoal sensível regulado pela LGPD. Funções no Knoxis:

1. **Matching** durante validação do eleitor: comparar CPF digitado com a lista importada.
2. **Exibição mascarada** no painel do organizador (listas de votantes, relatórios).
3. **Auditoria parcial** (entender quantos votaram, sem identificar).

Não há função que exija o CPF em claro depois da importação.

## Decisão

**Armazenar apenas hash HMAC-SHA256 determinístico do CPF e os dois últimos dígitos para exibição mascarada. Nunca armazenar o CPF em claro.**

### Implementação

- Coluna `voters.cpf_hash` (CHAR(64) — hex SHA-256): `HMAC-SHA256(secret_key=CPF_HMAC_KEY, message=cpf_normalizado)`.
- Coluna `voters.cpf_last2` (CHAR(2)): últimos 2 dígitos do CPF (antes ou depois do verificador — decidir na implementação; documentar a escolha).
- Chave `CPF_HMAC_KEY` em variável de ambiente. Rotacionar exige re-importar listas — aceitável.
- Validação na entrada (formato + dígitos verificadores) **antes** de hashear.

### Como funciona o matching

1. Eleitor digita CPF.
2. Backend normaliza (remove pontuação), valida formato + verificadores.
3. Backend computa `hash = hmac_sha256(CPF_HMAC_KEY, cpf_normalizado)`.
4. `SELECT * FROM voters WHERE election_id = ? AND cpf_hash = ?` — bate ou não.

Como é determinístico, o lookup é O(log n) com índice — tão rápido quanto comparar texto claro.

### Como funciona a exibição

Em listas administrativas:
- "João da Silva — ***.***.***-89" (apenas últimos 2 visíveis).
- Logs: nunca incluem `cpf` nem `cpf_hash`. Helper `mascarar_cpf(input)` para uso obrigatório se for logar algo relacionado.

### Importação de CSV

- Cliente envia CPF em claro (única forma possível inicial).
- Servidor recebe via TLS, processa em memória, hasheia, descarta o claro.
- Arquivo CSV original **não é armazenado** — apenas o resultado (`voters` populada).
- Relatório de import mostra nomes + cpf_last2; nunca os CPFs completos.

## Trade-offs e limitações

### Hash determinístico permite ataque dicionário
- Atacante com acesso ao banco pode tentar todos os 10^11 CPFs e bater contra `cpf_hash`. Mas: precisa da `CPF_HMAC_KEY` para reproduzir o hash. Sem a chave, o ataque de dicionário não funciona.
- Trade-off: HMAC com chave secreta torna o hash não-precomputável por adversário sem acesso ao servidor. Se o servidor cair, o atacante tem tanto o banco quanto a chave — mas neste cenário o jogo acabou de qualquer forma.

### Rotação de chave
- Trocar `CPF_HMAC_KEY` invalida o matching das listas existentes.
- Procedimento: re-importar a lista da eleição com a nova chave, ou manter uma "chave de eleição" por organização (futuro).
- Não é problema operacional sério porque eleições são eventos isolados.

### Não suporta busca por CPF parcial
- Hash determinístico impede `LIKE '...%'`. Aceitável: organizador usa busca por nome.

## Consequências

### Positivas
- Banco/backup sem CPFs em claro reduz drasticamente o impacto de vazamento.
- Conformidade LGPD melhor (minimização de dados).
- Implementação simples e performática.

### Negativas
- Perda do CPF original irreversível. Organizador precisa manter o CSV original em seu controle se quiser referência. **Documentar isso explicitamente no fluxo de import.**
- Mudança de organizadora/igreja não consegue recuperar CPFs — precisaria re-importar.

## Alternativas consideradas

### Armazenar CPF em claro com acesso restrito
- Mais flexível.
- Rejeitado: aumenta o blast radius de qualquer vazamento. LGPD exige minimização.

### Cifragem reversível (Fernet/AES)
- Mantém capacidade de recuperar.
- Rejeitado: nenhuma função do sistema exige recuperar o CPF. Cifragem reversível seria peso sem ganho.

### Bcrypt do CPF
- Não-determinístico → impossível fazer matching direto.
- Rejeitado: matching exigiria comparar com todos os hashes da lista — inviável.

### Hash sem chave (SHA-256 puro)
- Rejeitado: vulnerável a dicionário sem precisar comprometer o servidor.
