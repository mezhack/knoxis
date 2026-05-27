# Histórias de usuário

Histórias agrupadas por persona e por fase. Cada história tem critérios de aceitação que viram testes durante a implementação.

## Persona 1 — Organizador (admin de organização)

### HU-O-01 — Cadastro inicial
**Como** secretário do Conselho da minha igreja,
**quero** criar uma conta na plataforma e cadastrar minha igreja,
**para que** eu possa começar a configurar eleições.

**Critérios:**
- Posso criar conta com email + senha forte (mínimo 12 caracteres, conforme política configurada).
- Após cadastro, sou levado a criar uma organização (nome da igreja, cidade/estado opcional).
- Eu sou owner automaticamente da organização que criei.

### HU-O-02 — Login
**Como** organizador cadastrado,
**quero** logar com email e senha,
**para que** eu acesse o painel da minha igreja.

**Critérios:**
- Login retorna ao painel da última organização acessada (ou única, se só houver uma).
- Sessão expira após 8h de inatividade.
- 5 tentativas falhadas em 15min bloqueiam o IP por 30min.

### HU-O-03 — Criar eleição
**Como** organizador,
**quero** criar uma nova eleição,
**para que** eu defina cargos, vagas, candidatos e votantes.

**Critérios:**
- Crio com nome (ex.: "Eleição de oficiais 2026") e data prevista.
- Eleição nasce em estado `rascunho`.
- Posso ter múltiplas eleições simultaneamente (uma em rascunho, outra encerrada, etc.).

### HU-O-04 — Configurar cargos e vagas
**Como** organizador,
**quero** adicionar cargos e definir vagas,
**para que** a cédula reflita o edital aprovado pelo Conselho.

**Critérios:**
- Adiciono cargo informando nome livre e número de vagas (inteiro ≥ 1).
- Cargos predefinidos sugeridos no UI: "Presbítero", "Diácono".
- Posso editar nome/vagas enquanto eleição está em `rascunho` ou `pronta`.

### HU-O-05 — Cadastrar candidatos
**Como** organizador,
**quero** cadastrar os candidatos por cargo,
**para que** apareçam na cédula.

**Critérios:**
- Adiciono candidato informando nome completo e vinculando a um cargo.
- Posso ter mais candidatos do que vagas (cenário normal).
- Não posso iniciar eleição com `candidatos < vagas` em algum cargo.
- Posso editar/remover candidatos enquanto a eleição está em `rascunho` ou `pronta`.

### HU-O-06 — Importar lista de votantes
**Como** organizador,
**quero** importar a lista de membros aptos a votar via CSV,
**para que** o sistema valide CPF na hora do voto.

**Critérios:**
- Faço upload de CSV com colunas `cpf` e `nome` (cabeçalho).
- Sistema valida CPFs e mostra relatório: importados, rejeitados (com motivo) — duplicados, inválidos, formato errado.
- Importação é additiva: posso fazer múltiplos uploads acumulando. CPF duplicado entre uploads é ignorado (não duplica).

### HU-O-07 — Configurar regra do escrutínio final
**Como** organizador,
**quero** definir como será o último escrutínio,
**para que** o sistema saiba quando aplicar "mais votados sem necessidade de maioria".

**Critérios:**
- Escolho entre: (a) "Marcar último manualmente" — em algum escrutínio futuro, ligo a flag; ou (b) "Limitar a N escrutínios" — sistema marca o último automaticamente.
- Posso alterar essa configuração enquanto eleição está em `rascunho` ou `pronta`. Em `em_andamento`, posso aumentar o limite (relaxar) mas não diminuir.

### HU-O-08 — Iniciar eleição (abrir 1º escrutínio)
**Como** organizador,
**quero** iniciar a eleição,
**para que** os eleitores possam começar a votar.

**Critérios:**
- Pré-requisitos validados (RF-015). Falhas mostram lista de pendências.
- Após iniciar, vejo URL pública da eleição e QR code para projetar na assembleia.
- 1º escrutínio é criado automaticamente em estado `aberto`.

### HU-O-09 — Acompanhar parciais (privado)
**Como** organizador,
**quero** ver a contagem parcial enquanto o escrutínio está aberto,
**para que** eu possa decidir, conforme rito, quando divulgar.

**Critérios:**
- Existe link "Ver parciais (nova aba)" no painel do escrutínio.
- A aba só é acessível autenticado. Compartilhar URL sem login não dá acesso.
- Atualiza a cada ≤3 segundos.
- A interface deixa explícito "parciais — não divulgar até decisão do organizador".

### HU-O-10 — Encerrar escrutínio e ver resultado
**Como** organizador,
**quero** encerrar o escrutínio e ver quem foi eleito,
**para que** eu possa anunciar o resultado na assembleia.

**Critérios:**
- Botão "Encerrar escrutínio" com confirmação dupla.
- Após encerrar: vejo, por cargo, contagem total e destaque visual nos eleitos.
- Vejo "candidatos remanescentes" (não eleitos) que seguirão para o próximo escrutínio.
- Se houver empate na linha de corte, vejo aviso claro com botão para resolver.

### HU-O-11 — Iniciar próximo escrutínio
**Como** organizador,
**quero** iniciar a próxima rodada com os remanescentes,
**para que** as vagas restantes sejam preenchidas.

**Critérios:**
- O sistema pré-carrega candidatos e vagas restantes; não preciso reconfigurar.
- Se o escrutínio anterior tinha empate não resolvido, não posso iniciar o próximo até resolver.
- Se atingi `max_escrutinios`, sistema marca este como `is_final` automaticamente e me avisa.

### HU-O-12 — Marcar escrutínio como final manualmente
**Como** organizador (modo manual),
**quero** marcar um escrutínio como final antes de abri-lo,
**para que** o critério "mais votados" entre em vigor.

**Critérios:**
- Toggle `is_final` disponível na tela de criação/preparação do escrutínio.
- Após abrir, não posso desmarcar.

### HU-O-13 — Imprimir relatório por escrutínio
**Como** organizador,
**quero** imprimir o relatório de cada escrutínio,
**para que** seja anexado à ata.

**Critérios:**
- Aba "Relatórios" da eleição lista todos os escrutínios encerrados.
- Cada item abre página com: cabeçalho da eleição, número do escrutínio, contagem por candidato (por cargo), total de votantes, abstenção (se aplicável), eleitos do escrutínio.
- Botão "Imprimir" usa CSS de impressão limpo.

### HU-O-14 — Resolver empate manualmente
**Como** organizador,
**quero** registrar a resolução do empate (ex.: por sorteio),
**para que** o sistema saiba quem foi eleito.

**Critérios:**
- Tela específica do empate mostra os candidatos empatados e o número de vagas em disputa.
- Posso escolher: eleger candidato X (e não Y), ou levar ambos a um novo escrutínio adicional (mesmo que estivéssemos no "final"), ou ampliar vagas (registrar nota).
- Cada resolução fica registrada com nota textual obrigatória (quem decidiu, como — "sorteio realizado em assembleia, ata fls. X").

## Persona 2 — Eleitor

### HU-E-01 — Acessar página de votação
**Como** membro da igreja,
**quero** acessar a página de votação pela URL ou QR projetado,
**para que** eu vote no celular ou em estação preparada.

**Critérios:**
- URL pública não exige login.
- Mostra nome da eleição, número do escrutínio atual, instruções claras.
- Se nenhum escrutínio está aberto, mostra mensagem "votação não disponível no momento".

### HU-E-02 — Identificar-se por CPF
**Como** eleitor,
**quero** entrar com meu CPF,
**para que** o sistema confirme que sou membro e libere a cédula.

**Critérios:**
- Campo de CPF aceita com ou sem pontuação.
- Validação local de formato e dígitos verificadores antes de enviar.
- Se CPF não está no rol: mensagem "CPF não localizado na lista de membros desta eleição".
- Se CPF já votou neste escrutínio: mensagem "voto já registrado neste escrutínio".
- Após validação, cédula abre na mesma tela; não há tela intermediária de boas-vindas.

### HU-E-03 — Votar na cédula única
**Como** eleitor,
**quero** marcar minha cédula com presbíteros e diáconos da minha preferência,
**para que** meu voto seja registrado.

**Critérios:**
- Cédula mostra todos os cargos com vagas remanescentes.
- Cada cargo indica claramente "marque exatamente K candidatos".
- Excesso ou falta de marcações é sinalizado em tempo real; botão "Confirmar voto" só fica ativo quando todos os cargos estão corretos.
- Confirmação dupla: tela de revisão antes da submissão final.
- Após submissão, vejo "Voto registrado com sucesso." sem retornar conteúdo do voto.
- **No celular**: cada cargo é uma seção rolável independente, com contador "X de Y" fixo no topo da seção. Botão "Confirmar voto" fica sticky no rodapé. Áreas de toque ≥ 44x44px. Sem zoom involuntário no foco do input. Ver detalhes em [docs/02-arquitetura/frontend.md#responsividade](../02-arquitetura/frontend.md#responsividade).
- **No tablet/desktop**: mesmo fluxo, conteúdo centralizado em coluna legível (~ 720px de largura).

### HU-E-04 — Não conseguir votar novamente
**Como** eleitor que já votei,
**quero** ser informado claramente se tentar votar de novo no mesmo escrutínio,
**para que** eu entenda que não houve falha.

**Critérios:**
- Mensagem específica: "Você já votou neste escrutínio. Aguarde a próxima rodada, se houver."
- Não revela conteúdo do voto anterior.

### HU-E-05 — Votar em escrutínio seguinte
**Como** eleitor que votei no escrutínio 1,
**quero** poder votar normalmente no escrutínio 2,
**para que** eu participe de todas as rodadas.

**Critérios:**
- "Votou neste escrutínio" é por escrutínio, não por eleição.
- O fluxo de identificação por CPF é idêntico em qualquer escrutínio.
