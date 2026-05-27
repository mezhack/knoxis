# Regras de negócio

As regras estão expressas com exemplos numéricos para evitar ambiguidade. Em caso de divergência entre este documento e o código, **este documento prevalece** e o código deve ser corrigido.

## RN-1 — Cálculo do limiar de maioria simples

**Definição:** dado `N` = número de votantes do escrutínio (eleitores que submeteram cédula naquele escrutínio), o limiar de elegibilidade é:

```
limiar = floor(N / 2) + 1
```

Equivalente a "metade mais um", arredondando a metade para baixo antes de somar 1.

**Exemplos:**

| Votantes (N) | floor(N/2) | Limiar |
|---|---|---|
| 30 | 15 | 16 |
| 31 | 15 | 16 |
| 50 | 25 | 26 |
| 51 | 25 | 26 |
| 100 | 50 | 51 |
| 101 | 50 | 51 |

> Nota: hoje N = número de votantes do escrutínio. Futuro (RFu-001): N = número de presentes confirmados na lista de presença. A mudança altera o denominador mas não a fórmula. Ver [funcionalidades-futuras.md](../07-futuro/funcionalidades-futuras.md).

## RN-2 — Apuração em escrutínio NÃO-final

Para cada cargo na eleição, ao encerrar o escrutínio:

1. Contar votos válidos por candidato: `contagem[candidato] = COUNT(votos onde candidato_id = candidato.id)`.
2. Calcular `limiar` conforme RN-1.
3. Filtrar candidatos com `contagem ≥ limiar`. Chamemos essa lista de `qualificados`.
4. Ordenar `qualificados` por contagem desc; em caso de empate, ordenar por nome (estabilidade — mas o efeito prático é nulo pois o item 5 considera todos do empate).
5. Eleger os `min(vagas_remanescentes, len(qualificados))` primeiros como **eleitos neste escrutínio**.
6. Caso ainda haja empate **na linha de corte** dentro da lista de qualificados (ex.: 5 candidatos atingiram limiar mas só há 4 vagas, e os 4º e 5º têm a mesma contagem), o sistema marca o cargo como `empate_no_corte` e exige resolução manual antes de iniciar o próximo escrutínio.
7. Candidatos qualificados não eleitos (ficaram fora do corte por menos votos) **e** candidatos não qualificados são todos elegíveis para o próximo escrutínio. Contagem zera.
8. Vagas remanescentes do cargo = `vagas_no_escrutinio - eleitos_no_escrutinio`.

**Exemplo:** cargo "Presbítero", 4 vagas, 60 votantes. Limiar = 31.

| Candidato | Votos | Status |
|---|---|---|
| A | 50 | Eleito (1ª vaga) |
| B | 45 | Eleito (2ª vaga) |
| C | 32 | Eleito (3ª vaga) |
| D | 31 | Eleito (4ª vaga) — atingiu limiar exato |
| E | 30 | Remanescente (não atingiu limiar) |
| F | 28 | Remanescente |
| G | 20 | Remanescente |

Próximo escrutínio (se houver): 0 vagas para presbítero, cargo encerrado.

**Exemplo com vagas restantes:** mesma situação, mas D = 28.

| Candidato | Votos | Status |
|---|---|---|
| A | 50 | Eleito |
| B | 45 | Eleito |
| C | 32 | Eleito |
| D | 28 | Remanescente |
| E | 30 | Remanescente |
| F | 28 | Remanescente |

3 eleitos, 1 vaga remanescente, candidatos D/E/F seguem para o próximo escrutínio (mais G se ainda estava). Próximo escrutínio: 1 vaga, 4 candidatos.

**Exemplo de empate na linha de corte:** cargo com 3 vagas, escrutínio NÃO-final, todos atingiram limiar.

| Candidato | Votos | Status |
|---|---|---|
| A | 40 | Eleito (1ª vaga) |
| B | 35 | Eleito (2ª vaga) |
| C | 30 | Empate no corte |
| D | 30 | Empate no corte |

Cargo fica em `empate_no_corte`. O organizador resolve manualmente (ex.: elege ambos por consenso e ajusta vagas no edital, ou desempata por sorteio, ou reabre nova rodada com C e D). A UI deve oferecer as ações: "Eleger C", "Eleger D", "Levar ambos ao próximo escrutínio".

## RN-3 — Apuração em escrutínio FINAL

Para cada cargo, ao encerrar o escrutínio final:

1. Contar votos por candidato (idêntico à RN-2).
2. Ordenar por votos desc.
3. Eleger os primeiros `vagas_remanescentes`, **independentemente do limiar de maioria simples**.
4. Se o último colocado dentro do corte e o primeiro colocado fora do corte tiverem o mesmo número de votos (empate na linha de corte), o cargo é marcado como `empate_no_corte` e exige resolução manual. A eleição **não** transita para `encerrada` até resolução.

**Exemplo:** cargo "Diácono", 2 vagas, escrutínio final.

| Candidato | Votos | Status |
|---|---|---|
| X | 20 | Eleito (1ª vaga) |
| Y | 12 | Eleito (2ª vaga) |
| Z | 5 | Não eleito |

Eleição segue para `encerrada` se todos os cargos preencheram as vagas (ou marcaram empate sem resolver).

**Empate no corte em escrutínio final:** 2 vagas.

| Candidato | Votos | Status |
|---|---|---|
| X | 20 | Eleito |
| Y | 12 | Empate no corte |
| Z | 12 | Empate no corte |

Cargo fica `empate_no_corte`. Organizador resolve manualmente.

## RN-4 — Cálculo de abstenção

**Definição:** abstenção do escrutínio `n` (para `n ≥ 2`) é a diferença entre votantes do escrutínio `n-1` e votantes do escrutínio `n`, considerando apenas valores positivos:

```
abstencao[n] = max(0, votantes[n-1] - votantes[n])
```

Se votantes[n] ≥ votantes[n-1], abstenção é zero (não é negativa).

**Exemplo:**

| Escrutínio | Votantes | Abstenção |
|---|---|---|
| 1 | 80 | — (não aplicável) |
| 2 | 75 | 5 |
| 3 | 70 | 5 |
| 4 | 72 | 0 (aumento — provavelmente alguém atrasado entrou) |

Abstenção aparece apenas no relatório a partir do 2º escrutínio.

## RN-5 — Composição da cédula

A cédula apresentada ao eleitor em um dado escrutínio contém **todos os cargos da eleição que ainda têm vagas remanescentes**, na seguinte estrutura:

- Para cada cargo com vagas remanescentes:
  - Título do cargo
  - Texto: "Marque exatamente `K` candidatos." onde `K = vagas_remanescentes`
  - Lista de candidatos elegíveis no escrutínio (checkboxes)
- Botão "Submeter cédula" só fica habilitado quando, em cada cargo, exatamente `K` checkboxes estiverem marcados.

Cargos sem vagas remanescentes não aparecem.

## RN-6 — Submissão de voto

1. Eleitor entra com CPF.
2. Sistema valida: CPF tem formato válido (11 dígitos com verificadores), CPF está no rol da eleição, eleitor ainda não votou neste escrutínio.
3. Se válido: cria sessão de cédula (token + expiração de 10min), apresenta cédula.
4. Eleitor seleciona candidatos respeitando RN-5 e submete.
5. Sistema, em **uma única transação**:
   a. Verifica que sessão ainda é válida (não expirou, não usada);
   b. Verifica que escrutínio ainda está aberto;
   c. Marca sessão como usada;
   d. Insere registro em `voter_attendance(escrutinio_id, voter_id, voted_at)`;
   e. Insere N registros em `votes(escrutinio_id, position_id, candidate_id)`, um por candidato marcado, **sem voter_id**;
   f. Confirma transação.
6. Se a transação falhar (ex.: escrutínio encerrou entre etapas 3 e 4), o voto é descartado, sessão invalidada, eleitor informado que precisa tentar de novo.

## RN-7 — Estados de eleição

```
rascunho ──(setup completo)──► pronta ──(iniciar)──► em_andamento ──(todas vagas preenchidas)──► encerrada
                                                          │
                                                          └─(eleição cancelada pelo organizador)──► cancelada
```

- **rascunho:** configuração em curso, sem candidatos suficientes ou sem votantes.
- **pronta:** todos os pré-requisitos atendidos (ver RF-015); pode iniciar.
- **em_andamento:** pelo menos um escrutínio já aberto. Não permite edição de cargos, vagas, candidatos ou lista de votantes.
- **encerrada:** sem vagas remanescentes ou último escrutínio final terminou.
- **cancelada:** organizador abortou; estado terminal alternativo. Cancelamento exige confirmação dupla.

## RN-8 — Estados de escrutínio

```
preparando ──(abrir)──► aberto ──(encerrar)──► encerrado
```

- **preparando:** criado mas não aberto; organizador ainda pode revisar configurações herdadas.
- **aberto:** aceita votos.
- **encerrado:** apuração calculada, eleitos definidos (ou empate sinalizado). Imutável.

Apenas um escrutínio por eleição pode estar em estado `aberto` por vez.

## RN-9 — Validações de CPF

- CPF deve ter 11 dígitos.
- Verificadores de CPF (algoritmo padrão) precisam ser válidos.
- CPFs notoriamente inválidos (todos os dígitos iguais — `11111111111`, etc.) são rejeitados.
- Pontuação e espaços são removidos antes da validação.

CPF inválido na importação de lista é registrado no relatório de erros e a linha é ignorada (não bloqueia o restante).

## RN-10 — Imutabilidade de escrutínio aberto

Quando um escrutínio é aberto, os seguintes são "tirados de uma foto" e ficam imutáveis até o encerramento:

- Lista de candidatos elegíveis (aqueles que não foram eleitos em escrutínios anteriores)
- Vagas remanescentes por cargo
- Lista de votantes habilitados

Editar a eleição (adicionar candidato, alterar vagas, importar mais votantes) só é permitido enquanto o escrutínio mais recente está `encerrado` ou enquanto a eleição está em `rascunho` / `pronta`. Mesmo assim, alterações tardias devem disparar aviso ao organizador sobre o impacto.
